# [1차]: MiniRedis 코어 엔진 모듈을 정의합니다.
# [2차]: 손님의 주문을 접수하고 저장소, 캐시, 유통기한, 저울을 지휘하는 만능 총괄 매니저입니다.
"""
MiniRedis 코어 엔진 모듈
내장 dict, set, collections를 일절 사용하지 않고
직접 구현한 HashMap, DoublyLinkedList, MinHeap을 조화시켜 Redis 명령어를 처리합니다.
"""

# [1차]: 시간 측정을 위한 표준 time 모듈을 임포트합니다.
# [2차]: 중앙 관제탑 시계를 임포트합니다.
import time
# [1차]: 주 저장소로 사용할 자체 HashMap 클래스를 임포트합니다.
# [2차]: 메인 우편함 수납장을 가져옵니다.
from src.hash_map import HashMap
# [1차]: LRU 캐시 순서 추적을 위한 LRUManager 클래스를 임포트합니다.
# [2차]: 최근 사용 순서를 추적하는 스마트 책꽂이 관리인을 데려옵니다.
from src.lru_cache import LRUManager
# [1차]: 메모리 한도 및 바이트 회계를 담당하는 MemoryManager 클래스를 임포트합니다.
# [2차]: 가방 무게를 달아보는 정밀 저울을 가져옵니다.
from src.memory_manager import MemoryManager
# [1차]: 만료 시각 및 최소 힙 정돈을 담당하는 TTLManager 클래스를 임포트합니다.
# [2차]: 유통기한 담당자를 데려옵니다.
from src.ttl_manager import TTLManager


