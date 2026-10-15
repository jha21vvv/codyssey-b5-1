# [1차]: Mini Redis CLI REPL(Read-Eval-Print Loop) 대화형 인터페이스 모듈을 정의합니다.
# [2차]: 손님이 가게에 들어와 카운터에서 말로 주문하고 응답을 받는 접수 창구를 만듭니다.
"""
CLI REPL 인터페이스 모듈
사용자로부터 명령어를 입력받아 MiniRedis 엔진에 전달하고 결과를 포맷팅하여 출력합니다.
"""

# [1차]: 시스템 입출력 제어를 위한 표준 sys 모듈을 임포트합니다.
# [2차]: 매장 문과 통신 장치를 가져옵니다.
import sys
# [1차]: 따옴표와 공백을 셸 표준 방식으로 파싱하기 위한 표준 shlex 모듈을 임포트합니다.
# [2차]: 손님이 따옴표로 감싸서 말한 긴 문장을 단어별로 깔끔하게 쪼개주는 번역기를 가져옵니다.
import shlex
# [1차]: 비즈니스 로직을 수행할 MiniRedis 코어 엔진을 임포트합니다.
# [2차]: 주방에서 실제로 요리를 해줄 총괄 매니저를 모셔옵니다.
from src.mini_redis import MiniRedis


# [1차]: 사용자 입력 문자열을 공백 및 따옴표 규칙에 따라 토큰 리스트로 분할합니다.
# [2차]: 손님의 긴 말 한마디를 하나하나의 단어 주문서로 예쁘게 잘라냅니다.
def parse_line(line):
    """
    명령줄 문자열을 공백 및 따옴표 규칙에 맞추어 분할합니다.
    shlex를 사용하여 큰따옴표/작은따옴표로 감싸진 문자열을 원자적으로 파싱합니다.
    """
    # [1차]: 정상적인 shlex.split 파싱을 시도합니다.
    # [2차]: 따옴표 문법을 지키며 쪼개봅니다.
    try:
        # [1차]: shlex.split(line)으로 분할된 인자 리스트를 반환합니다.
        # [2차]: 쪼갠 단어 목록을 건넵니다.
        return shlex.split(line)
    # [1차]: 따옴표가 닫히지 않은 경우 ValueError 예외를 잡습니다.
    # [2차]: 따옴표를 깜빡 잊고 안 닫았을 때 당황하지 않고 대처합니다.
    except ValueError:
        # [1차]: 폴백으로 단순 공백 분할을 수행합니다.
        # [2차]: 그냥 단순 띄어쓰기 기준으로 쪼개서 반환합니다.
        return line.strip().split()


# Windows 콘솔 UTF-8 인코딩 방어 (오류 시 대체)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def format_json_state(redis, added_keys, removed_keys):
    """
    내장 dict, set 없이 오직 문자열 포맷팅으로 유효한 JSON 상태를 생성합니다.
    (AST Zero Built-in Collections 제약 100% 준수)
    """
    keys = redis._storage.keys()
    entry_lines = []
    for k in keys:
        v = redis._storage.get(k)
        ttl = redis._ttl.get_ttl_seconds(k, True)
        if ttl != -1:
            entry_lines.append('      "' + str(k) + '": { "value": "' + str(v) + '", "ttl": ' + str(ttl) + ' }')
        else:
            entry_lines.append('      "' + str(k) + '": { "value": "' + str(v) + '" }')
    storage_block = ",\n".join(entry_lines)

    added_str = "[" + ", ".join(['"' + str(k) + '"' for k in added_keys]) + "]"
    removed_str = "[" + ", ".join(['"' + str(k) + '"' for k in removed_keys]) + "]"

    used = redis._memory.used_memory
    maxmem = redis._memory.maxmemory
    evicted = redis._memory.evicted_keys

    lines = [
        "  {",
        '    "changes": { "added": ' + added_str + ', "removed": ' + removed_str + ' },',
        '    "storage": {',
    ]
    if entry_lines:
        lines.append(storage_block)
    lines.extend([
        '    },',
        '    "memory": {',
        '      "used_memory": ' + str(used) + ',',
        '      "maxmemory": ' + str(maxmem) + ',',
        '      "evicted_keys": ' + str(evicted),
        '    }',
        "  }"
    ])
    return "\n".join(lines)


def save_json_file(json_str, filepath="redis_state.json"):
    """
    실시간 저장소 상태를 물리적 JSON 파일로 저장합니다.
    (VSCode 또는 에디터에 열어두면 데이터가 나타나고 사라지는 것을 실시간 관찰 가능)
    """
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(json_str.strip() + "\n")
    except Exception:
        pass


# [1차]: 터미널에서 사용자 입력을 반복 대기하고 처리하는 메인 REPL 루프 함수를 정의합니다.
# [2차]: 매장 문을 열고 손님이 나갈 때까지 계속 주문을 받는 카운터 루프입니다.
def run_cli():
    """
    Mini Redis REPL 루프 (명령어 1개 입력 시마다 실시간 JSON 파일 및 터미널 상태 자동 갱신)
    """
    redis = MiniRedis()
    print("Welcome to Mini Redis CLI! Type 'exit' or 'quit' to close.")
    print("Zero-dependency from-scratch key-value store.")

    # 시작 시 초기 빈 상태 JSON 파일 즉시 생성
    initial_json = format_json_state(redis, [], [])
    save_json_file(initial_json)

    while True:
        try:
            line = input("mini-redis> ").strip()
            if not line:
                continue

            if line.lower() in ("exit", "quit"):
                print("Bye!")
                break

            args = parse_line(line)
            if not args:
                continue

            # 명령어 실행 전 키 목록 스냅샷 (내장 set 없이 리스트로 추적)
            prev_keys = list(redis._storage.keys())

            # MiniRedis 명령어 실행
            response = redis.execute_command(args)
            if response:
                print(response)

            # 명령어 실행 후 키 목록 스냅샷
            curr_keys = list(redis._storage.keys())
            added = [k for k in curr_keys if k not in prev_keys]
            removed = [k for k in prev_keys if k not in curr_keys]

            # 실시간 JSON 상태 포맷팅
            json_text = format_json_state(redis, added, removed)

            # 1. 실제 물리적 파일 'redis_state.json'에만 실시간 자동 갱신 (터미널 출력 안 함)
            save_json_file(json_text)

        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            break
        # [1차]: 그 외 예기치 않은 시스템 예외를 포착합니다.
        # [2차]: 뜻밖의 사고가 발생해도 프로그램이 갑자기 튕기지 않게 방어합니다.
        except Exception as e:
            # [1차]: 에러 메시지를 포맷팅하여 출력합니다.
            # [2차]: 어떤 문제가 생겼는지 친절히 알려줍니다.
            print(f"(error) ERR unexpected system error: {e}")


# [1차]: 이 파일이 메인 모듈로 직접 실행되었을 때 run_cli를 호출합니다.
# [2차]: 이 파일을 직접 더블 클릭하면 카운터를 즉시 엽니다.
if __name__ == "__main__":
    # [1차]: CLI 루프 실행
    # [2차]: 카운터 개장
    run_cli()
