# 📋 Mini Redis 아키텍처 및 개발 계획서 (PLAN.md)

## 1. 프로젝트 개요
- **프로젝트명**: Mini Redis (Zero Built-in Collections In-Memory Key-Value Store)
- **목표**: Python의 내장 컬렉션(`dict`, `set`, `collections`)을 일절 사용하지 않고, 오직 밑바닥(From Scratch)부터 직접 구현한 **이중 연결 리스트(Doubly Linked List)**, **체이닝 해시맵(Chaining Hash Map)**, **최소 힙(Min Heap)**을 결합하여 Redis의 핵심 명령어, O(1) LRU 메모리 방출(Eviction), 힙 기반 TTL 만료 시스템, REPL CLI를 완성한다.
- **제약 조건**:
  - Python 3.8+ 환경
  - `dict`, `set`, `collections` 등 내장 키-값/집합 자료구조 사용 엄격 금지 (버킷 인덱싱용 기본 고정 리스트 `[None] * N` 및 힙용 dynamic array `list` 인덱스 접근만 허용)
  - 네트워크 통신, 멀티스레딩 락, 디스크 영속성 배제 (순수 In-Memory 단일 스레드 REPL)
  - Redis 표준 응답 포맷 준수 (`OK`, `(nil)`, `(integer) N`, `(error) ...`)

---

## 2. 핵심 자료구조 및 모듈 설계

```text
[ CLI REPL (cli.py) ]
         │ (shlex parsing)
         ▼
[ MiniRedis Engine (mini_redis.py) ]
  ├── [ HashMap (hash_map.py) ] ─────── Primary Storage (Key -> Value)
  ├── [ LRU Manager (lru_cache.py) ] ── DoublyLinkedList + HashMap(Key -> Node)
  ├── [ TTL Manager (ttl_manager.py) ] ─ MinHeap((expire_at, key)) + HashMap(Key -> expire_at)
  └── [ Memory Manager (memory_manager.py) ] ─ used_memory (Σ UTF-8 bytes) & maxmemory eviction
```

### 2.1. 이중 연결 리스트 (`src/doubly_linked_list.py`)
- **노드 구조**: `Node(key, value, prev=None, next=None)`
- **센티넬 노드(Dummy Head & Tail)** 도입: 빈 리스트 경계 처리 간소화 및 O(1) 안전성 확보.
- **핵심 메서드**:
  - `insert_front(node)` / `insert_back(node)`: O(1)
  - `remove_front()` / `remove_back()`: O(1)
  - `remove_node(node)`: O(1) 특정 노드 즉시 분리
  - `move_to_front(node)`: O(1) 기존 위치에서 분리 후 head 바로 뒤로 이동 (LRU 갱신용)
  - `size()`: O(1) 노드 수 반환

### 2.2. 체이닝 해시맵 (`src/hash_map.py`)
- **버킷 배열**: 기본 크기 16의 `list` (각 버킷은 `DoublyLinkedList` 또는 충돌 체이닝 노드 연결)
- **자체 해시 함수**: Polynomial Rolling Hash (소수 베이스 31 및 대형 모듈러 적용)
  ```python
  # hash = (hash * 31 + ord(char)) % capacity
  ```
- **로드 팩터 및 리사이징**:
  - `load_factor = size / capacity`
  - `load_factor > 0.75` 도달 시 버킷 크기 2배 확장(`capacity * 2`) 및 전체 키-값 재해싱(Rehashing)
- **핵심 메서드**:
  - `put(key, value)`: 키 삽입 또는 기존 값 갱신
  - `get(key)`: 키 조회 (미존재 시 None 반환)
  - `remove(key)`: 키 삭제 (삭제된 값 반환, 없으면 None)
  - `contains(key)`: 키 존재 여부 (True/False)
  - `keys()`: 전체 키 목록 반환 (리스트)
  - `size()`: 현재 저장된 고유 키의 개수 반환

### 2.3. 최소 힙 (`src/min_heap.py`)
- **요소 규격**: `(expire_at, key)` 튜플
- **구조**: 0-인덱스 기반 완전 이진 트리 (`list` 활용)
  - 부모 노드: `(i - 1) // 2`
  - 좌측 자식: `2 * i + 1`, 우측 자식: `2 * i + 2`
- **핵심 메서드**:
  - `push(item)`: 맨 뒤 삽입 후 `_heapify_up` (O(log N))
  - `pop()`: 루트 추출 후 맨 뒤 요소를 루트로 올리고 `_heapify_down` (O(log N))
  - `peek()`: 최솟값(가장 빠른 만료 항목) O(1) 확인
  - `size()`: O(1)

### 2.4. 메모리 관리 및 LRU 방출 (`src/memory_manager.py`, `src/lru_cache.py`)
- **used_memory 계산**:
  $$\text{used\_memory} = \sum (\text{len}(\text{utf8}(key)) + \text{len}(\text{utf8}(value)))$$
