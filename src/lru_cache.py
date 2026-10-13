# [1차]: LRU 캐시 매니저 모듈을 정의합니다.
# [2차]: 최근에 본 책은 책상 맨 위에 올려두고 가장 오래 안 본 책은 밑바닥으로 보내는 독서대를 만듭니다.
"""
LRU 추적 관리자 (LRU Cache Manager) 모듈
DoublyLinkedList와 자체 HashMap을 결합하여 O(1) 시간 복잡도로 키 접근 추적 및 최하위(LRU) 키 방출을 수행합니다.
dict, set, collections는 일절 사용하지 않습니다.
"""

# [1차]: O(1) 순서 재배치를 위한 DoublyLinkedList 및 Node 클래스를 가져옵니다.
# [2차]: 책들을 엮어둘 양방향 기차 대형 부품들을 챙겨옵니다.
from src.doubly_linked_list import DoublyLinkedList, Node
# [1차]: O(1) 키 탐색을 위한 자체 HashMap 클래스를 가져옵니다.
# [2차]: 책 이름표를 보고 즉시 책 위치를 찍어줄 번호표 수납장을 가져옵니다.
from src.hash_map import HashMap


# [1차]: LRUManager 클래스를 정의합니다.
# [2차]: 가장 오래 안 쓴 물건을 칼같이 골라내는 스마트 독서대 관리인입니다.
class LRUManager:
    """
    O(1) LRU(Least Recently Used) 추적 관리자
    - 최근 접근된 키는 리스트의 Head 쪽에 위치
    - 가장 오랫동안 접근되지 않은 키는 리스트의 Tail 쪽에 위치
    - 자체 HashMap(key -> Node)을 통해 O(1) 노드 탐색 및 위치 갱신
    """
    # [1차]: LRUManager 인스턴스를 초기화하고 리스트와 노드 맵을 생성합니다.
    # [2차]: 순서를 기억할 트랙(리스트)과 책 위치를 적어둘 장부(해시맵)를 준비합니다.
    def __init__(self):
        # [1차]: 접근 순서를 기록하는 DoublyLinkedList 인스턴스를 할당합니다.
        # [2차]: 최근 순서대로 책을 꽂아둘 양방향 책꽂이를 놓습니다.
        self._list = DoublyLinkedList()
        # [1차]: key에서 Node 객체 참조를 매핑하는 HashMap 인스턴스를 할당합니다.
        # [2차]: "이 책이 책꽂이 몇 번째 칸에 꽂혀 있는지" 적어둔 색인 장부를 엽니다.
        self._node_map = HashMap()

    # [1차]: 특정 키에 대한 접근(Read/Write)을 기록하고 해당 노드를 맨 앞으로 이동시킵니다.
    # [2차]: 손님이 책을 읽거나 새로 사 오면, 그 책을 책꽂이 맨 앞자리(1등석)로 옮깁니다.
    def access(self, key):
        """
        키에 접근(조회 또는 갱신/추가)했을 때 해당 키를 가장 최근(Head)으로 갱신합니다.
        O(1) 연산
        """
        # [1차]: HashMap에서 해당 키에 대응하는 기존 Node 참조를 O(1)으로 조회합니다.
        # [2차]: 색인 장부를 보고 이 책이 이미 책꽂이에 꽂혀 있는지 확인합니다.
        existing_node = self._node_map.get(key)
        # [1차]: 기존 노드가 존재하는 경우 분기합니다.
        # [2차]: 이미 책꽂이에 꽂혀 있던 책인 경우입니다.
        if existing_node is not None:
            # [1차]: DoublyLinkedList의 move_to_front를 호출하여 O(1)으로 헤드 바로 뒤로 이동합니다.
            # [2차]: 책꽂이 중간에서 그 책을 쏙 빼서 맨 앞자리로 탁 꽂아 넣습니다.
            self._list.move_to_front(existing_node)
        else:
            # [1차]: 신규 키인 경우 새 Node를 생성합니다.
            # [2차]: 오늘 서점에서 처음 사 온 새 책인 경우입니다.
            new_node = Node(key=key, value=None, data=key)
            # [1차]: 리스트의 맨 앞에 새 노드를 O(1)으로 삽입합니다.
            # [2차]: 책꽂이 맨 앞 1등 자리에 새 책을 꽂습니다.
            self._list.insert_front(new_node)
            # [1차]: HashMap에 key -> new_node 매핑을 등록합니다.
            # [2차]: 색인 장부에 "이 새 책은 여기에 있어요" 하고 위치를 적어둡니다.
            self._node_map.put(key, new_node)

    # [1차]: 키가 삭제되거나 만료되었을 때 LRU 추적 구조에서 O(1)으로 제거합니다.
    # [2차]: 책을 버리거나 분실했을 때 책꽂이와 색인 장부에서 깨끗이 지웁니다.
    def remove(self, key):
        """
        키가 삭제되었거나 만료되었을 때 LRU 추적 구조에서 O(1)으로 제거합니다.
        """
        # [1차]: HashMap에서 해당 키의 Node를 조회합니다.
        # [2차]: 색인 장부에서 책 위치를 찾습니다.
        node = self._node_map.get(key)
        # [1차]: 노드가 존재하면 리스트와 맵에서 동시에 제거합니다.
        # [2차]: 책이 실제로 꽂혀 있다면 제거 절차를 밟습니다.
        if node is not None:
            # [1차]: 연결 리스트에서 해당 노드를 O(1)으로 분리합니다.
            # [2차]: 책꽂이에서 그 책을 쏙 빼냅니다.
            self._list.remove_node(node)
            # [1차]: HashMap에서 해당 키의 매핑을 제거합니다.
            # [2차]: 색인 장부에서 해당 책 이름을 지웁니다.
            self._node_map.remove(key)
            # [1차]: 성공을 의미하는 True를 반환합니다.
            # [2차]: 잘 치웠다고 보고합니다.
            return True
        # [1차]: 키가 없으면 False를 반환합니다.
        # [2차]: 원래 없던 책이니 지울 게 없다고 보고합니다.
        return False

    # [1차]: 가장 오랫동안 접근되지 않은(리스트 tail 바로 앞) 노드를 O(1)으로 꺼내어 제거하고 key를 반환합니다.
    # [2차]: 책꽂이 맨 밑바닥에 먼지 쌓인 가장 오래된 책을 1초 만에 꺼내어 버립니다.
    def pop_lru(self):
        """
        가장 오랫동안 사용되지 않은(Tail에 위치한) 키를 O(1)으로 추출하고 제거합니다.
        추출된 key를 반환하며, 비어있으면 None을 반환합니다.
        """
        # [1차]: 리스트가 비어있는지 확인합니다.
        # [2차]: 책꽂이에 책이 한 권도 없는지 봅니다.
        if self._list.is_empty():
            # [1차]: 비어있으면 None을 반환합니다.
            # [2차]: 버릴 책이 없으니 빈손으로 돌아옵니다.
            return None

        # [1차]: 리스트의 맨 뒤 유효 노드를 remove_back으로 O(1) 제거합니다.
        # [2차]: 책꽂이 맨 꼴찌 자리에 꽂혀 있던 가장 오래된 책을 뺍니다.
        lru_node = self._list.remove_back()
        # [1차]: 제거된 노드가 존재하면 HashMap에서도 키를 정리하고 key를 반환합니다.
        # [2차]: 꺼낸 책이 있다면 장부에서도 지우고 그 책 이름을 알려줍니다.
        if lru_node is not None:
            # [1차]: HashMap에서 해당 노드의 key 매핑을 제거합니다.
            # [2차]: 색인 장부에서 그 책의 이름을 지웁니다.
            self._node_map.remove(lru_node.key)
            # [1차]: 방출된 노드의 key를 반환합니다.
            # [2차]: "이 책을 방출했습니다" 하고 책 이름을 알려줍니다.
            return lru_node.key
        # [1차]: 비정상 상태 시 None을 반환합니다.
        # [2차]: 아무것도 못 꺼냈으면 빈손으로 끝냅니다.
        return None

    # [1차]: 현재 LRU 추적 중인 총 키 개수를 반환합니다.
    # [2차]: 현재 책꽂이에 꽂혀 있는 책이 총 몇 권인지 세어줍니다.
    def size(self):
        """현재 추적 중인 키 개수 반환"""
        # [1차]: 내부 리스트의 size를 반환합니다.
        # [2차]: 책꽂이의 책 권수를 알려줍니다.
        return self._list.size()
