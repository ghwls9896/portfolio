"""
tree.py

허프만 트리(Huffman tree)를 구성하고,
각 리프 노드(문자)에 대해 허프만 코드를 생성한다.
"""

import heapq


class Node:
    """
    허프만 트리의 노드.

    속성:
    - freq : 이 노드를 루트로 하는 서브트리의 총 빈도수
    - byte : 리프 노드일 때 해당하는 바이트 값 (0~255), 내부 노드는 None
    - left : 왼쪽 자식 노드
    - right: 오른쪽 자식 노드
    """

    __slots__ = ("freq", "byte", "left", "right")

    def __init__(self, freq, byte=None, left=None, right=None):
        self.freq = freq
        self.byte = byte
        self.left = left
        self.right = right

    def __lt__(self, other):
        """
        heapq(최소 힙)에서 노드 간 비교 기준.
        빈도(freq)가 작은 것이 우선순위가 높다.
        """
        return self.freq < other.freq


def build_huffman_tree(freqs):
    """
    빈도표로부터 허프만 트리를 생성한다.

    freqs: list[int]
        길이 256, freqs[i] = 바이트 i의 등장 횟수

    return: Node | None
        허프만 트리의 루트 노드. 데이터가 비어 있으면 None.
    """
    heap = []

    # 각 바이트 값에 대해 등장 빈도가 1 이상이면 리프 노드를 만들어 힙에 넣는다.
    for byte_val, f in enumerate(freqs):
        if f > 0:
            heapq.heappush(heap, Node(f, byte=byte_val))

    # 데이터가 전혀 없을 경우
    if not heap:
        return None

    # 서로 다른 문자가 하나뿐인 경우(엣지 케이스):
    # 코드가 최소 1비트 이상 나오도록 부모 노드를 하나 만든다.
    if len(heap) == 1:
        only = heapq.heappop(heap)
        root = Node(only.freq, None, left=only, right=None)
        return root

    # 허프만 트리 생성 단계:
    # 가장 빈도 낮은 두 노드를 꺼내서 하나의 부모 노드로 합치고 다시 힙에 넣는다.
    # 힙에 노드가 1개 남을 때까지 반복.
    while len(heap) > 1:
        a = heapq.heappop(heap)
        b = heapq.heappop(heap)
        parent = Node(a.freq + b.freq, None, left=a, right=b)
        heapq.heappush(heap, parent)

    return heap[0]


def build_codes(root):
    codes = {}
    if root is None:
        return codes

    def dfs(node, prefix):
        """
        깊이 우선 탐색으로 리프까지 내려가며 코드 생성.
        왼쪽 자식 → '0', 오른쪽 자식 → '1'
        """
        if node is None:
            return

        # 리프 노드인 경우
        if node.byte is not None:
            if prefix == "":
                # 서로 다른 문자가 하나뿐일 때, 코드가 최소 1비트는 되도록 "0"을 할당
                codes[node.byte] = "0"
            else:
                codes[node.byte] = prefix
            return

        # 왼쪽 / 오른쪽으로 내려가며 '0' / '1' 추가
        dfs(node.left, prefix + "0")
        dfs(node.right, prefix + "1")

    dfs(root, "")
    return codes
