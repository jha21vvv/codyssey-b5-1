"""
최소 힙 (Min Heap) 모듈
dict, set, collections 없이 동적 배열(list)을 완전 이진 트리 구조로 사용하여 구현합니다.
TTL 만료 관리를 위한 (expire_at, key) 형태의 요소를 효율적으로 처리합니다.
"""

class MinHeap:
    """
    최소 힙 (Min-Heap)
    - 주요 메서드: push, pop, peek, size
    - 내부 복원 알고리즘: _heapify_up, _heapify_down
    """
    def __init__(self):
        self._data = []

    def push(self, item):
        """
        새 요소를 힙에 삽입하고 상향 힙 복원(_heapify_up)을 수행합니다.
        시간 복잡도: O(log N)
        """
        self._data.append(item)
        self._heapify_up(len(self._data) - 1)

    def pop(self):
        """
        최솟값(루트 노드)을 제거하고 반환합니다.
        힙이 비어있으면 None을 반환합니다.
        시간 복잡도: O(log N)
        """
        if self.is_empty():
            return None

        if len(self._data) == 1:
            return self._data.pop()

        root = self._data[0]
        self._data[0] = self._data.pop()
        self._heapify_down(0)
        return root

    def peek(self):
        """
        최솟값(루트 노드)을 제거하지 않고 확인합니다.
        힙이 비어있으면 None을 반환합니다.
        시간 복잡도: O(1)
        """
        if self.is_empty():
            return None
        return self._data[0]

    def size(self):
        """힙에 저장된 총 요소 개수를 반환합니다."""
        return len(self._data)

    def is_empty(self):
        """힙이 비어있는지 확인합니다."""
        return len(self._data) == 0

    def _heapify_up(self, index):
        """
        새로 삽입된 요소를 부모와 비교하며 적절한 위치까지 위로 끌어올립니다.
        부모 인덱스: (index - 1) // 2
        """
        while index > 0:
            parent_idx = (index - 1) // 2
            if self._data[index] < self._data[parent_idx]:
                self._data[index], self._data[parent_idx] = self._data[parent_idx], self._data[index]
                index = parent_idx
            else:
                break

    def _heapify_down(self, index):
        """
        루트 또는 특정 위치의 요소를 자식들과 비교하며 적절한 위치까지 아래로 내립니다.
        좌측 자식: 2 * index + 1
        우측 자식: 2 * index + 2
        """
        length = len(self._data)
        while True:
            left_child_idx = 2 * index + 1
            right_child_idx = 2 * index + 2
            smallest_idx = index

            if left_child_idx < length and self._data[left_child_idx] < self._data[smallest_idx]:
                smallest_idx = left_child_idx

            if right_child_idx < length and self._data[right_child_idx] < self._data[smallest_idx]:
                smallest_idx = right_child_idx

            if smallest_idx != index:
                self._data[index], self._data[smallest_idx] = self._data[smallest_idx], self._data[index]
                index = smallest_idx
            else:
                break
