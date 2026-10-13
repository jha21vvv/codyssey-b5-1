# 📑 Mini Redis 세부 엔지니어링 리포트 (REPORT.md)

---

## 1. 아키텍처 의사결정 및 자료구조 선정 분석

### 1.1. In-Memory Key-Value 저장소의 병목과 해결책
Redis가 수십만 QPS(Queries Per Second)를 달성하는 비결은 **단일 스레드 이벤트 루프**와 **자료구조의 극단적 최적화**에 있습니다. 본 프로젝트에서는 Python의 고수준 내장 컬렉션(`dict`, `set`, `collections`)을 일절 배제하고 C언어로 작성된 Redis의 내부 자료구조 원형을 파이썬 코드로 재현했습니다.

### 1.2. 핵심 자료구조 복잡도 및 선정 근거

| 컴포넌트 | 선택 자료구조 | 시간 복잡도 (평균 / 최악) | 공간 복잡도 | 선정 근거 및 기술적 트레이드오프 |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Storage** | **Chaining HashMap** | $O(1) / O(N)$ | $O(N)$ | 충돌 회피를 위해 djb2 고분산 해시를 적용하고, 로드 팩터 0.75 도달 시 2배 리사이징을 통해 최악의 충돌 체인 형성을 사전에 차단함. |
| **LRU Tracking** | **Doubly Linked List + HashMap** | $O(1) / O(1)$ | $O(N)$ | 단일 연결 리스트는 이전 노드 탐색에 $O(N)$이 걸리지만, 양방향 포인터와 더미 헤드/테일을 도입하여 노드 분리 및 재배치를 엄격한 $O(1)$ 원자적 연산으로 수행. |
| **TTL Engine** | **Binary Min-Heap** | Peek: $O(1)$<br>Push/Pop: $O(\log N)$ | $O(N)$ | 수만 개의 키가 각각 다른 만료 시각을 가질 때 전체 키를 선형 탐색($O(N)$)하는 것은 불가능함. 루트에 언제나 가장 빠른 만료 시각이 위치하므로 $O(1)$만에 검사 가능. |
| **Memory Accounting** | **Byte Counter** | $O(1) / O(1)$ | $O(1)$ | 모든 키/값의 UTF-8 인코딩 길이를 실시간 가산/감산하여 $O(N)$ 집계 루프 없이 $O(1)$ 메모리 상한선 검사 달성. |

---

## 2. 테스트 자동화 결과 및 성능 벤치마크

### 2.1. 테스트 수행 지표
- **테스트 러너**: Python 표준 `unittest`
- **테스트 케이스 수**: 총 28개 (자료구조 단위 17개 + 통합/시나리오 11개)
- **테스트 통과율**: **100% (28/28 PASS)**
- **소요 시간**: **0.006초 (6 밀리초)**

```text
Ran 28 tests in 0.006s

OK
```

### 2.2. 무결성 검증 포인트
1. **Zero External Dependency**: 외부 네트워크 호출, API 요청, C-extension 의존성 0%
2. **Deterministic Time Mocking**: `MockTime` 주입을 통해 `time.sleep()` 없이 밀리초 단위 시간 경과 및 만료를 결정론적으로 0.001초 만에 검증
3. **Large-scale Stress Test**: 100건 대량 키 삽입 및 리사이징, 다중 체이닝 무결성 통과

---

## 3. 엣지 케이스(Edge Cases) 발견 및 엔지니어링 방어 전략

### 3.1. Windows 콘솔 UTF-8 한글 인코딩 및 메모리 바이트 정밀 계산
- **문제점**: Windows 콘솔 환경(cp949) 및 파이썬 `len("홍길동")`은 문자 단위 길이인 `3`을 반환합니다. 그러나 Redis 스펙은 바이트 단위(`used_memory = Σ len(utf8(k)) + len(utf8(v))`)를 요구합니다.
- **해결책**:
  ```python
  @staticmethod
  def calc_entry_size(key, value):
      key_bytes = str(key).encode("utf-8")
      val_bytes = str(value).encode("utf-8")
      return len(key_bytes) + len(val_bytes)
  ```
  `홍길동`을 UTF-8로 인코딩하여 정확히 9바이트로 산정함으로써 한글 및 멀티바이트 유니코드 환경에서도 규격과 100% 일치하도록 방어했습니다.

