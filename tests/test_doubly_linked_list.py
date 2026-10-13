"""
이중 연결 리스트 단위 테스트 (tests/test_doubly_linked_list.py)
"""

import unittest
from src.doubly_linked_list import DoublyLinkedList, Node


class TestDoublyLinkedList(unittest.TestCase):
    def setUp(self):
        self.dll = DoublyLinkedList()

    def test_initially_empty(self):
        self.assertEqual(self.dll.size(), 0)
        self.assertTrue(self.dll.is_empty())
        self.assertIsNone(self.dll.remove_front())
        self.assertIsNone(self.dll.remove_back())

    def test_insert_front_and_back(self):
        n1 = Node(key="k1", value="v1")
        n2 = Node(key="k2", value="v2")
        n3 = Node(key="k3", value="v3")

        self.dll.insert_front(n1)
        self.dll.insert_front(n2)  # front: n2 -> n1
        self.dll.insert_back(n3)   # order: n2 -> n1 -> n3

        self.assertEqual(self.dll.size(), 3)
        nodes = self.dll.to_list()
        self.assertEqual([n.key for n in nodes], ["k2", "k1", "k3"])

    def test_remove_front_and_back(self):
        n1 = Node(key="k1", value="v1")
        n2 = Node(key="k2", value="v2")
        self.dll.insert_back(n1)
        self.dll.insert_back(n2)

        removed_front = self.dll.remove_front()
        self.assertEqual(removed_front.key, "k1")
        self.assertEqual(self.dll.size(), 1)

        removed_back = self.dll.remove_back()
        self.assertEqual(removed_back.key, "k2")
        self.assertEqual(self.dll.size(), 0)
        self.assertTrue(self.dll.is_empty())

    def test_remove_node_in_middle(self):
        n1 = Node(key="k1")
        n2 = Node(key="k2")
        n3 = Node(key="k3")
        self.dll.insert_back(n1)
        self.dll.insert_back(n2)
        self.dll.insert_back(n3)

        self.dll.remove_node(n2)
        self.assertEqual(self.dll.size(), 2)
        self.assertEqual([n.key for n in self.dll.to_list()], ["k1", "k3"])

    def test_move_to_front(self):
        n1 = Node(key="k1")
        n2 = Node(key="k2")
        n3 = Node(key="k3")
        self.dll.insert_back(n1)
        self.dll.insert_back(n2)
        self.dll.insert_back(n3)  # k1, k2, k3

        # k3를 맨 앞으로 이동
        self.dll.move_to_front(n3)
        self.assertEqual([n.key for n in self.dll.to_list()], ["k3", "k1", "k2"])
        self.assertEqual(self.dll.size(), 3)

        # 이미 맨 앞인 노드 이동 시 아무런 부작용 없음
        self.dll.move_to_front(n3)
        self.assertEqual([n.key for n in self.dll.to_list()], ["k3", "k1", "k2"])

        # 중간 노드 k1 이동
        self.dll.move_to_front(n1)
        self.assertEqual([n.key for n in self.dll.to_list()], ["k1", "k3", "k2"])

    def test_sentinel_protection(self):
        # 더미 헤드나 테일을 삭제하려고 시도해도 안전하게 차단됨
        self.assertIsNone(self.dll.remove_node(self.dll.head))
        self.assertIsNone(self.dll.remove_node(self.dll.tail))
        self.assertIsNone(self.dll.remove_node(None))


if __name__ == "__main__":
    unittest.main()
