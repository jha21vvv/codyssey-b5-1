# [1차]: 최소 힙 기반 TTL(Time To Live) 관리자 모듈을 정의합니다.
# [2차]: 유통기한이 적힌 삼각김밥들을 최소 힙 진열대에 올리고 지연 폐기를 관리하는 유통기한 전담반을 만듭니다.
"""
TTL(Time To Live) 관리자 모듈
MinHeap과 자체 HashMap을 결합하여 (expire_at, key) 만료 시간을 관리하고 지연 삭제(Lazy Deletion)를 수행합니다.
dict, set, collections는 사용하지 않습니다.
"""

# [1차]: 현재 시각 측정을 위한 표준 time 모듈을 임포트합니다.
# [2차]: 매장 벽에 걸린 정확한 전자시계를 쳐다봅니다.
import time
# [1차]: 남은 시간 올림(ceil) 계산을 위한 표준 math 모듈을 임포트합니다.
# [2차]: 남은 초가 0.1초라도 있으면 1초로 계산해 주는 친절한 올림 계산기를 챙깁니다.
import math
# [1차]: 만료 시각 우선순위 관리를 위한 MinHeap 클래스를 임포트합니다.
# [2차]: 유통기한 빠른 순으로 정렬해 주는 피라미드 진열대를 가져옵니다.
from src.min_heap import MinHeap
# [1차]: 키별 최신 만료 시각 매핑을 위한 자체 HashMap 클래스를 임포트합니다.
# [2차]: 상품별 유통기한 메모 장부(해시맵)를 가져옵니다.
from src.hash_map import HashMap

