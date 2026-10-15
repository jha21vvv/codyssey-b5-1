"""
메모리 관리자 (Memory Manager) 모듈
used_memory(UTF-8 바이트 총합)와 maxmemory 한도를 추적하고,
메모리 한도 초과 시 LRU 정책에 따라 키를 자동 방출(Eviction)합니다.
"""

class MemoryManager:
    """
    메모리 관리 및 한도 검사 클래스
    - used_memory: Σ(len(utf8(key)) + len(utf8(value)))
    - maxmemory: 0은 무제한, 양수는 바이트 단위 제한
    - evicted_keys: 메모리 초과로 인해 제거된 키의 누적 개수
    """
    def __init__(self, maxmemory=0):
        self._maxmemory = maxmemory
        self._used_memory = 0
        self._evicted_keys = 0

    @staticmethod
    def calc_entry_size(key, value):
        """키와 값의 UTF-8 바이트 크기 합산 계산"""
        key_bytes = str(key).encode("utf-8")
        val_bytes = str(value).encode("utf-8")
        return len(key_bytes) + len(val_bytes)

    @property
    def maxmemory(self):
        return self._maxmemory

    @maxmemory.setter
    def maxmemory(self, value):
        self._maxmemory = max(0, int(value))

    @property
    def used_memory(self):
        return self._used_memory

    @property
    def evicted_keys(self):
        return self._evicted_keys

    def is_single_entry_oom(self, key, value):
        """
        단일 엔트리 자체의 크기가 maxmemory를 초과하는지 검사합니다.
        maxmemory > 0이고 단일 크기 > maxmemory이면 True (저장 불가 OOM)
        """
        if self._maxmemory <= 0:
            return False
        entry_size = self.calc_entry_size(key, value)
        return entry_size > self._maxmemory

    def add_entry_memory(self, key, value):
        """새 엔트리 추가 시 메모리 사용량 증가"""
        self._used_memory += self.calc_entry_size(key, value)

    def update_entry_memory(self, key, old_value, new_value):
        """기존 엔트리 갱신 시 값 차이만큼 메모리 사용량 반영"""
        old_val_size = len(str(old_value).encode("utf-8"))
        new_val_size = len(str(new_value).encode("utf-8"))
        self._used_memory += (new_val_size - old_val_size)

    def remove_entry_memory(self, key, value):
        """엔트리 삭제 시 메모리 사용량 차감"""
        size = self.calc_entry_size(key, value)
        self._used_memory = max(0, self._used_memory - size)

    def evict_if_needed(self, lru_manager, del_callback):
        """
        maxmemory > 0이고 used_memory > maxmemory인 경우,
        used_memory <= maxmemory가 될 때까지 LRU 키를 방출합니다.
        del_callback(key)은 주 저장소 및 TTL 등에서 해당 키를 완전 정리하는 콜백입니다.
        """
        if self._maxmemory <= 0:
            return

        while self._used_memory > self._maxmemory:
            lru_key = lru_manager.pop_lru()
            if lru_key is None:
                break
            
            del_callback(lru_key, is_eviction=True)
            self._evicted_keys += 1

    def get_info_memory(self):
        """INFO memory 명령어용 출력 문자열 생성"""
        return f"used_memory:{self._used_memory}\nmaxmemory:{self._maxmemory}\nevicted_keys:{self._evicted_keys}"
