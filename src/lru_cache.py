"""
LRU 추적 관리자 (LRU Cache Manager) 모듈
DoublyLinkedList와 자체 HashMap을 결합하여 O(1) 시간 복잡도로 키 접근 추적 및 최하위(LRU) 키 방출을 수행합니다.
dict, set, collections는 일절 사용하지 않습니다.
"""

from src.doubly_linked_list import DoublyLinkedList, Node
from src.hash_map import HashMap


class LRUManager:
    """
    O(1) LRU(Least Recently Used) 추적 관리자
    - 최근 접근된 키는 리스트의 Head 쪽에 위치
    - 가장 오랫동안 접근되지 않은 키는 리스트의 Tail 쪽에 위치
    - 자체 HashMap(key -> Node)을 통해 O(1) 노드 탐색 및 위치 갱신
    """
    def __init__(self):
        self._list = DoublyLinkedList()
        self._node_map = HashMap()

    def access(self, key):
        """
        키에 접근(조회 또는 갱신/추가)했을 때 해당 키를 가장 최근(Head)으로 갱신합니다.
        O(1) 연산
        """
        existing_node = self._node_map.get(key)
        if existing_node is not None:
            self._list.move_to_front(existing_node)
        else:
            new_node = Node(key=key, value=None, data=key)
            self._list.insert_front(new_node)
            self._node_map.put(key, new_node)

    def remove(self, key):
        """
        키가 삭제되었거나 만료되었을 때 LRU 추적 구조에서 O(1)으로 제거합니다.
        """
        node = self._node_map.get(key)
        if node is not None:
            self._list.remove_node(node)
            self._node_map.remove(key)
            return True
        return False

    def pop_lru(self):
        """
        가장 오랫동안 사용되지 않은(Tail에 위치한) 키를 O(1)으로 추출하고 제거합니다.
        추출된 key를 반환하며, 비어있으면 None을 반환합니다.
        """
        if self._list.is_empty():
            return None

        lru_node = self._list.remove_back()
        if lru_node is not None:
            self._node_map.remove(lru_node.key)
            return lru_node.key
        return None

    def size(self):
        """현재 추적 중인 키 개수 반환"""
        return self._list.size()
