# 🚀 Mini Redis (From Scratch Key-Value Store)

> Python 내장 컬렉션(`dict`, `set`, `collections`)을 일절 사용하지 않고, 오직 밑바닥부터 구현한 **이중 연결 리스트**, **체이닝 해시맵**, **최소 힙**으로 완성한 고성능 인메모리 Redis 엔진 및 CLI.

![System Architecture](diagrams/01_system_architecture.png)

---

## 📌 주요 특징
1. **Zero Built-in Collections**: `dict`, `set`, `OrderedDict` 없이 순수 자료구조로 구현.
2. **O(1) LRU Eviction**: DoublyLinkedList와 자체 HashMap을 결합하여 메모리 한도 초과 시 $O(1)$ 방출.
3. **MinHeap 기반 TTL**: 최소 힙을 통해 유효기간이 가장 임박한 키를 $O(1)$ 확인 및 지연 삭제(Lazy Deletion) 수행.
4. **UTF-8 메모리 회계**: $\sum (\text{len}(\text{utf8}(k)) + \text{len}(\text{utf8}(v)))$ 바이트 단위 정밀 제어 및 단일 엔트리 OOM 방어.
5. **Redis 호환 CLI**: `mini-redis>` 프롬프트 및 Redis 표준 응답 포맷 준수.

---

## 🚀 빠른 시작

### CLI 실행
```bash
python main.py
```

### 단위 테스트 실행 (28개 테스트 전원 0.006초 통과)
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

### 아키텍처 다이어그램 재생성
```bash
python scripts/generate_diagrams_matplotlib.py
```

---

## 📚 상세 문서
- [📋 개발 계획서 (PLAN.md)](PLAN.md)
- [📘 요구사항 대조 및 주니어 멘토링 스터디 (스터디.md)](스터디.md)
- [📑 세부 엔지니어링 리포트 (REPORT.md)](REPORT.md)
- [🎧 NotebookLM 학습 및 팟캐스트 가이드 (NOTEBOOKLM_GUIDE.md)](NOTEBOOKLM_GUIDE.md)

---

## 🧪 🔍 평가자를 위한 원클릭 요구사항 검증 및 시각화 테스트 공간

> 평가자가 과제 요구사항(`코디세이 b5-1.md`)의 모든 구현 항목이 100% 정상 작동하는지 **명령어별 상세 동작 원리**와 **데이터가 나타나고 사라지는 실시간 JSON 상태 변화**로 눈에 띄게 확인할 수 있는 전용 공간입니다.

---

### 1. 🌟 [강력 추천] 실시간 JSON 데이터 상태 변화 시각화 러너 실행
명령어 하나하나가 무엇을 하는지 상세한 설명과 함께 실행되며, 데이터가 **생성(`[+]`)**, **LRU 한도 초과로 방출(`[-]`)**, **TTL 만료로 소멸(`[X]`)**하는 전 과정을 실시간 JSON 스냅샷으로 터미널에 아름답게 출력합니다:

```bash
python scripts/demo_visualizer.py
```
> 💡 *한 단계씩 엔터를 누르며 직접 확인하려면 `python scripts/demo_visualizer.py --interactive`를 입력하세요.*

---

### 2. 📊 [원클릭 자동 검증] 요구사항 8대 항목 전수 검증 테이블 & 요약 JSON
AST 정밀 문법 검사를 통한 `Zero Built-in Collections` 제약 준수 여부부터 8대 기능 전수 검증을 터미널 컬러 테이블로 즉시 출력합니다:

```bash
python scripts/verify_requirements.py
```