'''
헷갈려 일단 익스파이어를 해쉬와 함께 보관함에 넣어뒀고
그게 self._expire_map.put(key, expire_at)코드 같아.
self._heap.push((expire_at, key))이건 키와 합께 힙으로 만들 리스트에 넣어둔거고,
 힙의 최상값을 데려와서 익파이어를 확인하고 맞으면 키값으로 해쉬에서 위치를 찾아서 
 지우는 구조 맞아?
'''
# [1차]: TTLManager 클래스를 선언합니다.
# [2차]: 유통기한 확인 및 만료 폐기를 전문으로 지휘하는 매니저입니다.
class TTLManager:
    """
    최소 힙 기반 TTL 관리자
    - _heap: MinHeap((expire_at, key)) -> O(log N) 만료 시간 우선순위 관리
    - _expire_map: HashMap(key -> expire_at) -> O(1) 만료 시간 조회 및 유효성 검증
    """
    # [1차]: TTLManager 인스턴스를 초기화하며 힙, 해시맵, 시간 제공자를 설정합니다.
    # [2차]: 진열대, 메모 장부, 전자시계를 준비합니다.
    def __init__(self, time_provider=time.time):
        # [1차]: (expire_at, key) 튜플을 저장할 MinHeap 인스턴스를 생성합니다.
        # [2차]: 유통기한 삼각김밥 피라미드 진열대를 만듭니다.
        self._heap = MinHeap()
        # [1차]: key -> expire_at 매핑을 저장할 HashMap 인스턴스를 생성합니다.
        # [2차]: 각 상품의 최신 유통기한을 기록해둘 장부를 만듭니다.
        self._expire_map = HashMap()
        # [1차]: 현재 시각을 반환하는 함수 포인터를 저장합니다 (테스트 시 가상 시간 주입 가능).
        # [2차]: 진짜 시계 또는 테스트용 연습 시계를 지정합니다.
        self._time_provider = time_provider

    # [1차]: 특정 키의 만료 시간(초)을 설정하고 힙과 맵에 기록합니다.
    # [2차]: 상품에 "지금부터 N초 뒤 폐기"라는 딱지를 붙이고 진열대에 올립니다.
    def set_ttl(self, key, seconds):
        """
        키의 만료 시간(초)을 설정합니다.
        seconds <= 0이면 즉시 만료 상태로 간주합니다.
        """
        # [1차]: 현재 시각을 구합니다.
        # [2차]: 지금 몇 시 몇 분 몇 초인지 시계를 봅니다.
        now = self._time_provider()
        # [1차]: 만료 시각 타임스탬프(now + seconds)를 계산합니다.
        # [2차]: 유통기한 만료 시각을 계산합니다.
        expire_at = now + seconds
        # [1차]: _expire_map에 key -> expire_at 매핑을 갱신합니다.
        # [2차]: 장부에 이 상품의 최신 만료 시각을 적습니다.
        self._expire_map.put(key, expire_at)
        # [1차]: 힙에 (expire_at, key) 튜플을 push합니다.
        # [2차]: 진열대 위에 이 김밥을 올리고 알맞은 층으로 정돈시킵니다.
        self._heap.push((expire_at, key))
        # [1차]: 계산된 만료 타임스탬프를 반환합니다.
        # [2차]: 정해진 만료 시각을 알려줍니다.
        return expire_at

    # [1차]: 키의 만료 시간 설정을 해제하고 맵에서 제거합니다.
    # [2차]: 상품의 유통기한 딱지를 떼어내어 평생 보관 가능한 무기한 상품으로 바꿉니다.
    def remove_ttl(self, key):
        """키의 TTL 설정을 제거합니다 (SET 덮어쓰기나 DEL 호출 시 사용)."""
        # [1차]: _expire_map에서 해당 key를 삭제합니다.
        # [2차]: 장부에서 유통기한 기록을 깨끗이 지웁니다.
        return self._expire_map.remove(key)

    # [1차]: 키의 만료 타임스탬프를 조회합니다.
    # [2차]: 이 상품의 유통기한 시각이 언제로 적혀 있는지 장부를 봅니다.
    def get_expire_at(self, key):
        """키의 만료 타임스탬프를 조회합니다 (미설정 시 None)."""
        # [1차]: _expire_map에서 만료 시각을 조회하여 반환합니다.
        # [2차]: 장부에 적힌 만료 시각을 읽어줍니다.
        return self._expire_map.get(key)

    # [1차]: 키가 만료 시각을 초과했는지 여부를 불리언 값으로 확인합니다.
    # [2차]: 지금 시각이 유통기한을 지났는지 따져보고 상했는지 판별합니다.
    def is_expired(self, key):
        """
        키가 만료되었는지 여부를 확인합니다.
        만료시간이 설정되어 있고 현재 시각 >= expire_at 이면 True를 반환합니다.
        """
        # [1차]: 해당 키의 만료 시각을 가져옵니다.
        # [2차]: 장부에서 유통기한을 찾습니다.
        expire_at = self._expire_map.get(key)
        # [1차]: 만료 시각이 설정되지 않았다면 만료되지 않은 것입니다.
        # [2차]: 유통기한 딱지가 없는 물건은 영구 보관이므로 안 상했습니다.
        if expire_at is None:
            # [1차]: False 반환
            # [2차]: 안전함 보고
            return False
        # [1차]: 현재 시각이 expire_at 이상인지 비교합니다.
        # [2차]: 지금 시계 바늘이 유통기한 시각을 넘어섰는지 봅니다.
        return self._time_provider() >= expire_at

    # [1차]: Redis TTL 명령어 규격에 맞추어 남은 초(-2, -1, N)를 계산하여 반환합니다.
    # [2차]: 손님이 "이 김밥 며칠 남았어요?" 물어봤을 때 정확한 숫자로 답해줍니다.
    def get_ttl_seconds(self, key, key_exists_in_storage):
        """
        Redis 규격에 따른 TTL 반환값:
        - key가 없으면: -2
        - key는 존재하지만 만료 시간이 없으면: -1
        - 만료 시간이 있고 아직 유효하면: 남은 초 (정수 N, math.ceil 또는 round)
        """
        # [1차]: 저장소 자체에 키가 없으면 -2를 반환합니다.
        # [2차]: 가게에 아예 없는 물건이면 -2라고 답합니다.
        if not key_exists_in_storage:
            # [1차]: -2 반환
            # [2차]: 물건 없음
            return -2

        # [1차]: 만료 시각을 맵에서 조회합니다.
        # [2차]: 장부에서 유통기한을 찾습니다.
        expire_at = self._expire_map.get(key)
        # [1차]: 만료 시각이 설정되어 있지 않은 영구 키인 경우 -1을 반환합니다.
        # [2차]: 유통기한이 없는 영구 보관 상품이면 -1이라고 답합니다.
        if expire_at is None:
            # [1차]: -1 반환
            # [2차]: 무기한 상품
            return -1

        # [1차]: 현재 시각을 구합니다.
        # [2차]: 지금 시각을 봅니다.
        now = self._time_provider()
        # [1차]: 잔여 초(expire_at - now)를 계산합니다.
        # [2차]: 유통기한까지 남은 시간을 계산합니다.
        remaining = expire_at - now
        # [1차]: 이미 시간이 지난 경우 만료(-2)로 처리합니다.
        # [2차]: 0초 이하로 이미 지난 물건은 만료(-2) 처리합니다.
        if remaining <= 0:
            # [1차]: -2 반환
            # [2차]: 이미 상함
            return -2  # 이미 만료됨
        # [1차]: 1초 미만이라도 남아있으면 최소 1 이상으로 올림하여 반환합니다.
        # [2차]: 0.5초 남았어도 올림해서 1초 남았다고 친절하게 알려줍니다.
        return max(1, math.ceil(remaining))

    # [1차]: 최소 힙의 루트를 확인하여 만료된 항목들을 능동적으로 pop하고 콜백으로 삭제합니다.
    # [2차]: 진열대 꼭대기를 보며 유통기한 지난 상품들을 차례대로 쓸어 담아 쓰레기통에 버립니다.
    def cleanup_expired(self, del_callback):
        """
        힙의 루트를 확인하여 현재 시각 기준 이미 만료된 키들을 능동적으로 정리합니다.
        유효하지 않거나 이미 갱신된 stale entry는 자동으로 버립니다.
        """
        # [1차]: 현재 시각을 측정합니다.
        # [2차]: 지금 시각을 확인합니다.
        now = self._time_provider()
        # [1차]: 힙이 빌 때까지 루트를 검사하는 루프를 실행합니다.
        # [2차]: 진열대가 빌 때까지 꼭대기 상품들을 살펴봅니다.
        while not self._heap.is_empty():
            # [1차]: 루트 요소를 제거하지 않고 peek으로 봅니다.
            # [2차]: 진열대 꼭대기 1등 상품의 유통기한을 슬쩍 봅니다.
            peek_item = self._heap.peek()
            # [1차]: None인 경우 중단합니다.
            # [2차]: 없으면 그만둡니다.
            if peek_item is None:
                # [1차]: 루프 탈출
                # [2차]: 중단
                break
            # [1차]: 튜플에서 expire_at과 key를 분해합니다.
            # [2차]: 만료 시각과 상품 이름을 분리해 봅니다.
            expire_at, key = peek_item
            # [1차]: 가장 빠른 만료 시각조차 아직 현재 시각보다 미래라면 루프를 종료합니다.
            # [2차]: 꼭대기 김밥도 아직 유통기한이 안 지났다면, 아래층 김밥들은 볼 것도 없이 전부 안전하니 청소를 끝냅니다!
            if expire_at > now:
                # [1차]: 추가 탐색 없이 즉시 종료
                # [2차]: 1초 만에 확인 완료
                break

            # [1차]: 만료 시각이 도래한 요소를 힙에서 pop합니다.
            # [2차]: 지난 상품을 진열대에서 뺍니다.
            self._heap.pop()

            # [1차]: 해당 키의 최신 expire_at이 현재 튜플의 expire_at과 일치하는지 유효성을 검증합니다.
            # [2차]: 장부를 펼쳐 이 상품이 그사이 새 유통기한으로 갱신된 건 아닌지 확인합니다.
            current_expire_at = self._expire_map.get(key)
            # [1차]: 일치하는 경우에만 실제 만료 삭제를 수행합니다 (stale entry 방어).
            # [2차]: 진짜 상한 물건이 맞다면 장부에서 지우고 쓰레기통에 버려달라고 부탁합니다.
            if current_expire_at is not None and current_expire_at == expire_at:
                # [1차]: 장부에서 키를 제거합니다.
                # [2차]: 장부에서 지웁니다.
                self._expire_map.remove(key)
                # [1차]: del_callback을 호출하여 저장소와 메모리에서 키를 완전 삭제합니다.
                # [2차]: "이 김밥 만료됐으니 매장에서 싹 치워주세요" 하고 폐기 처리합니다.
                del_callback(key, is_expired=True)
