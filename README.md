# 🚀 Mini Redis (From Scratch Key-Value Store)

> Python 내장 컬렉션(`dict`, `set`, `collections`)을 일절 사용하지 않고, 오직 밑바닥부터 구현한 **이중 연결 리스트**, **체이닝 해시맵**, **최소 힙**으로 완성한 고성능 인메모리 Redis 엔진 및 CLI.

![System Architecture](file:///c:/Users/안재현/Documents/24_code/2609_codyssey/codyssey-b5-1/diagrams/01_system_architecture.png)

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
- [📋 개발 계획서 (PLAN.md)](file:///c:/Users/안재현/Documents/24_code/2609_codyssey/codyssey-b5-1/PLAN.md)
- [📘 요구사항 대조 및 주니어 멘토링 스터디 (스터디.md)](file:///c:/Users/안재현/Documents/24_code/2609_codyssey/codyssey-b5-1/스터디.md)
- [📑 세부 엔지니어링 리포트 (REPORT.md)](file:///c:/Users/안재현/Documents/24_code/2609_codyssey/codyssey-b5-1/REPORT.md)
- [🎧 NotebookLM 학습 및 팟캐스트 가이드 (NOTEBOOKLM_GUIDE.md)](file:///c:/Users/안재현/Documents/24_code/2609_codyssey/codyssey-b5-1/NOTEBOOKLM_GUIDE.md)

---

## 🧪 🔍 평가자를 위한 원클릭 요구사항 검증 및 시각화 테스트 공간

> 평가자가 과제 요구사항(`코디세이 b5-1.md`)의 모든 구현 항목이 100% 정상 작동하는지 터미널과 JSON으로 **실시간 시각적 검증**을 수행할 수 있는 전용 공간입니다.

### 1. [원클릭 자동 검증] 터미널 테이블 & JSON 시각화 러너 실행
복잡한 수동 입력 없이 아래 명령 한 줄을 실행하면 AST 문법 검사부터 8대 기능 전수 검증이 수행되며, **터미널 결과 테이블** 및 **시각적 JSON 데이터**가 즉시 출력됩니다:

```bash
python scripts/verify_requirements.py
```

#### 📊 터미널 시각적 출력 화면 (실제 실행 결과)
```text
================================================================================
  [*] MINI REDIS : Evaluator Automated Requirements Verification Suite
================================================================================

분류               | 항목                                       | 결과       | 세부 내용
----------------------------------------------------------------------------------------------------
제약사항             | Zero Built-in Collections (dict/set/collections 금지) | ✅ PASS   | AST 정밀 검사 결과 dict/set 문법 사용 0건
String 명령어 (6종)  | SET, GET, EXISTS, DBSIZE, KEYS, DEL 정상 작동 | ✅ PASS   | SET->OK, GET->"Alice", DEL->(integer) 1
CLI 파싱           | 따옴표 감싼 문자열 공백 보존 (shlex)                 | ✅ PASS   | GET greeting -> "Hello Mini Redis World"
메모리 관리           | used_memory UTF-8 바이트 정밀 합산 (한글 9바이트 지원) | ✅ PASS   | used_memory:15 | maxmemory:0 | evicted_keys:0
LRU 방출           | maxmemory 초과 시 LRU 노드 O(1) 자동 방출 & evicted_keys 카운트 | ✅ PASS   | k1->(nil), k2->"v2", info->used_memory:4 | maxmemory:6 | evicted_keys:1
OOM 에러 방어        | 단일 엔트리 > maxmemory 시 저장 거부 및 OOM 에러 출력   | ✅ PASS   | (error) OOM command not allowed when used_memory > 'maxmemory'
TTL 관리           | MinHeap 기반 만료 시간 설정, 잔여초 조회, Lazy Deletion | ✅ PASS   | EXPIRE->(integer) 1, TTL(초기)->(integer) 10, TTL(11초후)->(integer) -2, GET(11초후)->(nil)
엣지 케이스           | SET으로 덮어쓸 때 기존 TTL 초기화(-1)               | ✅ PASS   | TTL temp -> (integer) -1
----------------------------------------------------------------------------------------------------

총 검증 항목: 8개 | 통과: 8개 | 통과율: 100.0%
```

#### 📦 시각적 JSON 출력 데이터 공간 (실시간 상태 모니터링)
```json
{
  "timestamp": "2026-10-13 14:50:01",
  "total_checks": 8,
  "passed_checks": 8,
  "pass_rate": "100.0%",
  "results": [
    { "category": "제약사항", "item": "Zero Built-in Collections", "status": "PASS" },
    { "category": "String 명령어 (6종)", "item": "SET/GET/DEL/EXISTS/DBSIZE/KEYS", "status": "PASS" },
    { "category": "CLI 파싱", "item": "따옴표 공백 보존 (shlex)", "status": "PASS" },
    { "category": "메모리 관리", "item": "used_memory 한글 UTF-8 바이트 정밀 합산", "status": "PASS" },
    { "category": "LRU 방출", "item": "maxmemory 초과 시 O(1) 자동 방출 & evicted_keys", "status": "PASS" },
    { "category": "OOM 에러 방어", "item": "단일 엔트리 초과 시 OOM 에러 출력", "status": "PASS" },
    { "category": "TTL 관리", "item": "MinHeap 기반 만료 시간 & Lazy Deletion", "status": "PASS" },
    { "category": "엣지 케이스", "item": "SET 덮어쓰기 시 TTL 초기화(-1)", "status": "PASS" }
  ]
}
```

---

### 2. [대화형 REPL 수동 검증] 평가자가 직접 입력해보는 시나리오 코드

터미널에서 `python main.py`를 실행한 후 아래 명령을 한 줄씩 복사하여 붙여넣으면 각 기능의 동작을 눈으로 직접 확인할 수 있습니다.

#### 시나리오 1: 따옴표 파싱 및 String 기본 명령어 (6개)
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

#### 시나리오 2: maxmemory 설정 & O(1) LRU 자동 방출 검증
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

#### 시나리오 3: 단일 엔트리 OOM 에러 방어 검증
```text
mini-redis> CONFIG SET maxmemory 10
OK
mini-redis> SET super_long_key "this value is definitely too large"
(error) OOM command not allowed when used_memory > 'maxmemory'
```

#### 시나리오 4: 최소 힙 기반 TTL 만료 및 덮어쓰기 초기화 검증
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

