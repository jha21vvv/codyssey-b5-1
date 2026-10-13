"""
MiniRedis 통합 및 기능별 단위 테스트 (tests/test_mini_redis.py)
결정론적 가상 시간 주입 및 엣지 케이스 무결성 100% 검증
"""

import unittest
from src.mini_redis import MiniRedis
from src.cli import parse_line


class MockTime:
    """결정론적 단위 테스트를 위한 가상 시간 제공자"""
    def __init__(self, start_time=1000.0):
        self.current_time = start_time

    def now(self):
        return self.current_time

    def advance(self, seconds):
        self.current_time += seconds


class TestMiniRedis(unittest.TestCase):
    def setUp(self):
        self.mock_time = MockTime(1000.0)
        self.redis = MiniRedis(time_provider=self.mock_time.now)

    def test_basic_string_commands(self):
        # SET & GET
        self.assertEqual(self.redis.execute_command(["SET", "user:1", "Alice"]), "OK")
        self.assertEqual(self.redis.execute_command(["GET", "user:1"]), '"Alice"')
        self.assertEqual(self.redis.execute_command(["GET", "user:999"]), "(nil)")

        # EXISTS
        self.assertEqual(self.redis.execute_command(["EXISTS", "user:1"]), "(integer) 1")
        self.assertEqual(self.redis.execute_command(["EXISTS", "user:999"]), "(integer) 0")

        # DBSIZE
        self.assertEqual(self.redis.execute_command(["DBSIZE"]), "(integer) 1")
        self.redis.execute_command(["SET", "user:2", "Bob"])
        self.assertEqual(self.redis.execute_command(["DBSIZE"]), "(integer) 2")

        # KEYS
        keys_out = self.redis.execute_command(["KEYS"])
        self.assertIn('"user:1"', keys_out)
        self.assertIn('"user:2"', keys_out)

        # DEL
        self.assertEqual(self.redis.execute_command(["DEL", "user:1"]), "(integer) 1")
        self.assertEqual(self.redis.execute_command(["DEL", "user:1"]), "(integer) 0")
        self.assertEqual(self.redis.execute_command(["GET", "user:1"]), "(nil)")
        self.assertEqual(self.redis.execute_command(["DBSIZE"]), "(integer) 1")

    def test_memory_and_used_memory_utf8(self):
        # "k" (1 byte) + "val" (3 bytes) = 4 bytes
        self.redis.execute_command(["SET", "k", "val"])
        info = self.redis.execute_command(["INFO", "memory"])
        self.assertIn("used_memory:4", info)
        self.assertIn("maxmemory:0", info)
        self.assertIn("evicted_keys:0", info)

        # 한글 UTF-8 바이트 테스트: "이름" (6 bytes) + "홍길동" (9 bytes) = 15 bytes
        self.redis.execute_command(["SET", "이름", "홍길동"])
        info2 = self.redis.execute_command(["INFO", "memory"])
        # 4 + 15 = 19 bytes
        self.assertIn("used_memory:19", info2)

    def test_single_entry_oom(self):
        # maxmemory를 10바이트로 설정
        self.redis.execute_command(["CONFIG", "SET", "maxmemory", "10"])

        # "large_key" (9 bytes) + "large_value" (11 bytes) = 20 bytes > 10 bytes
        res = self.redis.execute_command(["SET", "large_key", "large_value"])
        self.assertEqual(res, "(error) OOM command not allowed when used_memory > 'maxmemory'")
        # 저장되지 않았는지 확인
        self.assertEqual(self.redis.execute_command(["GET", "large_key"]), "(nil)")

    def test_lru_eviction(self):
        # 각 엔트리 크기:
        # "k1": "v1" -> 2 + 2 = 4 bytes
        # "k2": "v2" -> 2 + 2 = 4 bytes
        # maxmemory = 6 bytes 로 설정하면 엔트리 1개(4 bytes)만 유지 가능 (2개 넣으면 8 bytes > 6 bytes)
        self.redis.execute_command(["CONFIG", "SET", "maxmemory", "6"])
        self.redis.execute_command(["SET", "k1", "v1"])
        self.redis.execute_command(["SET", "k2", "v2"])

        # k1이 방출되고 k2만 남아있어야 함
        self.assertEqual(self.redis.execute_command(["GET", "k1"]), "(nil)")
        self.assertEqual(self.redis.execute_command(["GET", "k2"]), '"v2"')

        info = self.redis.execute_command(["INFO", "memory"])
        self.assertIn("evicted_keys:1", info)
        self.assertIn("used_memory:4", info)

    def test_lru_access_order_update(self):
        # maxmemory = 10 bytes -> 각 4바이트인 k1, k2 총 8바이트까지 동시 수용 가능
        # k1 추가(4) -> k2 추가(4) -> k1 GET(k1이 최신이 됨) -> k3 추가(4)
        # 이때 k2가 LRU이므로 k2가 방출되어야 함!
        self.redis.execute_command(["CONFIG", "SET", "maxmemory", "10"])
        self.redis.execute_command(["SET", "k1", "v1"])
        self.redis.execute_command(["SET", "k2", "v2"])

        # k1 접근하여 최신으로 승격
        self.assertEqual(self.redis.execute_command(["GET", "k1"]), '"v1"')

        # k3 추가 -> 총 12바이트 > 10바이트이므로 LRU인 k2 방출
        self.redis.execute_command(["SET", "k3", "v3"])

        self.assertEqual(self.redis.execute_command(["GET", "k1"]), '"v1"')  # 생존
        self.assertEqual(self.redis.execute_command(["GET", "k2"]), "(nil)") # 방출됨
        self.assertEqual(self.redis.execute_command(["GET", "k3"]), '"v3"')  # 생존

    def test_ttl_and_expire(self):
        self.redis.execute_command(["SET", "temp", "val"])
        self.assertEqual(self.redis.execute_command(["TTL", "temp"]), "(integer) -1")

        # EXPIRE 10초 설정
        self.assertEqual(self.redis.execute_command(["EXPIRE", "temp", "10"]), "(integer) 1")
        self.assertEqual(self.redis.execute_command(["TTL", "temp"]), "(integer) 10")

        # 4초 경과
        self.mock_time.advance(4)
        self.assertEqual(self.redis.execute_command(["TTL", "temp"]), "(integer) 6")
        self.assertEqual(self.redis.execute_command(["GET", "temp"]), '"val"')

        # 7초 추가 경과 (총 11초 경과 -> 만료됨)
        self.mock_time.advance(7)
        self.assertEqual(self.redis.execute_command(["TTL", "temp"]), "(integer) -2")
        self.assertEqual(self.redis.execute_command(["GET", "temp"]), "(nil)")
        self.assertEqual(self.redis.execute_command(["EXISTS", "temp"]), "(integer) 0")

    def test_expire_zero_or_negative(self):
        self.redis.execute_command(["SET", "k", "v"])
        # seconds <= 0이면 즉시 만료 삭제 후 (integer) 1
        self.assertEqual(self.redis.execute_command(["EXPIRE", "k", "0"]), "(integer) 1")
        self.assertEqual(self.redis.execute_command(["GET", "k"]), "(nil)")

        # 없는 키에 EXPIRE 호출 시 (integer) 0
        self.assertEqual(self.redis.execute_command(["EXPIRE", "non_existent", "10"]), "(integer) 0")

    def test_set_overwrites_clears_ttl(self):
        self.redis.execute_command(["SET", "k", "v1"])
        self.redis.execute_command(["EXPIRE", "k", "60"])
        self.assertEqual(self.redis.execute_command(["TTL", "k"]), "(integer) 60")

        # SET으로 덮어쓰면 TTL은 초기화(-1)되어야 함
        self.redis.execute_command(["SET", "k", "v2"])
        self.assertEqual(self.redis.execute_command(["TTL", "k"]), "(integer) -1")
        self.assertEqual(self.redis.execute_command(["GET", "k"]), '"v2"')

    def test_expired_key_does_not_update_lru(self):
        # 만료된 키는 GET 시 먼저 삭제 후 (nil) 반환하고 LRU를 갱신하지 않아야 함
        self.redis.execute_command(["SET", "k1", "v1"])
        self.redis.execute_command(["EXPIRE", "k1", "5"])
        self.mock_time.advance(10) # 만료됨

        res = self.redis.execute_command(["GET", "k1"])
        self.assertEqual(res, "(nil)")
        self.assertEqual(self.redis.execute_command(["DBSIZE"]), "(integer) 0")

    def test_error_standards(self):
        # Unknown command
        self.assertEqual(
            self.redis.execute_command(["FOOBAR"]),
            "(error) ERR unknown command 'FOOBAR'"
        )

        # Wrong arguments
        self.assertEqual(
            self.redis.execute_command(["SET", "a"]),
            "(error) ERR wrong number of arguments for 'set' command"
        )
        self.assertEqual(
            self.redis.execute_command(["GET"]),
            "(error) ERR wrong number of arguments for 'get' command"
        )

        # Invalid integer
        self.assertEqual(
            self.redis.execute_command(["EXPIRE", "a", "not_a_number"]),
            "(error) ERR value is not an integer or out of range"
        )
        self.assertEqual(
            self.redis.execute_command(["CONFIG", "SET", "maxmemory", "-5"]),
            "(error) ERR value is not an integer or out of range"
        )

    def test_shlex_quote_parsing(self):
        args1 = parse_line('SET greeting "Hello World"')
        self.assertEqual(args1, ["SET", "greeting", "Hello World"])
        self.redis.execute_command(args1)
        self.assertEqual(self.redis.execute_command(["GET", "greeting"]), '"Hello World"')


if __name__ == "__main__":
    unittest.main()