#### 📊 터미널 검증 결과 테이블 (실제 실행 화면)
```text
================================================================================
  [*] MINI REDIS : Evaluator Automated Requirements Verification Suite
================================================================================

------------------------------------------------------------------------------------------
 분류               | 검증 항목                                  | 결과    | 세부 증명
------------------------------------------------------------------------------------------
 제약사항           | Zero Built-in Collections (dict/set/collections 금지) | [OK] PASS | AST 정밀 검사 결과 dict/set 문법 사용 0건
 String 명령어 (6종) | SET, GET, EXISTS, DBSIZE, KEYS, DEL 정상 작동 | [OK] PASS | SET->OK, GET->"Alice", DEL->(integer) 1
 CLI 파싱           | 따옴표 감싼 문자열 공백 보존 (shlex)       | [OK] PASS | GET greeting -> "Hello Mini Redis World"
 메모리 관리        | used_memory UTF-8 바이트 정밀 합산 (한글 9바이트 지원) | [OK] PASS | used_memory:15 | maxmemory:0 | evicted_keys:0
 LRU 방출           | maxmemory 초과 시 LRU 노드 O(1) 자동 방출 & evicted_keys 카운트 | [OK] PASS | k1->(nil), k2->"v2", info->used_memory:4 | maxmemory:6 | evicted_keys:1
 OOM 에러 방어      | 단일 엔트리 > maxmemory 시 저장 거부 및 OOM 에러 출력 | [OK] PASS | (error) OOM command not allowed when used_memory > 'maxmemory'
 TTL 관리           | MinHeap 기반 만료 시간 설정, 잔여초 조회, Lazy Deletion | [OK] PASS | EXPIRE->(integer) 1, TTL(초기)->(integer) 10, TTL(11초후)->(integer) -2, GET(11초후)->(nil)
 엣지 케이스        | SET으로 덮어쓸 때 기존 TTL 초기화(-1)      | [OK] PASS | TTL temp -> (integer) -1
------------------------------------------------------------------------------------------

>> 총 검증 항목: 8개 | 통과: 8개 | 통과율: 100.0%
```

---

### 3. 🎯 [대화형 REPL 수동 검증 & 상세 해설] 명령어 설명 및 실시간 JSON 상태 전이

직접 터미널에서 `python main.py`를 실행하여 테스트할 때, 각 명령어가 **무엇을 하는지**와 **내부 데이터가 어떻게 생성되고 사라지는지(JSON 스냅샷)**를 상세히 대조해볼 수 있습니다.

```bash
python main.py
```

---

#### 🌟 시나리오 1: 따옴표 파싱 및 String 기본 명령어 6종
> **검증 목표**: 공백이 포함된 문자열을 따옴표(`"`)로 묶어 온전히 저장하고, 6대 기본 명령어(`SET`, `GET`, `EXISTS`, `DBSIZE`, `KEYS`, `DEL`)의 정상 동작과 **데이터 삭제 시 완전히 소멸하는 과정**을 확인합니다.

##### 1) 명령어별 동작 상세 설명
| 순서 | 명령어 | 명령어 설명 및 내부 동작 원리 | 기대 응답 |
| :--- | :--- | :--- | :--- |
| **Step 1** | `SET user:1 "Alice In Wonderland"` | `shlex`로 큰따옴표 안의 띄어쓰기를 원자적으로 보존하여 키 `user:1`에 저장하고 메모리 회계(25B)를 반영합니다. | `OK` |
| **Step 2** | `GET user:1` | 자체 `HashMap`에서 $O(1)$로 값을 조회하고, LRU 연결 리스트의 맨 앞(MRU)으로 승격합니다. | `"Alice In Wonderland"` |
| **Step 3** | `EXISTS user:1` | 키의 존재 여부를 $O(1)$로 확인합니다 (존재 시 1, 부재 시 0). | `(integer) 1` |
| **Step 4** | `DBSIZE` | 현재 저장된 총 유효 키의 개수를 반환합니다. | `(integer) 1` |
| **Step 5** | `KEYS` | 현재 저장된 모든 키의 목록을 배열 형태로 출력합니다. | `1) "user:1"` |
| **Step 6** | `DEL user:1` | **[데이터 소멸]** 저장소, LRU 리스트, 메모리 회계에서 해당 키를 일괄 영구 삭제합니다. | `(integer) 1` |
| **Step 7** | `GET user:1` | 삭제되었으므로 없는 키로 인식되어 `(nil)`을 반환합니다. | `(nil)` |

