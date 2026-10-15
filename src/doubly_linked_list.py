"""
이중 연결 리스트 (Doubly Linked List) 모듈
dict, set, collections 없이 O(1) 삽입, 삭제, 이동 연산을 제공합니다.
"""

class Node:
    """이중 연결 리스트 노드"""
    def __init__(self, key=None, value=None, data=None):
        self.key = key
        self.value = value
        self.data = data if data is not None else (key, value)
        self.prev = None
        self.next = None

    def __repr__(self):
        return f"Node(key={self.key}, value={self.value})"


class DoublyLinkedList:
    """
    더미 헤드(dummy head)와 더미 테일(dummy tail)을 사용하는 원자적 O(1) 이중 연결 리스트
    """
    def __init__(self):
        self.head = Node()
        self.tail = Node()
        self.head.next = self.tail
        self.tail.prev = self.head
        self._size = 0

    def insert_front(self, node):
        if not isinstance(node, Node):
            node = Node(data=node)

        first = self.head.next
        node.prev = self.head
        node.next = first
        self.head.next = node
        first.prev = node
        self._size += 1
        return node

    def insert_back(self, node):
        if not isinstance(node, Node):
            node = Node(data=node)

        last = self.tail.prev
        node.prev = last
        node.next = self.tail
        last.next = node
        self.tail.prev = node
        self._size += 1
        return node

    def remove_node(self, node):
        if node is None or node.prev is None or node.next is None:
            return None
        
        if node is self.head or node is self.tail:
            return None

        prev_node = node.prev
        next_node = node.next
        prev_node.next = next_node
        next_node.prev = prev_node

        node.prev = None
        node.next = None
        self._size -= 1
        return node

    def remove_front(self):
        if self.is_empty():
            return None
        return self.remove_node(self.head.next)

    def remove_back(self):
        if self.is_empty():
            return None
        return self.remove_node(self.tail.prev)

    def move_to_front(self, node):
        if node is None or node is self.head or node is self.tail:
            return
        if self.head.next is node:
            return
        
        prev_node = node.prev
        next_node = node.next
        prev_node.next = next_node
        next_node.prev = prev_node

        first = self.head.next
        node.prev = self.head
        node.next = first
        self.head.next = node
        first.prev = node

    def size(self):
        return self._size

    def is_empty(self):
        return self._size == 0

    def to_list(self):
        result = []
        curr = self.head.next
        while curr is not self.tail:
            result.append(curr)
            curr = curr.next
        return result

    def __iter__(self):
        curr = self.head.next
        while curr is not self.tail:
            yield curr
            curr = curr.next
