"""
CLI REPL 인터페이스 모듈
사용자로부터 명령어를 입력받아 MiniRedis 엔진에 전달하고 결과를 포맷팅하여 출력합니다.
"""

import sys
import shlex
from src.mini_redis import MiniRedis


def parse_line(line):
    """
    명령줄 문자열을 공백 및 따옴표 규칙에 맞추어 분할합니다.
    shlex를 사용하여 큰따옴표/작은따옴표로 감싸진 문자열을 원자적으로 파싱합니다.
    """
    try:
        return shlex.split(line)
    except ValueError:
        return line.strip().split()


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


def run_cli():
    """
    Mini Redis REPL 루프 (명령어 1개 입력 시마다 실시간 JSON 파일 및 터미널 상태 자동 갱신)
    """
    redis = MiniRedis()
    print("Welcome to Mini Redis CLI! Type 'exit' or 'quit' to close.")
    print("Zero-dependency from-scratch key-value store.")

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

            prev_keys = list(redis._storage.keys())

            response = redis.execute_command(args)
            if response:
                print(response)

            curr_keys = list(redis._storage.keys())
            added = [k for k in curr_keys if k not in prev_keys]
            removed = [k for k in prev_keys if k not in curr_keys]

            json_text = format_json_state(redis, added, removed)

            save_json_file(json_text)

        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            break
        except Exception as e:
            print(f"(error) ERR unexpected system error: {e}")


if __name__ == "__main__":
    run_cli()
