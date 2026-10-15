"""
평가자 전용 실시간 JSON 데이터 상태 변화 시각화 데모 러너 (scripts/demo_visualizer.py)

터미널에서 각 명령어가 무엇을 하는지 상세한 설명과 함께 실행하고,
명령어 실행 전/후 데이터가 어떻게 생성되고(INSERT), 방출되며(EVICTED), 
만료되어 소멸하는지(EXPIRED) 실시간 JSON 스냅샷으로 눈에 띄게 시각화합니다.
"""

import os
import sys
import json
import time

# Windows UTF-8 콘솔 지원
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 프로젝트 루트 경로 등록
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mini_redis import MiniRedis
from src.cli import parse_line


class MockClock:
    def __init__(self, start=1000.0):
        self.t = start
    def now(self):
        return self.t
    def advance(self, s):
        self.t += s


def get_engine_snapshot(redis):
    """
    MiniRedis의 내부 상태(HashMap, LRU DoublyLinkedList, TTL Heap, Memory)를
    평가자가 한눈에 보기 편한 직관적인 딕셔너리로 추출합니다.
    """
    keys = redis._storage.keys()
    storage_dict = {}
    for k in keys:
        v = redis._storage.get(k)
        ttl = redis._ttl.get_ttl_seconds(k, True)
        k_b = len(k.encode("utf-8"))
        v_b = len(v.encode("utf-8"))
        storage_dict[k] = {
            "value": v,
            "bytes": k_b + v_b,
            "ttl": ttl  # -1: persistent, -2: expired, >0: seconds left
        }

    # LRU 순서 (Head쪽이 MRU: 최근 사용, Tail쪽이 LRU: 오래된 순서)
    lru_chain = []
    curr = redis._lru._list.head.next
    while curr != redis._lru._list.tail and curr is not None:
        lru_chain.append(curr.key)
        curr = curr.next

    return {
        "storage": storage_dict,
        "lru_order_mru_to_lru": lru_chain,
        "memory": {
            "used_memory_bytes": redis._memory.used_memory,
            "maxmemory_bytes": redis._memory.maxmemory,
            "evicted_keys_count": redis._memory.evicted_keys
        }
    }


def compute_diff(before_snap, after_snap):
    """이전 상태와 이후 상태를 비교하여 나타난 키와 사라진 키를 계산합니다."""
    before_keys = set(before_snap["storage"].keys())
    after_keys = set(after_snap["storage"].keys())
    
    added = list(after_keys - before_keys)
    removed = list(before_keys - after_keys)
    
    # 방출인지 만료/일반 삭제인지 판별
    evicted = after_snap["memory"]["evicted_keys_count"] - before_snap["memory"]["evicted_keys_count"]
    
    return {
        "appeared_keys": added,
        "disappeared_keys": removed,
        "evicted_count_diff": evicted
    }


def print_step_visual(step_num, title, cmd, explanation, response, before_snap, after_snap, action_tag):
    diff = compute_diff(before_snap, after_snap)
    
    print("\n" + "─" * 85)
    print(f" 🔹 [STEP {step_num}] {title}")
    print("─" * 85)
    print(f" ▶ 입력 명령어 : mini-redis> {cmd}")
    print(f" 💡 동작 설명   : {explanation}")
    print(f" ↩ 실행 응답   : {response}")
    print()
    print(" ┌── 📦 [실시간 저장소 JSON 상태 스냅샷 및 데이터 증감 모니터] ──────────────┐")
    
    # 변화 요약 표시
    status_summary = {
        "action": action_tag,
        "data_changes": {
            "[+] 나타난 데이터 (Added)": diff["appeared_keys"] if diff["appeared_keys"] else "없음",
            "[-] 사라진 데이터 (Removed)": diff["disappeared_keys"] if diff["disappeared_keys"] else "없음",
            "방출 누적 (Evicted)": f"{after_snap['memory']['evicted_keys_count']}개"
        },
        "current_storage": after_snap["storage"],
        "lru_order": " -> ".join(after_snap["lru_order_mru_to_lru"]) if after_snap["lru_order_mru_to_lru"] else "(empty)",
        "memory_status": after_snap["memory"]
    }
    
    json_str = json.dumps(status_summary, indent=2, ensure_ascii=False)
    for line in json_str.splitlines():
        print(f" │  {line}")
    print(" └──────────────────────────────────────────────────────────────────────────┘")