##### 2) 터미널 실행 로그
```text
mini-redis> SET user:1 "Alice In Wonderland"
OK
mini-redis> GET user:1
"Alice In Wonderland"
mini-redis> EXISTS user:1
(integer) 1
mini-redis> DBSIZE
(integer) 1
mini-redis> KEYS
1) "user:1"
mini-redis> DEL user:1
(integer) 1
mini-redis> GET user:1
(nil)
```

##### 3) 📦 실시간 JSON 데이터 상태 전이 (데이터가 생성되고 사라지는 과정)
```json
/* [Step 1: SET 실행 후 - 데이터가 메모리에 나타남 (+)] */
{
  "action": "[+] 데이터 생성 (INSERT)",
  "data_changes": {
    "[+] 나타난 데이터 (Added)": ["user:1"],
    "[-] 사라진 데이터 (Removed)": "없음"
  },
  "current_storage": {
    "user:1": { "value": "Alice In Wonderland", "bytes": 25, "ttl": -1 }
  },
  "lru_order": "user:1",
  "memory_status": { "used_memory_bytes": 25, "maxmemory_bytes": 0, "evicted_keys_count": 0 }
}

/* [Step 6: DEL 실행 후 - 데이터가 메모리에서 완전히 사라짐 (-)] */
{
  "action": "[-] 데이터 완전 삭제 (DELETED)",
  "data_changes": {
    "[+] 나타난 데이터 (Added)": "없음",
    "[-] 사라진 데이터 (Removed)": ["user:1"]
  },
  "current_storage": {},
  "lru_order": "(empty)",
  "memory_status": { "used_memory_bytes": 0, "maxmemory_bytes": 0, "evicted_keys_count": 0 }
}
```

---

#### 🌟 시나리오 2: maxmemory 제한 & O(1) LRU 자동 방출 (Eviction)
> **검증 목표**: 최대 메모리를 10바이트로 제한한 상태에서, 새 데이터가 들어올 때 **가장 오래 사용되지 않은 키(LRU)가 자동으로 방출되어 사라지는 과정**을 확인합니다.

##### 1) 명령어별 동작 상세 설명
| 순서 | 명령어 | 명령어 설명 및 내부 동작 원리 | 기대 응답 |
| :--- | :--- | :--- | :--- |
| **Step 1** | `CONFIG SET maxmemory 10` | 허용 메모리 한도를 10바이트로 설정합니다. 초과 시 LRU 방출이 즉시 트리거됩니다. | `OK` |
| **Step 2** | `SET a 1234` | 키 `a`(1B) + 값 `1234`(4B) = 5바이트 저장. (현재 메모리 5 / 10B) | `OK` |
| **Step 3** | `SET b 5678` | 키 `b`(1B) + 값 `5678`(4B) = 5바이트 추가. 메모리가 10/10B로 100% 한도에 도달합니다. LRU 순서: `b (최신) -> a (가장 오래됨)` | `OK` |
| **Step 4** | `INFO memory` | 현재 메모리 상태를 확인합니다. | `used_memory:10`, `maxmemory:10`, `evicted_keys:0` |
| **Step 5** | `SET c 9999` | **★ [핵심 방출]** 키 `c`(5B) 저장 시 10B를 초과하므로, 가장 오래 안 쓴 **`a`가 O(1)으로 자동 방출되어 사라지고** `c`가 저장됩니다! | `OK` |
| **Step 6** | `INFO memory` | 방출 누적 개수가 1개로 증가하고 메모리는 10B를 유지함을 확인합니다. | `used_memory:10`, `maxmemory:10`, `evicted_keys:1` |
| **Step 7** | `GET a` | 방출된 `a`는 메모리에서 삭제되었으므로 `(nil)`을 반환합니다. | `(nil)` |
| **Step 8** | `GET b` | 살아남은 `b`는 정상 조회되며, 조회로 인해 LRU 맨 앞(MRU)으로 승격됩니다. | `"5678"` |
| **Step 9** | `GET c` | 신규 진입한 `c`도 정상 보존되어 있음을 확인합니다. | `"9999"` |

