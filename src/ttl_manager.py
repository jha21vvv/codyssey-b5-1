"""
TTL(Time To Live) 관리자 모듈
MinHeap과 자체 HashMap을 결합하여 (expire_at, key) 만료 시간을 관리하고 지연 삭제(Lazy Deletion)를 수행합니다.
dict, set, collections는 사용하지 않습니다.
"""

import time
import math
from src.min_heap import MinHeap
from src.hash_map import HashMap

'''
헷갈려 일단 익스파이어를 해쉬와 함께 보관함에 넣어뒀고
그게 self._expire_map.put(key, expire_at)코드 같아.
self._heap.push((expire_at, key))이건 키와 합께 힙으로 만들 리스트에 넣어둔거고,
 힙의 최상값을 데려와서 익파이어를 확인하고 맞으면 키값으로 해쉬에서 위치를 찾아서 
 지우는 구조 맞아?
'''
class TTLManager:
    """
    최소 힙 기반 TTL 관리자
    - _heap: MinHeap((expire_at, key)) -> O(log N) 만료 시간 우선순위 관리
    - _expire_map: HashMap(key -> expire_at) -> O(1) 만료 시간 조회 및 유효성 검증
    """
    def __init__(self, time_provider=time.time):
        self._heap = MinHeap()
        self._expire_map = HashMap()
        self._time_provider = time_provider

    def set_ttl(self, key, seconds):
        """
        키의 만료 시간(초)을 설정합니다.
        seconds <= 0이면 즉시 만료 상태로 간주합니다.
        """
        now = self._time_provider()
        expire_at = now + seconds
        self._expire_map.put(key, expire_at)
        self._heap.push((expire_at, key))
        return expire_at

    def remove_ttl(self, key):
        """키의 TTL 설정을 제거합니다 (SET 덮어쓰기나 DEL 호출 시 사용)."""
        return self._expire_map.remove(key)

    def get_expire_at(self, key):
        """키의 만료 타임스탬프를 조회합니다 (미설정 시 None)."""
        return self._expire_map.get(key)

    def is_expired(self, key):
        """
        키가 만료되었는지 여부를 확인합니다.
        만료시간이 설정되어 있고 현재 시각 >= expire_at 이면 True를 반환합니다.
        """
        expire_at = self._expire_map.get(key)
        if expire_at is None:
            return False
        return self._time_provider() >= expire_at

    def get_ttl_seconds(self, key, key_exists_in_storage):
        """
        Redis 규격에 따른 TTL 반환값:
        - key가 없으면: -2
        - key는 존재하지만 만료 시간이 없으면: -1
        - 만료 시간이 있고 아직 유효하면: 남은 초 (정수 N, math.ceil 또는 round)
        """
        if not key_exists_in_storage:
            return -2

        expire_at = self._expire_map.get(key)
        if expire_at is None:
            return -1

        now = self._time_provider()
        remaining = expire_at - now
        if remaining <= 0:
            return -2
        return max(1, math.ceil(remaining))

    def cleanup_expired(self, del_callback):
        """
        힙의 루트를 확인하여 현재 시각 기준 이미 만료된 키들을 능동적으로 정리합니다.
        유효하지 않거나 이미 갱신된 stale entry는 자동으로 버립니다.
        """
        now = self._time_provider()
        while not self._heap.is_empty():
            peek_item = self._heap.peek()
            if peek_item is None:
                break
            expire_at, key = peek_item
            if expire_at > now:
                break

            self._heap.pop()

            current_expire_at = self._expire_map.get(key)
            if current_expire_at is not None and current_expire_at == expire_at:
                self._expire_map.remove(key)
                del_callback(key, is_expired=True)
