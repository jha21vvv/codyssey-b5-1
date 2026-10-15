"""
MiniRedis 코어 엔진 모듈
내장 dict, set, collections를 일절 사용하지 않고
직접 구현한 HashMap, DoublyLinkedList, MinHeap을 조화시켜 Redis 명령어를 처리합니다.
"""

import time
from src.hash_map import HashMap
from src.lru_cache import LRUManager
from src.memory_manager import MemoryManager
from src.ttl_manager import TTLManager


class MiniRedis:
    """
    Mini Redis 코어 엔진
    - Key-Value Storage: 자체 HashMap
    - LRU Tracking: LRUManager (DoublyLinkedList + HashMap)
    - TTL Management: TTLManager (MinHeap + HashMap)
    - Memory Management: MemoryManager
    """
    def __init__(self, time_provider=time.time):
        self._time_provider = time_provider
        self._storage = HashMap()
        self._lru = LRUManager()
        self._ttl = TTLManager(time_provider=self._time_provider)
        self._memory = MemoryManager()

    def _delete_entry(self, key, is_eviction=False, is_expired=False):
        """
        내부 엔트리 완전 삭제 헬퍼 (저장소, LRU, TTL, 메모리에서 일괄 제거)
        """
        val = self._storage.remove(key)
        if val is not None:
            self._lru.remove(key)
            self._ttl.remove_ttl(key)
            self._memory.remove_entry_memory(key, val)
            return True
        return False

    def _check_and_expire(self, key):
        """
        키가 만료되었는지 확인하고, 만료되었으면 즉시 삭제합니다.
        삭제되었으면 True, 여전히 유효하거나 없으면 False 반환
        """
        if not self._storage.contains(key):
            return False
        
        if self._ttl.is_expired(key):
            self._delete_entry(key, is_expired=True)
            return True
        return False

    def execute_command(self, args):
        """
        파싱된 인자 리스트(예: ['SET', 'name', 'Alice'])를 받아 적절한 명령어를 실행하고
        Redis 표준 응답 문자열을 반환합니다.
        """
        if not args:
            return ""

        cmd = args[0].upper()

        if cmd == "SET":
            return self._cmd_set(args)
        elif cmd == "GET":
            return self._cmd_get(args)
        elif cmd == "DEL":
            return self._cmd_del(args)
        elif cmd == "EXISTS":
            return self._cmd_exists(args)
        elif cmd == "DBSIZE":
            return self._cmd_dbsize(args)
        elif cmd == "KEYS":
            return self._cmd_keys(args)
        elif cmd == "CONFIG":
            return self._cmd_config(args)
        elif cmd == "INFO":
            return self._cmd_info(args)
        elif cmd == "EXPIRE":
            return self._cmd_expire(args)
        elif cmd == "TTL":
            return self._cmd_ttl(args)
        else:
            return f"(error) ERR unknown command '{args[0]}'"

    def _cmd_set(self, args):
        """SET key value"""
        if len(args) != 3:
            return "(error) ERR wrong number of arguments for 'set' command"

        key, value = args[1], args[2]

        if self._memory.is_single_entry_oom(key, value):
            return "(error) OOM command not allowed when used_memory > 'maxmemory'"

        self._check_and_expire(key)

        existing_val = self._storage.get(key)
        if existing_val is not None:
            self._ttl.remove_ttl(key)
            self._memory.update_entry_memory(key, existing_val, value)
            self._storage.put(key, value)
        else:
            self._memory.add_entry_memory(key, value)
            self._storage.put(key, value)

        self._lru.access(key)

        self._memory.evict_if_needed(self._lru, self._delete_entry)

        return "OK"

    def _cmd_get(self, args):
        """GET key"""
        if len(args) != 2:
            return "(error) ERR wrong number of arguments for 'get' command"

        key = args[1]

        if self._check_and_expire(key):
            return "(nil)"

        val = self._storage.get(key)
        if val is None:
            return "(nil)"

        self._lru.access(key)
        return f'"{val}"'

    def _cmd_del(self, args):
        """DEL key"""
        if len(args) != 2:
            return "(error) ERR wrong number of arguments for 'del' command"

        key = args[1]

        if self._check_and_expire(key):
            return "(integer) 0"

        deleted = self._delete_entry(key)
        return "(integer) 1" if deleted else "(integer) 0"

    def _cmd_exists(self, args):
        """EXISTS key"""
        if len(args) != 2:
            return "(error) ERR wrong number of arguments for 'exists' command"

        key = args[1]
        self._check_and_expire(key)

        exists = self._storage.contains(key)
        return "(integer) 1" if exists else "(integer) 0"

    def _cmd_dbsize(self, args):
        """DBSIZE"""
        if len(args) != 1:
            return "(error) ERR wrong number of arguments for 'dbsize' command"

        self._ttl.cleanup_expired(self._delete_entry)

        keys = self._storage.keys()
        for k in keys:
            self._check_and_expire(k)

        return f"(integer) {self._storage.size()}"

    def _cmd_keys(self, args):
        """KEYS"""
        if len(args) != 1:
            return "(error) ERR wrong number of arguments for 'keys' command"

        self._ttl.cleanup_expired(self._delete_entry)
        raw_keys = self._storage.keys()
        valid_keys = []
        for k in raw_keys:
            if not self._check_and_expire(k):
                valid_keys.append(k)

        if not valid_keys:
            return "(empty array)"

        lines = []
        for i, k in enumerate(valid_keys, 1):
            lines.append(f'{i}) "{k}"')
        return "\n".join(lines)

    def _cmd_config(self, args):
        """CONFIG SET maxmemory bytes"""
        if len(args) != 4 or args[1].upper() != "SET" or args[2].lower() != "maxmemory":
            return "(error) ERR unknown command or wrong arguments for 'config'"

        try:
            bytes_val = int(args[3])
            if bytes_val < 0:
                return "(error) ERR value is not an integer or out of range"
        except ValueError:
            return "(error) ERR value is not an integer or out of range"

        self._memory.maxmemory = bytes_val
        self._memory.evict_if_needed(self._lru, self._delete_entry)
        return "OK"

    def _cmd_info(self, args):
        """INFO memory"""
        if len(args) != 2 or args[1].lower() != "memory":
            return "(error) ERR wrong number of arguments for 'info' command"

        return self._memory.get_info_memory()

    def _cmd_expire(self, args):
        """EXPIRE key seconds"""
        if len(args) != 3:
            return "(error) ERR wrong number of arguments for 'expire' command"

        key = args[1]
        try:
            seconds = int(args[2])
        except ValueError:
            return "(error) ERR value is not an integer or out of range"

        if self._check_and_expire(key):
            return "(integer) 0"

        if not self._storage.contains(key):
            return "(integer) 0"

        if seconds <= 0:
            self._delete_entry(key, is_expired=True)
            return "(integer) 1"

        self._ttl.set_ttl(key, seconds)
        return "(integer) 1"

    def _cmd_ttl(self, args):
        """TTL key"""
        if len(args) != 2:
            return "(error) ERR wrong number of arguments for 'ttl' command"

        key = args[1]
        self._check_and_expire(key)

        key_exists = self._storage.contains(key)
        ttl_val = self._ttl.get_ttl_seconds(key, key_exists)
        return f"(integer) {ttl_val}"
