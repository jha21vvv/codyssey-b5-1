"""
체이닝 기반 해시맵 (Chaining Hash Map) 모듈
dict, set, collections 없이 DoublyLinkedList를 버킷 체이닝으로 사용하여 구현합니다.
로드 팩터 0.75 초과 시 버킷을 2배 확장(Rehashing)합니다.
"""

from src.doubly_linked_list import DoublyLinkedList, Node


class HashMap:
    """
    체이닝(Chaining) 방식 해시맵
    - 충돌 해결: DoublyLinkedList 체이닝
    - 해시 함수: djb2 기반 고분산 해시 알고리즘
    - 동적 리사이징: 로드 팩터 > 0.75 시 2배 확장
    """
    DEFAULT_CAPACITY = 16
    MAX_LOAD_FACTOR = 0.75

    def __init__(self, initial_capacity=DEFAULT_CAPACITY):
        self._capacity = max(initial_capacity, 4)
        self._size = 0
        self._buckets = [DoublyLinkedList() for _ in range(self._capacity)]

    def _hash(self, key):
        """
        직접 설계한 djb2 기반 해시 함수
        소수 5381과 비트 시프트 연산(h * 33 + ord(c))을 통해 균등한 해시 분포를 보장합니다.
        """
        key_str = str(key)
        h = 5381
        for char in key_str:
            h = (((h << 5) + h) + ord(char)) & 0x7FFFFFFF
        return h

    def _get_bucket_index(self, key):
        """해시값을 현재 버킷 크기로 모듈러 연산하여 인덱스 계산"""
        return self._hash(key) % self._capacity

    def put(self, key, value):
        """
        키와 값을 해시맵에 저장합니다.
        이미 키가 존재하면 값을 덮어씁니다.
        저장 후 로드 팩터가 0.75를 초과하면 버킷을 2배 확장합니다.
        """
        idx = self._get_bucket_index(key)
        bucket = self._buckets[idx]

        for node in bucket:
            if node.key == key:
                old_val = node.value
                node.value = value
                node.data = (key, value)
                return old_val

        new_node = Node(key=key, value=value, data=(key, value))
        bucket.insert_back(new_node)
        self._size += 1

        if (self._size / self._capacity) > self.MAX_LOAD_FACTOR:
            self._resize(self._capacity * 2)

        return None

    def get(self, key):
        """
        키에 해당하는 값을 조회합니다.
        키가 존재하지 않으면 None을 반환합니다.
        """
        idx = self._get_bucket_index(key)
        bucket = self._buckets[idx]

        for node in bucket:
            if node.key == key:
                return node.value
        return None

    def get_node(self, key):
        """
        키에 해당하는 노드 참조 자체를 조회합니다 (LRU 등 내부 연동용).
        """
        idx = self._get_bucket_index(key)
        bucket = self._buckets[idx]

        for node in bucket:
            if node.key == key:
                return node
        return None

    def remove(self, key):
        """
        키에 해당하는 항목을 삭제하고 기존 값을 반환합니다.
        존재하지 않으면 None을 반환합니다.
        """
        idx = self._get_bucket_index(key)
        bucket = self._buckets[idx]

        for node in bucket:
            if node.key == key:
                val = node.value
                bucket.remove_node(node)
                self._size -= 1
                return val
        return None

    def contains(self, key):
        """키 존재 여부를 반환합니다 (True/False)."""
        return self.get(key) is not None or self._key_exists(key)

    def _key_exists(self, key):
        """값이 None인 경우에도 키 존재 여부를 판별하기 위한 헬퍼"""
        idx = self._get_bucket_index(key)
        bucket = self._buckets[idx]
        for node in bucket:
            if node.key == key:
                return True
        return False

    def keys(self):
        """저장된 모든 키의 목록을 일반 파이썬 리스트로 반환합니다."""
        all_keys = []
        for bucket in self._buckets:
            for node in bucket:
                all_keys.append(node.key)
        return all_keys

    def size(self):
        """저장된 고유 키의 총 개수를 반환합니다."""
        return self._size

    def capacity(self):
        """현재 버킷 배열의 크기를 반환합니다."""
        return self._capacity

    def load_factor(self):
        """현재 해시맵의 로드 팩터를 반환합니다."""
        return self._size / self._capacity

    def _resize(self, new_capacity):
        """
        버킷 크기를 변경하고 모든 기존 항목을 재해싱(Rehashing)하여 재배치합니다.
        """
        old_buckets = self._buckets
        self._capacity = new_capacity
        self._buckets = [DoublyLinkedList() for _ in range(self._capacity)]
        self._size = 0

        for bucket in old_buckets:
            for node in bucket:
                self.put(node.key, node.value)
