"""
체이닝 해시맵 단위 테스트 (tests/test_hash_map.py)
"""

import unittest
from src.hash_map import HashMap


class TestHashMap(unittest.TestCase):
    def setUp(self):
        self.map = HashMap(initial_capacity=4)

    def test_put_and_get(self):
        self.map.put("k1", "v1")
        self.map.put("k2", "v2")
        self.assertEqual(self.map.get("k1"), "v1")
        self.assertEqual(self.map.get("k2"), "v2")
        self.assertIsNone(self.map.get("non_existent"))

    def test_update_existing_key(self):
        self.map.put("key", "val1")
        old_val = self.map.put("key", "val2")
        self.assertEqual(old_val, "val1")
        self.assertEqual(self.map.get("key"), "val2")
        self.assertEqual(self.map.size(), 1)

    def test_remove(self):
        self.map.put("k1", "v1")
        self.map.put("k2", "v2")
        self.assertEqual(self.map.size(), 2)

        removed = self.map.remove("k1")
        self.assertEqual(removed, "v1")
        self.assertIsNone(self.map.get("k1"))
        self.assertEqual(self.map.size(), 1)
        self.assertFalse(self.map.contains("k1"))

        # 존재하지 않는 키 삭제
        self.assertIsNone(self.map.remove("non_existent"))

    def test_contains_and_keys(self):
        self.map.put("a", 1)
        self.map.put("b", 2)
        self.assertTrue(self.map.contains("a"))
        self.assertTrue(self.map.contains("b"))
        self.assertFalse(self.map.contains("c"))

        keys = self.map.keys()
        self.assertEqual(len(keys), 2)
        self.assertIn("a", keys)
        self.assertIn("b", keys)

    def test_dynamic_resizing(self):
        # 초기 capacity 4이므로, 4 * 0.75 = 3 초과(즉 4개 삽입 시) 리사이징 발생
        self.assertEqual(self.map.capacity(), 4)
        self.map.put("1", "one")
        self.map.put("2", "two")
        self.map.put("3", "three")
        self.assertEqual(self.map.capacity(), 4)

        # 4번째 키 삽입 -> 4/4 = 1.0 > 0.75 -> 2배(8)로 리사이징
        self.map.put("4", "four")
        self.assertEqual(self.map.capacity(), 8)
        self.assertEqual(self.map.size(), 4)

        # 모든 기존 데이터가 올바르게 재해싱되어 조회 가능한지 검증
        self.assertEqual(self.map.get("1"), "one")
        self.assertEqual(self.map.get("2"), "two")
        self.assertEqual(self.map.get("3"), "three")
        self.assertEqual(self.map.get("4"), "four")

    def test_collision_handling(self):
        # 100개의 키-값을 대량 삽입하여 해시 충돌 및 재해싱 스트레스 테스트
        large_map = HashMap(initial_capacity=8)
        for i in range(100):
            large_map.put(f"key_{i}", f"val_{i}")

        self.assertEqual(large_map.size(), 100)
        for i in range(100):
            self.assertEqual(large_map.get(f"key_{i}"), f"val_{i}")


if __name__ == "__main__":
    unittest.main()