##### 2) 터미널 실행 로그
```text
mini-redis> CONFIG SET maxmemory 10
OK
mini-redis> SET a 1234
OK
mini-redis> SET b 5678
OK
mini-redis> INFO memory
used_memory:10
maxmemory:10
evicted_keys:0

mini-redis> SET c 9999
OK
mini-redis> INFO memory
used_memory:10
maxmemory:10
evicted_keys:1

mini-redis> GET a
(nil)
mini-redis> GET b
"5678"
mini-redis> GET c
"9999"
```

##### 3) 📦 실시간 JSON 데이터 상태 전이 (한도 초과로 'a'가 사라지고 'c'가 나타남)
```json
/* [Step 3: SET b 완료 - 10바이트 한도 포화 상태] */
{
  "action": "[+] 데이터 생성 (used_memory: 10B, 한도 포화)",
  "current_storage": {
    "a": { "value": "1234", "bytes": 5, "ttl": -1 },
    "b": { "value": "5678", "bytes": 5, "ttl": -1 }
  },
  "lru_order": "b (최신 MRU) -> a (방출 1순위 LRU)",
  "memory_status": { "used_memory_bytes": 10, "maxmemory_bytes": 10, "evicted_keys_count": 0 }
}

/* [Step 5: SET c 9999 실행 후 ★ - 'a'가 방출 소멸되고 'c'가 나타남!] */
{
  "action": "[-] LRU 자동 방출 ('a' 삭제 & 'c' 추가)",
  "data_changes": {
    "[+] 나타난 데이터 (Added)": ["c"],
    "[-] 사라진 데이터 (Removed)": ["a"],
    "방출 누적 (Evicted)": "1개"
  },
  "current_storage": {
    "b": { "value": "5678", "bytes": 5, "ttl": -1 },
    "c": { "value": "9999", "bytes": 5, "ttl": -1 }
  },
  "lru_order": "c (최신 MRU) -> b (다음 방출 후보 LRU)",
  "memory_status": { "used_memory_bytes": 10, "maxmemory_bytes": 10, "evicted_keys_count": 1 }
}
```

---

#### 🌟 시나리오 3: 단일 엔트리 OOM (Out Of Memory) 에러 방어
> **검증 목표**: 단일 엔트리(키+값) 자체의 크기가 `maxmemory` 전체 한도보다 큰 경우, 기존 캐시 데이터를 함부로 방출하지 않고 **저장을 사전에 거부하여 기존 데이터를 안전하게 보존**하는지 확인합니다.

##### 1) 명령어별 동작 상세 설명
| 순서 | 명령어 | 명령어 설명 및 내부 동작 원리 | 기대 응답 |
| :--- | :--- | :--- | :--- |
| **Step 1** | `CONFIG SET maxmemory 10` | 최대 메모리를 10바이트로 제한합니다. | `OK` |
| **Step 2** | `SET super_long_key "this value is definitely too large"` | 엔트리 크기(56B)가 maxmemory(10B)를 초과하므로 저장 거부 및 OOM 에러 출력. | `(error) OOM command not allowed when used_memory > 'maxmemory'` |
| **Step 3** | `INFO memory` | OOM으로 저장이 거부되었으므로 기존 데이터와 메모리가 100% 안전하게 보존되었음을 확인. | 기존 데이터 보존 |

##### 2) 터미널 실행 로그
```text
mini-redis> CONFIG SET maxmemory 10
OK
mini-redis> SET super_long_key "this value is definitely too large"
(error) OOM command not allowed when used_memory > 'maxmemory'
```