# [1차]: Redis 호환 프로토콜과 메모리/TTL/LRU 정책을 통합 제어하는 MiniRedis 클래스를 선언합니다.
# [2차]: Mini Redis 매장의 총사령관 클래스입니다.
class MiniRedis:
    """
    Mini Redis 코어 엔진
    - Key-Value Storage: 자체 HashMap
    - LRU Tracking: LRUManager (DoublyLinkedList + HashMap)
    - TTL Management: TTLManager (MinHeap + HashMap)
    - Memory Management: MemoryManager
    """
    # [1차]: MiniRedis 인스턴스를 초기화하며 주 저장소, LRU, TTL, 메모리 매니저를 바인딩합니다.
    # [2차]: 매장 문을 열고 4명의 전문 직원(저장소, 책꽂이, 유통기한, 저울)을 채용하여 배치합니다.
    def __init__(self, time_provider=time.time):
        # [1차]: 시간 제공자 함수를 인스턴스 변수에 저장합니다.
        # [2차]: 매장 공식 표준시계를 설정합니다.
        self._time_provider = time_provider
        # [1차]: 키-값을 보관할 메인 HashMap을 인스턴스화합니다.
        # [2차]: 물건을 실제로 보관할 메인 수납장을 세웁니다.
        self._storage = HashMap()
        # [1차]: LRU 추적용 LRUManager를 인스턴스화합니다.
        # [2차]: LRU 책꽂이 순서판을 엽니다.
        self._lru = LRUManager()
        # [1차]: TTL 만료 관리용 TTLManager를 인스턴스화합니다.
        # [2차]: 유통기한 최소 힙 진열대를 준비합니다.
        self._ttl = TTLManager(time_provider=self._time_provider)
        # [1차]: 바이트 단위 메모리 관리를 위한 MemoryManager를 인스턴스화합니다.
        # [2차]: 전자저울을 켜둡니다.
        self._memory = MemoryManager()

    # [1차]: 저장소, LRU, TTL, 메모리 매니저에서 특정 키의 엔트리를 원자적으로 일괄 삭제합니다.
    # [2차]: 매장에서 물건을 뺄 때 4군데 장부에서 단 1개의 누락도 없이 깔끔하게 한 번에 지웁니다.
    def _delete_entry(self, key, is_eviction=False, is_expired=False):
        """
        내부 엔트리 완전 삭제 헬퍼 (저장소, LRU, TTL, 메모리에서 일괄 제거)
        """
        # [1차]: 메인 저장소 HashMap에서 키를 제거하고 기존 값을 가져옵니다.
        # [2차]: 메인 수납장에서 물건을 꺼냅니다.
        val = self._storage.remove(key)
        # [1차]: 기존 값이 존재하는 경우에만 나머지 구조에서도 동기화 제거를 수행합니다.
        # [2차]: 물건이 진짜 있었던 경우에만 다른 장부들도 정리합니다.
        if val is not None:
            # [1차]: LRU 관리자에서 해당 키를 O(1)으로 제거합니다.
            # [2차]: LRU 책꽂이 명부에서 지웁니다.
            self._lru.remove(key)
            # [1차]: TTL 관리자에서 해당 키의 만료 설정을 제거합니다.
            # [2차]: 유통기한 장부에서 지웁니다.
            self._ttl.remove_ttl(key)
            # [1차]: 메모리 관리자에서 해당 엔트리의 UTF-8 바이트 크기를 차감합니다.
            # [2차]: 저울에서 빠진 물건 무게를 뺍니다.
            self._memory.remove_entry_memory(key, val)
            # [1차]: 삭제 성공을 알리는 True를 반환합니다.
            # [2차]: 성공 보고를 올립니다.
            return True
        # [1차]: 삭제할 키가 없으면 False를 반환합니다.
        # [2차]: 없었음을 보고합니다.
        return False

    # [1차]: 키가 만료되었는지 사전에 검사하고 만료되었으면 즉각 삭제합니다.
    # [2차]: 손님이 찾기 전에 유통기한이 지났는지 먼저 쓱 확인하고 상했으면 그 자리에서 버립니다.
    def _check_and_expire(self, key):
        """
        키가 만료되었는지 확인하고, 만료되었으면 즉시 삭제합니다.
        삭제되었으면 True, 여전히 유효하거나 없으면 False 반환
        """
        # [1차]: 저장소에 키가 아예 없다면 만료 검사가 불필요하므로 False를 반환합니다.
        # [2차]: 매장에 아예 없는 물건이면 검사할 것도 없습니다.
        if not self._storage.contains(key):
            # [1차]: False 반환
            # [2차]: 없음 보고
            return False
        
        # [1차]: TTL 관리자에게 해당 키가 만료 시각을 지났는지 확인합니다.
        # [2차]: 유통기한 담당자에게 상했는지 물어봅니다.
        if self._ttl.is_expired(key):
            # [1차]: 만료되었으므로 내부 삭제 헬퍼를 호출하여 일괄 제거합니다.
            # [2차]: 상했으니 매장에서 즉시 폐기 처리합니다.
            self._delete_entry(key, is_expired=True)
            # [1차]: 만료 삭제되었음을 뜻하는 True를 반환합니다.
            # [2차]: 만료 폐기 완료 보고를 올립니다.
            return True
        # [1차]: 아직 신선하고 유효한 경우 False를 반환합니다.
        # [2차]: 안전함을 확인합니다.
        return False

    # [1차]: 인자 리스트를 받아 명령어를 파싱하고 적절한 서브 루틴을 라우팅하여 실행 결과를 반환합니다.
    # [2차]: 손님이 카운터에서 외친 명령어를 듣고 알맞은 담당 직원에게 일을 시킵니다.
    def execute_command(self, args):
        """
        파싱된 인자 리스트(예: ['SET', 'name', 'Alice'])를 받아 적절한 명령어를 실행하고
        Redis 표준 응답 문자열을 반환합니다.
        """
        # [1차]: 인자가 빈 리스트인 경우 빈 문자열을 반환합니다.
        # [2차]: 손님이 아무 말도 안 했으면 가만히 있습니다.
        if not args:
            # [1차]: 빈 문자열 반환
            # [2차]: 침묵
            return ""

        # [1차]: 명령어 이름을 대문자로 정규화합니다.
        # [2차]: 손님이 소문자로 말하든 대문자로 말하든 알아듣기 쉽게 대문자로 통일합니다.
        cmd = args[0].upper()

        # [1차]: 명령어 종류에 따라 분기하여 전용 처리 함수를 호출합니다.
        # [2차]: 외친 주문 메뉴에 따라 담당 요리사에게 접수합니다.
        if cmd == "SET":
            # [1차]: SET 명령어 실행
            # [2차]: 저장하기
            return self._cmd_set(args)
        elif cmd == "GET":
            # [1차]: GET 명령어 실행
            # [2차]: 꺼내보기
            return self._cmd_get(args)
        elif cmd == "DEL":
            # [1차]: DEL 명령어 실행
            # [2차]: 지우기
            return self._cmd_del(args)
        elif cmd == "EXISTS":
            # [1차]: EXISTS 명령어 실행
            # [2차]: 있는지 확인
            return self._cmd_exists(args)
        elif cmd == "DBSIZE":
            # [1차]: DBSIZE 명령어 실행
            # [2차]: 총 개수 세기
            return self._cmd_dbsize(args)
        elif cmd == "KEYS":
            # [1차]: KEYS 명령어 실행
            # [2차]: 전체 목록 보기
            return self._cmd_keys(args)
        elif cmd == "CONFIG":
            # [1차]: CONFIG 명령어 실행
            # [2차]: 설정 변경
            return self._cmd_config(args)
        elif cmd == "INFO":
            # [1차]: INFO 명령어 실행
            # [2차]: 정보 조회
            return self._cmd_info(args)
        elif cmd == "EXPIRE":
            # [1차]: EXPIRE 명령어 실행
            # [2차]: 유통기한 붙이기
            return self._cmd_expire(args)
        elif cmd == "TTL":
            # [1차]: TTL 명령어 실행
            # [2차]: 남은 시간 조회
            return self._cmd_ttl(args)
        else:
            # [1차]: 정의되지 않은 알 수 없는 명령어 에러를 Redis 표준 포맷으로 반환합니다.
            # [2차]: 메뉴판에 없는 메뉴를 시키면 그런 메뉴 없다고 정중히 거절합니다.
            return f"(error) ERR unknown command '{args[0]}'"

    # [1차]: SET key value 명령어를 처리합니다.
    # [2차]: 수납장에 새 물건을 꽂고 저울과 책꽂이 순서를 갱신합니다.
    def _cmd_set(self, args):
        """SET key value"""
        # [1차]: 인자 개수가 정확히 3개(SET, key, value)인지 검증합니다.
        # [2차]: 주문 인자 수가 안 맞으면 주문서를 반려합니다.
        if len(args) != 3:
            # [1차]: Redis 인자 개수 오류 반환
            # [2차]: 에러 통보
            return "(error) ERR wrong number of arguments for 'set' command"

        # [1차]: key와 value를 추출합니다.
        # [2차]: 이름표와 내용물을 손에 쥡니다.
        key, value = args[1], args[2]

        # [1차]: 단일 엔트리 자체가 maxmemory를 초과하는지 OOM을 사전 검사합니다.
        # [2차]: 이 물건 1개의 무게가 가방 전체 용량보다 더 무거운지 저울에 대봅니다.
        if self._memory.is_single_entry_oom(key, value):
            # [1차]: OOM 에러 메시지 반환
            # [2차]: 가방 터짐 에러 통보
            return "(error) OOM command not allowed when used_memory > 'maxmemory'"

        # [1차]: 실행 전 기존 키가 만료 상태인지 확인하고 지웁니다.
        # [2차]: 혹시 예전에 만료된 채 방치된 물건이 있다면 치웁니다.
        self._check_and_expire(key)

        # [1차]: 기존 키의 값이 존재하는지 조회합니다.
        # [2차]: 이미 꽂혀 있던 물건이 있는지 봅니다.
        existing_val = self._storage.get(key)
        # [1차]: 기존 값이 존재하는 경우 (덮어쓰기 분기)
        # [2차]: 덮어쓰기 상황입니다.
        if existing_val is not None:
            # [1차]: 덮어쓰기 시 기존 키에 걸려있던 TTL 설정을 규격에 따라 초기화(삭제)합니다.
            # [2차]: 새 물건으로 갈아 끼웠으니 이전 유통기한 딱지를 싹 떼어냅니다.
            self._ttl.remove_ttl(key)
            # [1차]: 값 차이만큼 메모리 사용량을 갱신합니다.
            # [2차]: 내용물 교체로 인한 무게 변화를 저울에 반영합니다.
            self._memory.update_entry_memory(key, existing_val, value)
            # [1차]: 주 저장소에 새 값을 put합니다.
            # [2차]: 수납장에 새 물건을 꽂습니다.
            self._storage.put(key, value)
        else:
            # [1차]: 신규 키 삽입 분기
            # [2차]: 완전히 새로운 물건을 처음 들여놓는 상황입니다.
            self._memory.add_entry_memory(key, value)
            # [1차]: 주 저장소에 키-값을 저장합니다.
            # [2차]: 수납장에 새 자리를 만들어 꽂습니다.
            self._storage.put(key, value)

        # [1차]: LRU 캐시 관리자에게 키 접근을 통보하여 맨 앞으로 승격시킵니다.
        # [2차]: 이 책을 책꽂이 맨 앞 1등석으로 옮깁니다.
        self._lru.access(key)

        # [1차]: 메모리 한도가 초과되었다면 한도 이하가 될 때까지 LRU 키들을 지속 방출합니다.
        # [2차]: 가방이 꽉 찼으면 한도 안으로 들어올 때까지 가장 오래 안 본 책부터 밖으로 던집니다.
        self._memory.evict_if_needed(self._lru, self._delete_entry)

        # [1차]: 성공 응답 'OK'를 반환합니다.
        # [2차]: 잘 저장되었다고 'OK' 도장을 찍어줍니다.
        return "OK"

    # [1차]: GET key 명령어를 처리합니다.
    # [2차]: 수납장에서 물건을 꺼내어 손님에게 보여줍니다.
    def _cmd_get(self, args):
        """GET key"""
        # [1차]: 인자 개수가 2개(GET, key)인지 검증합니다.
        # [2차]: 인자가 안 맞으면 거절합니다.
        if len(args) != 2:
            # [1차]: 인자 개수 오류 반환
            # [2차]: 에러 통보
            return "(error) ERR wrong number of arguments for 'get' command"

        # [1차]: 대상 key를 추출합니다.
        # [2차]: 찾으려는 이름표를 확인합니다.
        key = args[1]

        # [1차]: 키의 만료 여부를 검사하여 만료되었으면 삭제 후 (nil)을 반환합니다.
        # [2차]: 꺼내기 전에 유통기한을 보니 상했으면 바로 버리고 "(nil)"(없음)이라고 답합니다.
        if self._check_and_expire(key):
            # [1차]: (nil) 반환 (LRU 갱신 없음)
            # [2차]: 상해서 버렸으니 없음 통보
            return "(nil)"

        # [1차]: 저장소에서 값을 조회합니다.
        # [2차]: 수납장에서 물건을 꺼냅니다.
        val = self._storage.get(key)
        # [1차]: 값이 없으면 (nil)을 반환합니다.
        # [2차]: 원래 없던 물건이면 "(nil)"이라고 답합니다.
        if val is None:
            # [1차]: (nil) 반환
            # [2차]: 없음 통보
            return "(nil)"

        # [1차]: 조회 성공 시에만 LRU 순서를 최신으로 갱신합니다.
        # [2차]: 손님이 읽어본 책이니 책꽂이 맨 앞자리로 옮깁니다.
        self._lru.access(key)
        # [1차]: 따옴표로 감싼 Redis 스타일 문자열 포맷으로 값을 반환합니다.
        # [2차]: 예쁜 따옴표 상자에 담아 손님에게 건넵니다.
        return f'"{val}"'

    # [1차]: DEL key 명령어를 처리합니다.
    # [2차]: 매장에서 특정 물건을 영구 폐기합니다.
    def _cmd_del(self, args):
        """DEL key"""
        # [1차]: 인자 개수 검증
        # [2차]: 주문서 검증
        if len(args) != 2:
            # [1차]: 인자 오류
            # [2차]: 에러 통보
            return "(error) ERR wrong number of arguments for 'del' command"

        # [1차]: 대상 key 추출
        # [2차]: 버릴 이름표 확인
        key = args[1]

        # [1차]: 삭제 전 만료 확인 (만료 시 이미 삭제되어 (integer) 0 반환)
        # [2차]: 만료되어 이미 사라진 물건이면 지운 게 0개라고 알립니다.
        if self._check_and_expire(key):
            # [1차]: 0 반환
            # [2차]: 0개 삭제 보고
            return "(integer) 0"

        # [1차]: 내부 삭제 헬퍼를 호출하여 완전 삭제를 시도합니다.
        # [2차]: 4개 장부에서 싹 지웁니다.
        deleted = self._delete_entry(key)
        # [1차]: 삭제 성공 시 (integer) 1, 미존재 시 (integer) 0 반환
        # [2차]: 1개 지웠으면 1, 없었으면 0을 돌려줍니다.
        return "(integer) 1" if deleted else "(integer) 0"

    # [1차]: EXISTS key 명령어를 처리합니다.
    # [2차]: 매장에 이 물건이 현재 있는지 확인합니다.
    def _cmd_exists(self, args):
        """EXISTS key"""
        # [1차]: 인자 개수 검증
        # [2차]: 주문서 검증
        if len(args) != 2:
            # [1차]: 인자 오류
            # [2차]: 에러 통보
            return "(error) ERR wrong number of arguments for 'exists' command"

        # [1차]: key 추출
        # [2차]: 확인할 이름표
        key = args[1]
        # [1차]: 사전 만료 검사
        # [2차]: 유통기한 확인
        self._check_and_expire(key)

        # [1차]: 저장소에 키가 존재하는지 조회합니다.
        # [2차]: 수납장에 물건이 꽂혀 있는지 봅니다.
        exists = self._storage.contains(key)
        # [1차]: 존재 시 (integer) 1, 미존재 시 (integer) 0 반환
        # [2차]: 있으면 1, 없으면 0을 돌려줍니다.
        return "(integer) 1" if exists else "(integer) 0"

    # [1차]: DBSIZE 명령어를 처리합니다.
    # [2차]: 현재 매장에 진열된 총 유효 상품 개수를 셉니다.
    def _cmd_dbsize(self, args):
        """DBSIZE"""
        # [1차]: 인자 개수 검증
        # [2차]: 주문서 검증
        if len(args) != 1:
            # [1차]: 인자 오류
            # [2차]: 에러 통보
            return "(error) ERR wrong number of arguments for 'dbsize' command"

        # [1차]: 최소 힙을 통해 만료된 키들을 능동 정리합니다.
        # [2차]: 진열대 꼭대기를 훑어 상한 물건들을 싹 걷어냅니다.
        self._ttl.cleanup_expired(self._delete_entry)

        # [1차]: 전체 키를 순회하며 만료된 잔재가 있는지 재확인합니다.
        # [2차]: 혹시 남아있을지 모르는 상한 물건을 한 번 더 솎아냅니다.
        keys = self._storage.keys()
        for k in keys:
            self._check_and_expire(k)

        # [1차]: 현재 유효한 총 키 개수를 (integer) N 형식으로 반환합니다.
        # [2차]: 총 상품 숫자를 또박또박 셉니다.
        return f"(integer) {self._storage.size()}"

    # [1차]: KEYS 명령어를 처리하여 활성 키 목록을 배열 형식으로 출력합니다.
    # [2차]: 현재 매장에 남아있는 모든 물건의 이름표 목록을 출력합니다.
    def _cmd_keys(self, args):
        """KEYS"""
        # [1차]: 인자 개수 검증
        # [2차]: 주문서 검증
        if len(args) != 1:
            # [1차]: 인자 오류
            # [2차]: 에러 통보
            return "(error) ERR wrong number of arguments for 'keys' command"

        # [1차]: 만료된 항목을 능동 청소합니다.
        # [2차]: 상한 물건을 먼저 싹 정리합니다.
        self._ttl.cleanup_expired(self._delete_entry)
        # [1차]: 원시 키 목록을 가져옵니다.
        # [2차]: 수납장에 꽂힌 이름표들을 꺼냅니다.
        raw_keys = self._storage.keys()
        # [1차]: 유효 키들을 담을 리스트를 준비합니다.
        # [2차]: 진짜 신선한 이름표만 적을 명부를 만듭니다.
        valid_keys = []
        # [1차]: 각 키의 만료 여부를 검사하며 유효한 키만 수집합니다.
        # [2차]: 하나씩 냄새를 맡아보고 안전한 것만 명부에 올립니다.
        for k in raw_keys:
            if not self._check_and_expire(k):
                valid_keys.append(k)

        # [1차]: 유효한 키가 하나도 없으면 (empty array)를 반환합니다.
        # [2차]: 매장이 텅 비었으면 "(empty array)"라고 알립니다.
        if not valid_keys:
            # [1차]: 비어있음 응답
            # [2차]: 빈 배열 통보
            return "(empty array)"

        # [1차]: Redis 스타일 배열(1) "key" \n 2) "key") 포맷 문자열을 조립합니다.
        # [2차]: 번호 매겨진 깔끔한 목록으로 포장합니다.
        lines = []
        for i, k in enumerate(valid_keys, 1):
            lines.append(f'{i}) "{k}"')
        # [1차]: 개행 문자로 조립하여 반환합니다.
        # [2차]: 한 줄씩 출력합니다.
        return "\n".join(lines)

    # [1차]: CONFIG SET maxmemory bytes 명령어를 처리합니다.
    # [2차]: 매장 가방의 무게 제한 한도를 변경합니다.
    def _cmd_config(self, args):
        """CONFIG SET maxmemory bytes"""
        # [1차]: 인자 구성이 CONFIG SET maxmemory <bytes> 규격인지 검증합니다.
        # [2차]: 설정 문법이 올바른지 확인합니다.
        if len(args) != 4 or args[1].upper() != "SET" or args[2].lower() != "maxmemory":
            # [1차]: 문법 오류 반환
            # [2차]: 잘못된 설정 명령 거절
            return "(error) ERR unknown command or wrong arguments for 'config'"

        # [1차]: 바이트 인자를 정수로 파싱합니다.
        # [2차]: 숫자로 똑바로 적었는지 봅니다.
        try:
            # [1차]: 정수형 변환
            # [2차]: 정수 변환
            bytes_val = int(args[3])
            # [1차]: 0 미만의 음수는 허용되지 않습니다.
            # [2차]: 마이너스 무게는 말이 안 되니 거절합니다.
            if bytes_val < 0:
                return "(error) ERR value is not an integer or out of range"
        except ValueError:
            # [1차]: 정수 파싱 실패 오류 반환
            # [2차]: 숫자가 아니면 거절
            return "(error) ERR value is not an integer or out of range"

        # [1차]: 새 maxmemory 값을 메모리 매니저에 설정합니다.
        # [2차]: 저울의 최대 한도 눈금을 새 값으로 맞춥니다.
        self._memory.maxmemory = bytes_val
        # [1차]: 한도가 줄어들어 현재 사용량을 초과한 경우 즉시 LRU 방출을 수행합니다.
        # [2차]: 가방을 좁은 가방으로 바꿨으니 넘치는 책들을 즉각 밖으로 던집니다.
        self._memory.evict_if_needed(self._lru, self._delete_entry)
        # [1차]: 성공 응답 'OK' 반환
        # [2차]: 설정 완료 'OK'
        return "OK"

    # [1차]: INFO memory 명령어를 처리하여 메모리 통계를 출력합니다.
    # [2차]: 현재 저울 상태(사용 무게, 한도 무게, 버린 책 수) 영수증을 뽑아줍니다.
    def _cmd_info(self, args):
        """INFO memory"""
        # [1차]: 인자 규격 검증
        # [2차]: 주문서 검증
        if len(args) != 2 or args[1].lower() != "memory":
            # [1차]: 인자 오류
            # [2차]: 에러 통보
            return "(error) ERR wrong number of arguments for 'info' command"

        # [1차]: 메모리 매니저의 포맷팅 결과를 반환합니다.
        # [2차]: 통계 보고서를 전달합니다.
        return self._memory.get_info_memory()

    # [1차]: EXPIRE key seconds 명령어를 처리하여 만료 시간을 설정합니다.
    # [2차]: 특정 상품에 유통기한 딱지를 새로 붙입니다.
    def _cmd_expire(self, args):
        """EXPIRE key seconds"""
        # [1차]: 인자 개수 검증 (EXPIRE, key, seconds)
        # [2차]: 주문서 검증
        if len(args) != 3:
            # [1차]: 인자 오류
            # [2차]: 에러 통보
            return "(error) ERR wrong number of arguments for 'expire' command"

        # [1차]: 대상 key 추출
        # [2차]: 상품 이름표
        key = args[1]
        # [1차]: seconds 정수 파싱 검증
        # [2차]: 초 단위 숫자가 올바른지 확인
        try:
            seconds = int(args[2])
        except ValueError:
            # [1차]: 정수 오류 반환
            # [2차]: 숫자 에러 통보
            return "(error) ERR value is not an integer or out of range"

        # [1차]: 실행 전 사전 만료 검사
        # [2차]: 이미 유통기한 지난 상품인지 확인
        if self._check_and_expire(key):
            # [1차]: 없는 키로 간주되어 0 반환
            # [2차]: 0 반환
            return "(integer) 0"

        # [1차]: 저장소에 키가 없으면 (integer) 0 반환
        # [2차]: 매장에 없는 상품이면 딱지를 붙일 수 없으니 0을 반환합니다.
        if not self._storage.contains(key):
            # [1차]: 0 반환
            # [2차]: 실패 보고
            return "(integer) 0"

        # [1차]: seconds가 0 이하이면 즉시 만료 규칙에 따라 삭제합니다.
        # [2차]: 유통기한을 0초 이하로 정하면 즉시 상한 것이므로 즉각 쓰레기통에 버립니다.
        if seconds <= 0:
            # [1차]: 내부 삭제 수행
            # [2차]: 즉각 폐기
            self._delete_entry(key, is_expired=True)
            # [1차]: (integer) 1 반환
            # [2차]: 처리 완료 보고
            return "(integer) 1"

        # [1차]: TTL 관리자에 유효 초를 등록합니다.
        # [2차]: 유통기한 딱지를 찰떡같이 붙여둡니다.
        self._ttl.set_ttl(key, seconds)
        # [1차]: 성공 시 (integer) 1 반환
        # [2차]: 1 반환
        return "(integer) 1"

    # [1차]: TTL key 명령어를 처리하여 남은 만료 초를 반환합니다.
    # [2차]: 상품의 남은 유통기한을 조회합니다.
    def _cmd_ttl(self, args):
        """TTL key"""
        # [1차]: 인자 개수 검증
        # [2차]: 주문서 검증
        if len(args) != 2:
            # [1차]: 인자 오류
            # [2차]: 에러 통보
            return "(error) ERR wrong number of arguments for 'ttl' command"

        # [1차]: 대상 key 추출
        # [2차]: 상품 이름표
        key = args[1]
        # [1차]: 사전 만료 검사
        # [2차]: 유통기한 지남 여부 확인
        self._check_and_expire(key)

        # [1차]: 저장소에 키가 실제로 존재하는지 확인합니다.
        # [2차]: 매장에 물건이 있는지 봅니다.
        key_exists = self._storage.contains(key)
        # [1차]: TTL 관리자로부터 남은 초(-2, -1, N)를 계산받습니다.
        # [2차]: 유통기한 담당자에게 남은 초를 물어봅니다.
        ttl_val = self._ttl.get_ttl_seconds(key, key_exists)
        # [1차]: (integer) N 형식으로 반환합니다.
        # [2차]: 손님에게 결과를 알려줍니다.
        return f"(integer) {ttl_val}"