- **방출(Eviction) 알고리즘**:
  1. `SET key value` 실행 전/후 `maxmemory > 0` 검사
  2. 단일 엔트리 자체의 크기(`len(utf8(k)) + len(utf8(v))`)가 `maxmemory`보다 크면 `OOM` 에러 발생 및 저장 거부
  3. 새 엔트리 추가/갱신 시 `used_memory > maxmemory`이면, `used_memory <= maxmemory`가 될 때까지 LRU 리스트의 tail(가장 오래 접근되지 않은 노드)을 지속 방출
  4. 방출 시 `evicted_keys` 카운터 증가 및 주 저장소(HashMap), TTL 힙에서도 완전 제거

### 2.5. TTL 관리자 (`src/ttl_manager.py`)
- **지연 삭제(Lazy Deletion) & 사전 만료 체크**:
  - 키에 접근(`GET`, `EXISTS`, `TTL` 등)할 때마다 만료 타임스탬프(`current_time >= expire_at`)를 확인하여 만료되었으면 즉시 삭제하고 `(nil)` 처리
  - 능동적 만료 청소: `cleanup_expired(now)`를 통해 힙 루트를 확인하여 이미 지난 키들을 일괄 제거
  - 힙에는 과거 만료 시간 엔트리가 남아있을 수 있으므로 (동일 키에 재설정된 경우 등), HashMap에 최신 `expire_at`을 기록해두고 힙 pop 시 버전/시각이 불일치하면 스킵(Lazy Invalidation)

### 2.6. MiniRedis 엔진 & CLI REPL (`src/mini_redis.py`, `src/cli.py`)
- **명령어 집합**:
  - `SET key value`: 저장, LRU 헤드로 이동, 기존 TTL 초기화, 메모리 초과 시 방출
  - `GET key`: 만료 검사 -> 값 조회 -> LRU 헤드로 이동 -> `"value"` 반환
  - `DEL key`: 주 저장소, LRU, TTL에서 동시 제거 -> `(integer) 1` or `(integer) 0`
  - `EXISTS key`: 만료 검사 -> 존재 여부 반환
  - `DBSIZE`: 만료 정리 후 총 키 수 반환
  - `KEYS`: 모든 활성 키 목록 출력
  - `CONFIG SET maxmemory <bytes>`: 메모리 상한선 설정 (0=무제한)
  - `INFO memory`: `used_memory:<n> maxmemory:<n> evicted_keys:<n>` 출력
  - `EXPIRE key <seconds>`: 만료 초 설정
  - `TTL key`: 잔여 초 반환 (-2: 없음, -1: 무제한, N: 잔여 초)
  - `exit`, `quit`: CLI 종료
- **에러 규격**:
  - Unknown command: `(error) ERR unknown command '<cmd>'`
  - Wrong number of arguments: `(error) ERR wrong number of arguments for '<cmd>' command`
  - Not an integer: `(error) ERR value is not an integer or out of range`
  - OOM: `(error) OOM command not allowed when used_memory > 'maxmemory'`

---

## 3. 7단계 워크플로우 진행 로드맵

| 단계 | 작업 내용 | 세부 산출물 |
| :--- | :--- | :--- |
| **Step 1: PLAN** | 과제 요구사항 분석 및 아키텍처/자료구조 계획 수립 | `PLAN.md` |
| **Step 2: BUILD** | 내장 dict/set 제약 준수한 3대 자료구조 및 Redis 엔진 구현 | `src/doubly_linked_list.py`, `src/hash_map.py`, `src/min_heap.py`, `src/lru_cache.py`, `src/memory_manager.py`, `src/ttl_manager.py`, `src/mini_redis.py`, `src/cli.py`, `main.py` |
| **Step 3: TEST AUTOMATION** | 0.1초 이내 초고속 단위 테스트 및 무결성 100% 검증 | `tests/test_doubly_linked_list.py`, `tests/test_hash_map.py`, `tests/test_min_heap.py`, `tests/test_mini_redis.py` |
| **Step 4: AUDIT & DIAGRAMS** | 원본 요구사항 100% 대조, 주니어 일상 비유 설명, matplotlib 아키텍처 다이어그램 생성 | `스터디.md`, `scripts/generate_diagrams_matplotlib.py`, `diagrams/*.png` (4개 이미지) |
| **Step 5: REFINE & REPORT** | 엣지 케이스 방어(UTF-8, 타이 브레이킹, shlex 따옴표, 음수 TTL) & 세부 엔지니어링 리포트 | `REPORT.md` |
| **Step 6: NOTEBOOKLM** | 순수 소스 코드 단일 텍스트화, 자동 빌더 스크립트, 팟캐스트 기획서 | `NOTEBOOKLM_FULL_SOURCE.txt`, `scripts/build_notebooklm_source.py`, `NOTEBOOKLM_GUIDE.md` |
| **Step 7: 2-TIER COMMENTS** | 전 소스 코드 라인마다 [1차 기술/문법] + [2차 주니어 일상 비유] 2단 주석 내재화 | `src/*.py`, `main.py` 전체 소스 코드 100% 보존 주석화 |