##### 3) 📦 실시간 JSON 데이터 상태 전이 (저장 거부 및 기존 데이터 안전 보존)
```json
{
  "action": "[🛡️] OOM 저장 거부 (기존 캐시 100% 안전 보존)",
  "data_changes": {
    "[+] 나타난 데이터 (Added)": "없음 (저장 거부)",
    "[-] 사라진 데이터 (Removed)": "없음 (방출 방지)"
  },
  "current_storage": {
    "b": { "value": "5678", "bytes": 5, "ttl": -1 },
    "c": { "value": "9999", "bytes": 5, "ttl": -1 }
  },
  "memory_status": { "used_memory_bytes": 10, "maxmemory_bytes": 10, "evicted_keys_count": 1 }
}
```

---

#### 🌟 시나리오 4: 최소 힙 기반 TTL 만료(Lazy Deletion) 및 덮어쓰기 초기화
> **검증 목표**: 최소 힙(`MinHeap`)을 통해 유효기간을 관리하고, 시간이 경과했을 때 조회 시점에 **데이터가 자동으로 소멸(삭제)되어 사라지는 과정**과 `SET` 덮어쓰기 시 기존 TTL이 초기화되는 엣지 케이스를 확인합니다.

##### 1) 명령어별 동작 상세 설명
| 순서 | 명령어 | 명령어 설명 및 내부 동작 원리 | 기대 응답 |
| :--- | :--- | :--- | :--- |
| **Step 1** | `SET token "secret123"` | 새 키를 저장합니다. 초기 상태의 TTL은 영구를 의미하는 `-1`입니다. | `OK` |
| **Step 2** | `EXPIRE token 60` | 최소 힙에 `(만료시각, "token")`을 $O(\log N)$ 삽입하고 유효기간 60초를 부여합니다. | `(integer) 1` |
| **Step 3** | `TTL token` | 현재 남은 만료 시간(초)을 조회합니다. | `(integer) 60` |
| **Step 4** | `SET token "new_secret"` | **★ [엣지 케이스]** 기존 키를 덮어쓰면 Redis 표준에 따라 기존 만료 시간(TTL)이 즉시 초기화(삭제)됩니다. | `OK` |
| **Step 5** | `TTL token` | 만료 시간이 성공적으로 해제되어 영구 보관(`-1`) 상태로 복원됨을 확인합니다. | `(integer) -1` |
| **Step 6** | `EXPIRE token 10` 후 11초 대기 | 만료 시간을 10초로 부여한 후 시간이 11초 경과한 시점입니다. | `(integer) 1` |
| **Step 7** | `GET token` | **★ [핵심 만료 소멸]** 조회 시점에 MinHeap 만료 시각을 검사하여 이미 시간이 지났음을 감지하고, **데이터를 메모리에서 즉시 영구 삭제(소멸)한 뒤** `(nil)`을 반환합니다! | `(nil)` |

##### 2) 터미널 실행 로그
```text
mini-redis> SET token "secret123"
OK
mini-redis> EXPIRE token 60
(integer) 1
mini-redis> TTL token
(integer) 60
mini-redis> SET token "new_secret"
OK
mini-redis> TTL token
(integer) -1
mini-redis> quit
Bye!
```

##### 3) 📦 실시간 JSON 데이터 상태 전이 (만료로 인해 데이터가 영구 소멸하는 과정)
```json
/* [Step 2: EXPIRE 10 설정 - 만료 시각이 등록된 상태] */
{
  "action": "[⏱] TTL 만료 시간 설정 (10초)",
  "current_storage": {
    "token": { "value": "secret123", "bytes": 14, "ttl": 10 }
  },
  "memory_status": { "used_memory_bytes": 14, "maxmemory_bytes": 0, "evicted_keys_count": 0 }
}

/* [Step 7: 11초 경과 후 GET token 호출 시점 ★ - 데이터가 감쪽같이 사라짐!] */
{
  "action": "[X] TTL 만료 소멸 (Lazy Deletion 발동)",
  "data_changes": {
    "[+] 나타난 데이터 (Added)": "없음",
    "[-] 사라진 데이터 (Removed)": ["token"]
  },
  "current_storage": {},
  "lru_order": "(empty)",
  "memory_status": { "used_memory_bytes": 0, "maxmemory_bytes": 0, "evicted_keys_count": 0 }
}
```