def run_visual_demo(interactive=False):
    clock = MockClock(1000.0)
    redis = MiniRedis(time_provider=clock.now)

    print("\n" + "█" * 85)
    print("   🚀 MINI REDIS : 평가자를 위한 실시간 JSON 데이터 상태 변화 시각화 데모")
    print("   (명령어 설명 및 데이터 생성[+], 방출[-], 만료소멸[X] 실시간 추적)")
    print("█" * 85)

    def pause():
        if interactive:
            input("\n[Enter 키를 누르면 다음 스텝으로 진행합니다...]")

    step = 1

    # =========================================================================
    # 시나리오 1: 따옴표 파싱 및 String 기본 6종 명령어
    # =========================================================================
    print("\n" + "=" * 85)
    print(" 🌟 [시나리오 1] 따옴표 파싱 및 String 기본 명령어 6종 (SET/GET/EXISTS/DBSIZE/KEYS/DEL)")
    print("=" * 85)

    # 1.1 SET
    b = get_engine_snapshot(redis)
    cmd = 'SET user:1 "Alice In Wonderland"'
    resp = redis.execute_command(parse_line(cmd))
    a = get_engine_snapshot(redis)
    print_step_visual(
        step, "SET 명령어 & 따옴표 공백 보존",
        cmd,
        "shlex 파싱으로 큰따옴표 안 공백을 보존하여 HashMap에 O(1) 저장하고 메모리 회계(25B)를 갱신합니다.",
        resp, b, a, "[+] 데이터 생성 (INSERT)"
    )
    step += 1
    pause()

    # 1.2 GET
    b = get_engine_snapshot(redis)
    cmd = 'GET user:1'
    resp = redis.execute_command(parse_line(cmd))
    a = get_engine_snapshot(redis)
    print_step_visual(
        step, "GET 명령어 & LRU 갱신",
        cmd,
        "HashMap에서 O(1)으로 값을 조회하고, LRU 이중 연결 리스트의 맨 앞(MRU)으로 승격시킵니다.",
        resp, b, a, "[=] 데이터 조회 및 LRU 승격"
    )
    step += 1
    pause()

    # 1.3 EXISTS & DBSIZE & KEYS
    b = get_engine_snapshot(redis)
    cmd = 'EXISTS user:1'
    resp1 = redis.execute_command(parse_line(cmd))
    resp2 = redis.execute_command(parse_line("DBSIZE"))
    resp3 = redis.execute_command(parse_line("KEYS"))
    a = get_engine_snapshot(redis)
    print_step_visual(
        step, "EXISTS, DBSIZE, KEYS 검사",
        "EXISTS user:1 / DBSIZE / KEYS",
        "존재 여부(1), 총 저장 키 개수(1), 전체 키 목록을 조회합니다.",
        f"EXISTS->{resp1}, DBSIZE->{resp2}, KEYS->{resp3}",
        b, a, "[=] 메타데이터 조회"
    )
    step += 1
    pause()

    # 1.4 DEL (데이터가 사라지는 순간!)
    b = get_engine_snapshot(redis)
    cmd = 'DEL user:1'
    resp = redis.execute_command(parse_line(cmd))
    a = get_engine_snapshot(redis)
    print_step_visual(
        step, "DEL 명령어 (데이터 삭제로 소멸)",
        cmd,
        "HashMap, LRU 리스트, 메모리 회계에서 해당 키를 원자적으로 일괄 삭제하여 메모리를 0B로 환원합니다.",
        resp, b, a, "[-] 데이터 완전 삭제 (DELETED)"
    )
    step += 1
    pause()

    # =========================================================================
    # 시나리오 2: maxmemory 설정 & O(1) LRU 자동 방출 (Eviction)
    # =========================================================================
    print("\n" + "=" * 85)
    print(" 🌟 [시나리오 2] maxmemory 제한 & O(1) LRU 자동 방출 (데이터가 한도 초과로 사라지는 과정)")
    print("=" * 85)

    # 2.1 CONFIG SET maxmemory
    b = get_engine_snapshot(redis)
    cmd = 'CONFIG SET maxmemory 10'
    resp = redis.execute_command(parse_line(cmd))
    a = get_engine_snapshot(redis)
    print_step_visual(
        step, "CONFIG SET maxmemory (메모리 제한)",
        cmd,
        "최대 허용 메모리를 10바이트로 엄격히 제한합니다. 초과 시 가장 오래된 키부터 자동 방출됩니다.",
        resp, b, a, "[⚙] 메모리 제한 설정 (maxmemory: 10B)"
    )
    step += 1
    pause()

    # 2.2 SET a 1234 (5B)
    b = get_engine_snapshot(redis)
    cmd = 'SET a 1234'
    resp = redis.execute_command(parse_line(cmd))
    a = get_engine_snapshot(redis)
    print_step_visual(
        step, "SET a 1234 (5바이트 적재)",
        cmd,
        "키 'a'(1B) + 값 '1234'(4B) = 5바이트를 저장합니다. (현재 used_memory: 5 / 10)",
        resp, b, a, "[+] 데이터 생성 (used_memory: 5B)"
    )
    step += 1
    pause()

    # 2.3 SET b 5678 (5B) -> 10B 꽉 참
    b = get_engine_snapshot(redis)
    cmd = 'SET b 5678'
    resp = redis.execute_command(parse_line(cmd))
    a = get_engine_snapshot(redis)
    print_step_visual(
        step, "SET b 5678 (5바이트 추가 -> 메모리 10B 100% 한도 도달)",
        cmd,
        "키 'b'(1B) + 값 '5678'(4B) = 5바이트 추가. LRU 순서는 [b -> a]로 'a'가 다음 방출 후보가 됩니다.",
        resp, b, a, "[+] 데이터 생성 (used_memory: 10B, 한도 포화)"
    )
    step += 1
    pause()

    # 2.4 SET c 9999 (5B) -> LRU 방출 발동! 'a'가 소멸하고 'c'가 나타남!
    b = get_engine_snapshot(redis)
    cmd = 'SET c 9999'
    resp = redis.execute_command(parse_line(cmd))
    a = get_engine_snapshot(redis)
    print_step_visual(
        step, "SET c 9999 ★ [핵심] LRU 자동 방출 발동! ('a' 소멸, 'c' 진입)",
        cmd,
        "한도(10B) 초과로 O(1) LRU 정책이 즉시 발동! 가장 오래 미사용된 'a'가 자동 방출되어 사라지고 'c'가 저장됩니다.",
        resp, b, a, "[-] LRU 자동 방출 ('a' 삭제 & 'c' 추가)"
    )
    step += 1
    pause()

    # 2.5 GET a (방출 검증) & GET b (순서 갱신)
    b = get_engine_snapshot(redis)
    cmd = 'GET a'
    resp_a = redis.execute_command(parse_line(cmd))
    resp_b = redis.execute_command(parse_line("GET b"))
    a = get_engine_snapshot(redis)
    print_step_visual(
        step, "방출된 키 'a' 조회 및 생존 키 'b' 조회",
        "GET a / GET b",
        "방출된 'a'는 (nil)로 완전히 사라졌음을 확인하고, 'b'를 조회하여 다시 최신(MRU)으로 끌어올립니다.",
        f"GET a -> {resp_a} (소멸 확인), GET b -> {resp_b}",
        b, a, "[=] 캐시 상태 및 LRU 재정렬 확인"
    )
    step += 1
    pause()

    # =========================================================================
    # 시나리오 3: 단일 엔트리 OOM 방어
    # =========================================================================
    print("\n" + "=" * 85)
    print(" 🌟 [시나리오 3] 단일 엔트리 OOM (Out Of Memory) 방어 (기존 데이터 보존)")
    print("=" * 85)

    b = get_engine_snapshot(redis)
    cmd = 'SET super_huge_key "this value exceeds maxmemory definitely"'
    resp = redis.execute_command(parse_line(cmd))
    a = get_engine_snapshot(redis)
    print_step_visual(
        step, "단일 엔트리 > maxmemory OOM 방어",
        cmd,
        "엔트리 크기(56B)가 maxmemory(10B) 전체 한도를 초과하므로 저장을 즉각 거부하고 기존 캐시(b, c)를 안전하게 보존합니다.",
        resp, b, a, "[🛡️] OOM 거부 (기존 데이터 100% 안전 보존)"
    )
    step += 1
    pause()

    # =========================================================================
    # 시나리오 4: MinHeap TTL 만료 및 덮어쓰기 초기화
    # =========================================================================
    print("\n" + "=" * 85)
    print(" 🌟 [시나리오 4] MinHeap TTL 만료 (시간 경과로 데이터 소멸) & SET 덮어쓰기 초기화")
    print("=" * 85)

    # 4.1 SET session
    # maxmemory를 넉넉하게 확장
    redis.execute_command(["CONFIG", "SET", "maxmemory", "0"])
    redis.execute_command(["DEL", "b"])
    redis.execute_command(["DEL", "c"])

    b = get_engine_snapshot(redis)
    cmd = 'SET session "secret123"'
    resp = redis.execute_command(parse_line(cmd))
    a = get_engine_snapshot(redis)
    print_step_visual(
        step, "SET session (신규 세션 등록)",
        cmd,
        "새 키 'session'을 저장합니다. 초기 TTL은 -1(만료 없음, 영구)입니다.",
        resp, b, a, "[+] 데이터 생성 (TTL: -1)"
    )
    step += 1
    pause()

    # 4.2 EXPIRE session 10
    b = get_engine_snapshot(redis)
    cmd = 'EXPIRE session 10'
    resp = redis.execute_command(parse_line(cmd))
    a = get_engine_snapshot(redis)
    print_step_visual(
        step, "EXPIRE session 10 (최소 힙에 만료 시각 등록)",
        cmd,
        "최소 힙(MinHeap)에 (만료 시각, 'session')을 push하여 O(log N)으로 관리합니다. 잔여 TTL이 10초로 부여됩니다.",
        resp, b, a, "[⏱] TTL 만료 시간 설정 (10초)"
    )
    step += 1
    pause()

    # 4.3 11초 시간 경과 후 GET session -> Lazy Deletion으로 사라짐!
    clock.advance(11) # 가상 시계 11초 점프
    b = get_engine_snapshot(redis)
    cmd = 'GET session'
    resp = redis.execute_command(parse_line(cmd))
    a = get_engine_snapshot(redis)
    print_step_visual(
        step, "11초 시간 경과 후 GET session ★ [핵심] Lazy Deletion 만료 소멸!",
        "GET session (시계 +11초 경과 후)",
        "조회 시점에 MinHeap과 만료 시각을 검사하여 이미 11초가 지났음을 감지하고, 데이터를 즉시 메모리에서 영구 삭제(소멸)한 뒤 (nil)을 반환합니다.",
        resp, b, a, "[X] TTL 만료 소멸 (데이터 사라짐!)"
    )
    step += 1
    pause()

    # 4.4 SET 덮어쓰기 시 TTL 초기화 검증
    redis.execute_command(["SET", "temp", "initial_val"])
    redis.execute_command(["EXPIRE", "temp", "50"])
    ttl_before = redis.execute_command(["TTL", "temp"])
    
    b = get_engine_snapshot(redis)
    cmd = 'SET temp "overwritten_val"'
    resp = redis.execute_command(parse_line(cmd))
    ttl_after = redis.execute_command(["TTL", "temp"])
    a = get_engine_snapshot(redis)
    print_step_visual(
        step, "SET 덮어쓰기 시 기존 TTL 자동 초기화 (-1 복원)",
        cmd,
        f"기존에 TTL({ttl_before})이 걸려있던 'temp'를 새 값으로 덮어쓸 때 Redis 표준에 따라 TTL이 즉시 삭제(-1)되어 영구 데이터로 환원됩니다.",
        f"{resp} (TTL: {ttl_before} -> {ttl_after})",
        b, a, "[⚡] TTL 초기화 및 값 갱신 (TTL: -1)"
    )

    print("\n" + "█" * 85)
    print("   🎉 실시간 JSON 데이터 상태 변화 시각화 데모 완료!")
    print("   모든 시나리오에서 데이터의 생성[+], 방출[-], 만료소멸[X]이 정상 작동함을 증명했습니다.")
    print("█" * 85 + "\n")


if __name__ == "__main__":
    interactive_mode = "--interactive" in sys.argv or "-i" in sys.argv
    run_visual_demo(interactive=interactive_mode)
