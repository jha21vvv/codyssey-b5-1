"""
최소 힙 단위 테스트 (tests/test_min_heap.py)
"""

import unittest
from src.min_heap import MinHeap


class TestMinHeap(unittest.TestCase):
    def setUp(self):
        self.heap = MinHeap()

    def test_initially_empty(self):
        self.assertEqual(self.heap.size(), 0)
        self.assertTrue(self.heap.is_empty())
        self.assertIsNone(self.heap.peek())
        self.assertIsNone(self.heap.pop())

    def test_push_and_peek(self):
        self.heap.push(10)
        self.assertEqual(self.heap.peek(), 10)
        self.heap.push(5)
        self.assertEqual(self.heap.peek(), 5)
        self.heap.push(20)
        self.assertEqual(self.heap.peek(), 5)
        self.assertEqual(self.heap.size(), 3)

    def test_pop_ordering(self):
        # 무작위 순서로 삽입 후 오름차순으로 추출되는지 확인
        values = [15, 3, 22, 1, 8, 45, 2]
        for v in values:
            self.heap.push(v)

        sorted_vals = []
        while not self.heap.is_empty():
            sorted_vals.append(self.heap.pop())

        self.assertEqual(sorted_vals, sorted(values))

    def test_tuple_elements_for_ttl(self):
        # (expire_at, key) 형태의 튜플 처리 검증
        self.heap.push((100.5, "key_c"))
        self.heap.push((50.0, "key_a"))
        self.heap.push((75.2, "key_b"))

        self.assertEqual(self.heap.pop(), (50.0, "key_a"))
        self.assertEqual(self.heap.pop(), (75.2, "key_b"))
        self.assertEqual(self.heap.pop(), (100.5, "key_c"))
        self.assertTrue(self.heap.is_empty())

    def test_tie_breaking(self):
        # 만료 시각이 동일한 경우 key의 사전순으로 일관된 pop 순서 보장
        self.heap.push((10.0, "banana"))
        self.heap.push((10.0, "apple"))
        self.heap.push((10.0, "cherry"))

        self.assertEqual(self.heap.pop(), (10.0, "apple"))
        self.assertEqual(self.heap.pop(), (10.0, "banana"))
        self.assertEqual(self.heap.pop(), (10.0, "cherry"))


if __name__ == "__main__":
    unittest.main()