### 3.2. 부동소수점 타임스탬프 동률 시 최소 힙 타이브레이킹(Tie-breaking)
- **문제점**: 여러 키에 대해 동일한 만료 시각(`expire_at`)이 부여될 경우, 파이썬 튜플 `(expire_at, key)` 비교 시 튜플의 두 번째 인자인 `key` 문자열의 사전순으로 비교가 전이됩니다. 만약 `key`가 객체이거나 비교 불가 타입이면 TypeError가 발생할 수 있습니다.
- **해결책**: `MinHeap`에 푸시되는 튜플의 두 번째 요소가 항상 정규화된 `str(key)`를 유지하도록 보장하여 동률 타임스탬프 상황에서도 결정론적이고 안정적인(Stable) 비교 순서를 확립했습니다.

### 3.3. 공백 및 따옴표를 포함한 값 파싱 방어 (`shlex`)
- **문제점**: `SET msg "Hello Redis World"`를 단순 `line.split()`으로 분리하면 `['SET', 'msg', '"Hello', 'Redis', 'World"']`로 쪼개져 `wrong number of arguments` 에러가 발생합니다.
- **해결책**: `shlex.split(line)`을 적용하여 따옴표 내부의 공백을 문자열 값 하나로 완벽히 보존하고, 따옴표가 닫히지 않은 비정상 입력 시 안전하게 일반 split으로 폴백 처리했습니다.

### 3.4. 센티넬(더미 헤드/더미 테일) 노드를 통한 리스트 언더플로우 방어
- **문제점**: 일반 연결 리스트는 노드가 0개이거나 1개일 때 `head == None` 또는 `tail == None` 분기가 복잡해져 O(1) 이동 시 Null 참조 버그가 빈번합니다.
- **해결책**:
  ```python
  self.head = Node()
  self.tail = Node()
  self.head.next = self.tail
  self.tail.prev = self.head
  ```
  센티넬 노드를 고정 배치하여 리스트가 비어있어도 헤드와 테일이 항상 존재하도록 설계했습니다. 이를 통해 모든 삽입, 삭제, 맨 앞 이동(`move_to_front`) 연산이 단 한 줄의 `if-else` 분기 없이 완전한 원자적 4-포인터 교체로 동작합니다.

### 3.5. 덮어쓰기(`SET`) 시 과거 TTL 잔재 및 Stale Heap Invalidation 방어
- **문제점**: 이미 만료 시간이 걸려있는 키에 대해 새 값으로 `SET`을 호출하면 기존 만료 시간은 무효화되어야 합니다. 또한 힙 내부에는 이미 들어가 있는 과거 `(old_expire_at, key)` 튜플을 $O(1)$로 임의 삭제하기 어렵습니다 ($O(N)$ 탐색 필요).
- **해결책**: **Lazy Invalidation(지연 무효화)** 기법을 도입했습니다.
  - `SET` 덮어쓰기 시 자체 `_expire_map`에서 해당 키의 만료 기록을 즉시 제거합니다.
  - 추후 힙에서 과거 튜플이 pop될 때, 현재 `_expire_map`에 기록된 만료 타임스탬프와 대조하여 일치하지 않으면 아무런 작업도 하지 않고 버립니다(Discard Stale Entry).
  - 이를 통해 힙의 복잡도를 $O(N)$으로 떨어뜨리지 않고 $O(\log N)$을 유지하면서도 완벽한 만료 정합성을 달성했습니다.

### 3.6. 단일 엔트리 자체의 OOM 사전 차단
- **문제점**: `maxmemory`가 10바이트인데 20바이트 크기의 엔트리가 들어오면, 기존의 모든 키를 방출하더라도 메모리 한도를 만족할 수 없습니다.
- **해결책**: 삽입 연산 착수 전 `MemoryManager.is_single_entry_oom(key, value)`를 우선 평가하여, 단일 엔트리가 한도를 초과하면 기존 데이터를 단 1바이트도 건드리지 않고 즉시 `(error) OOM command not allowed when used_memory > 'maxmemory'`를 반환하도록 보호했습니다.

---

## 4. 결론 및 학습 성과
본 구현을 통해 Redis가 단순한 Key-Value 저장소를 넘어 왜 "자료구조 서버(Data Structure Server)"로 불리는지, 내장 라이브러리에 기대지 않고 순수 포인터와 배열 인덱스만으로 고성능 캐시 시스템을 구축하는 표준 패턴을 완벽히 입증했습니다.
