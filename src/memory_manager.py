# [1차]: 메모리 관리자(Memory Manager) 모듈을 정의합니다.
# [2차]: 책가방의 허용 무게(바이트 용량)를 재고, 가방이 터지려고 하면 책을 버려주는 스마트 저울을 만듭니다.
"""
메모리 관리자 (Memory Manager) 모듈
used_memory(UTF-8 바이트 총합)와 maxmemory 한도를 추적하고,
메모리 한도 초과 시 LRU 정책에 따라 키를 자동 방출(Eviction)합니다.
"""

# [1차]: MemoryManager 클래스를 선언합니다.
# [2차]: 매 순간 메모리 사용량을 바이트 단위로 달아보는 저울 관리인입니다.
class MemoryManager:
    """
    메모리 관리 및 한도 검사 클래스
    - used_memory: Σ(len(utf8(key)) + len(utf8(value)))
    - maxmemory: 0은 무제한, 양수는 바이트 단위 제한
    - evicted_keys: 메모리 초과로 인해 제거된 키의 누적 개수
    """
    # [1차]: MemoryManager 인스턴스를 초기화하며 maxmemory를 설정합니다.
    # [2차]: 가방의 최대 허용 무게를 입력받고 저울 바늘을 0으로 맞춥니다.
    def __init__(self, maxmemory=0):
        # [1차]: 최대 메모리 제한(바이트)을 인스턴스 변수에 저장합니다 (0: 무제한).
        # [2차]: 최대 무게 한도를 적어둡니다 (0이면 얼마든지 담아도 됨).
        self._maxmemory = maxmemory
        # [1차]: 현재 사용 중인 총 UTF-8 바이트 수를 0으로 초기화합니다.
        # [2차]: 현재 가방에 담긴 총 무게를 0g으로 시작합니다.
        self._used_memory = 0
        # [1차]: 메모리 초과로 강제 방출(evict)된 누적 키 개수를 0으로 초기화합니다.
        # [2차]: 지금까지 가방이 무거워서 밖으로 던져버린 책의 총 권수를 0권으로 잡습니다.
        self._evicted_keys = 0

    # [1차]: 키와 값의 문자열을 UTF-8 바이트로 인코딩한 길이의 합을 계산하는 정적 메서드입니다.
    # [2차]: 물건과 이름표를 전자저울에 올려 총 몇 g(바이트)인지 무게를 측정합니다.
    @staticmethod
    def calc_entry_size(key, value):
        """키와 값의 UTF-8 바이트 크기 합산 계산"""
        # [1차]: key를 문자열로 변환한 후 UTF-8 바이트 배열로 인코딩합니다.
        # [2차]: 이름표를 포장해서 무게를 잽니다.
        key_bytes = str(key).encode("utf-8")
        # [1차]: value를 문자열로 변환한 후 UTF-8 바이트 배열로 인코딩합니다.
        # [2차]: 내용물을 포장해서 무게를 잽니다.
        val_bytes = str(value).encode("utf-8")
        # [1차]: 키 바이트 수와 값 바이트 수의 합을 반환합니다.
        # [2차]: 둘의 무게를 합친 총 무게를 알려줍니다.
        return len(key_bytes) + len(val_bytes)

    # [1차]: maxmemory 속성의 getter 메서드입니다.
    # [2차]: 현재 가방의 무게 제한이 몇 g인지 물어봅니다.
    @property
    def maxmemory(self):
        # [1차]: _maxmemory 값을 반환합니다.
        # [2차]: 한도 무게를 말해줍니다.
        return self._maxmemory

    # [1차]: maxmemory 속성의 setter 메서드로 0 이상의 정수만 안전하게 할당합니다.
    # [2차]: 가방의 무게 한도를 새 값으로 조절합니다 (음수는 0으로 보정).
    @maxmemory.setter
    def maxmemory(self, value):
        # [1차]: 정수형으로 변환 후 0 이상의 값으로 클램핑합니다.
        # [2차]: 음수가 들어오지 못하게 0으로 딱 막아줍니다.
        self._maxmemory = max(0, int(value))

    # [1차]: used_memory 속성의 getter 메서드입니다.
    # [2차]: 현재 가방이 총 몇 g인지 저울 눈금을 읽습니다.
    @property
    def used_memory(self):
        # [1차]: _used_memory 값을 반환합니다.
        # [2차]: 현재 사용 중인 바이트 무게를 알려줍니다.
        return self._used_memory

    # [1차]: evicted_keys 속성의 getter 메서드입니다.
    # [2차]: 쫓겨난 책이 지금까지 총 몇 권인지 물어봅니다.
    @property
    def evicted_keys(self):
        # [1차]: _evicted_keys 값을 반환합니다.
        # [2차]: 쫓겨난 책 권수를 말해줍니다.
        return self._evicted_keys

    # [1차]: 단일 엔트리 자체의 크기가 maxmemory를 초과하는지 OOM 여부를 판별합니다.
    # [2차]: 책 한 권의 무게가 가방 전체 한도보다 더 무거워서 아예 안 들어가는지 검사합니다.
    def is_single_entry_oom(self, key, value):
        """
        단일 엔트리 자체의 크기가 maxmemory를 초과하는지 검사합니다.
        maxmemory > 0이고 단일 크기 > maxmemory이면 True (저장 불가 OOM)
        """
        # [1차]: maxmemory가 0 이하이면 무제한이므로 OOM이 발생하지 않습니다.
        # [2차]: 가방 크기가 무제한이면 어떤 거대한 책이 와도 다 들어갑니다.
        if self._maxmemory <= 0:
            # [1차]: False 반환
            # [2차]: 문제없음 보고
            return False
        # [1차]: 키와 값의 크기를 바이트 단위로 계산합니다.
        # [2차]: 이번 책 한 권의 무게를 잽니다.
        entry_size = self.calc_entry_size(key, value)
        # [1차]: 엔트리 크기가 maxmemory보다 크면 True를 반환합니다.
        # [2차]: 책 한 권 무게가 가방 전체 한도를 넘으면 가방 터짐(True)을 알립니다.
        return entry_size > self._maxmemory

    # [1차]: 새 엔트리가 추가될 때 used_memory를 증가시킵니다.
    # [2차]: 새 책을 가방에 넣었으니 그만큼 저울 눈금을 올립니다.
    def add_entry_memory(self, key, value):
        """새 엔트리 추가 시 메모리 사용량 증가"""
        # [1차]: 새 엔트리의 UTF-8 바이트 크기를 used_memory에 가산합니다.
        # [2차]: 저울 무게에 새 책 무게를 더합니다.
        self._used_memory += self.calc_entry_size(key, value)

    # [1차]: 기존 엔트리가 덮어쓰여질 때 값의 바이트 차이만큼 used_memory를 보정합니다.
    # [2차]: 책 속의 얇은 페이지를 두꺼운 새 페이지로 교체했을 때 무게 차이만큼 저울을 조정합니다.
    def update_entry_memory(self, key, old_value, new_value):
        """기존 엔트리 갱신 시 값 차이만큼 메모리 사용량 반영"""
        # [1차]: 기존 값의 UTF-8 바이트 길이를 계산합니다.
        # [2차]: 옛날 페이지 무게를 잽니다.
        old_val_size = len(str(old_value).encode("utf-8"))
        # [1차]: 새 값의 UTF-8 바이트 길이를 계산합니다.
        # [2차]: 새 페이지 무게를 잽니다.
        new_val_size = len(str(new_value).encode("utf-8"))
        # [1차]: (새 크기 - 기존 크기) 차이만큼 used_memory에 반영합니다.
        # [2차]: 무게 차이만큼 저울 눈금을 올려주거나 내려줍니다.
        self._used_memory += (new_val_size - old_val_size)

    # [1차]: 엔트리가 삭제될 때 used_memory를 차감합니다.
    # [2차]: 책을 가방에서 뺐으니 그만큼 저울 눈금을 내립니다.
    def remove_entry_memory(self, key, value):
        """엔트리 삭제 시 메모리 사용량 차감"""
        # [1차]: 삭제 대상의 바이트 크기를 계산합니다.
        # [2차]: 꺼낸 책의 무게를 잽니다.
        size = self.calc_entry_size(key, value)
        # [1차]: used_memory에서 차감하며 음수가 되지 않도록 max(0, ...) 처리합니다.
        # [2차]: 무게를 빼되, 저울이 마이너스가 되지 않도록 0에서 딱 멈춥니다.
        self._used_memory = max(0, self._used_memory - size)

    # [1차]: maxmemory 한도 초과 시 한도 이하가 될 때까지 LRU 키를 지속 방출합니다.
    # [2차]: 가방이 터질 때까지 차오르면, 가방 무게가 정상 범위가 될 때까지 가장 오래 안 본 책부터 밖으로 던집니다.
    def evict_if_needed(self, lru_manager, del_callback):
        """
        maxmemory > 0이고 used_memory > maxmemory인 경우,
        used_memory <= maxmemory가 될 때까지 LRU 키를 방출합니다.
        del_callback(key)은 주 저장소 및 TTL 등에서 해당 키를 완전 정리하는 콜백입니다.
        """
        # [1차]: maxmemory가 0 이하이면 무제한이므로 방출 루프를 수행하지 않습니다.
        # [2차]: 가방 용량이 무제한이면 책을 버릴 필요가 없습니다.
        if self._maxmemory <= 0:
            # [1차]: 함수를 즉시 종료합니다.
            # [2차]: 그대로 둡니다.
            return

        # [1차]: used_memory가 maxmemory를 초과하는 동안 반복 실행합니다.
        # [2차]: 가방 무게가 한도 무게보다 무거운 동안 계속 반복합니다.
        while self._used_memory > self._maxmemory:
            # [1차]: LRUManager에서 가장 오래된 키를 O(1)으로 pop합니다.
            # [2차]: 책꽂이 맨 밑바닥에서 가장 오래 안 읽은 책을 1권 꺼냅니다.
            lru_key = lru_manager.pop_lru()
            # [1차]: 더 이상 방출할 키가 없으면 루프를 탈출합니다.
            # [2차]: 더 이상 꺼낼 책이 없으면 멈춥니다.
            if lru_key is None:
                # [1차]: break로 반복문 탈출
                # [2차]: 루프 종료
                break
            
            # [1차]: 콜백을 호출하여 저장소, TTL, 메모리에서 해당 키를 일괄 정리합니다.
            # [2차]: 집주인에게 "이 책 버려주세요" 하고 방출 처리를 맡깁니다.
            del_callback(lru_key, is_eviction=True)
            # [1차]: 방출된 키 카운터를 1 증가시킵니다.
            # [2차]: 쫓겨난 책 권수 카운터를 1 올립니다.
            self._evicted_keys += 1

    # [1차]: INFO memory 명령어 요구 규격에 맞추어 포맷팅된 문자열을 반환합니다.
    # [2차]: 현재 가방 상태(사용 무게, 한도 무게, 버린 책 수)를 깔끔한 영수증으로 뽑아줍니다.
    def get_info_memory(self):
        """INFO memory 명령어용 출력 문자열 생성"""
        # [1차]: used_memory, maxmemory, evicted_keys 세 항목을 개행 문자로 연결하여 반환합니다.
        # [2차]: 3대 핵심 메모리 지표를 알기 쉽게 세 줄로 적어줍니다.
        return f"used_memory:{self._used_memory}\nmaxmemory:{self._maxmemory}\nevicted_keys:{self._evicted_keys}"
