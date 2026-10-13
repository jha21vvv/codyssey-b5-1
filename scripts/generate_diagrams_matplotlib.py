"""
고해상도 아키텍처 다이어그램 자동 생성 스크립트 (scripts/generate_diagrams_matplotlib.py)
matplotlib을 사용하여 Mini Redis의 핵심 아키텍처와 자료구조 원리를 시각화합니다.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# 출력 디렉토리
DIAGRAMS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "diagrams")
os.makedirs(DIAGRAMS_DIR, exist_ok=True)

# 공통 스타일 설정
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#CCCCCC'


def generate_architecture_diagram():
    """1. 전체 Mini Redis 시스템 아키텍처 다이어그램"""
    fig, ax = plt.subplots(figsize=(12, 7), dpi=300)
    ax.set_facecolor("#0F172A")
    fig.patch.set_facecolor("#0F172A")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # 제목
    ax.text(50, 94, "Mini Redis System Architecture", fontsize=18, fontweight="bold",
            color="#38BDF8", ha="center")
    ax.text(50, 89, "Zero Built-in Collections (dict/set/collections free)", fontsize=11,
            color="#94A3B8", ha="center", style="italic")

    # 1. CLI Layer
    rect_cli = patches.FancyBboxPatch((15, 74), 70, 9, boxstyle="round,pad=1",
                                      facecolor="#1E293B", edgecolor="#38BDF8", linewidth=2)
    ax.add_patch(rect_cli)
    ax.text(50, 78.5, "CLI REPL (src/cli.py) : mini-redis> [shlex parsing]",
            fontsize=12, fontweight="bold", color="#F8FAFC", ha="center")

    # Arrow Down
    ax.annotate('', xy=(50, 64), xytext=(50, 74),
                arrowprops=dict(facecolor='#38BDF8', edgecolor='#38BDF8', arrowstyle="->", lw=2.5))

    # 2. Core Engine
    rect_core = patches.FancyBboxPatch((10, 52), 80, 11, boxstyle="round,pad=1",
                                       facecolor="#1E293B", edgecolor="#F59E0B", linewidth=2)
    ax.add_patch(rect_core)
    ax.text(50, 58.5, "MiniRedis Core Engine (src/mini_redis.py)",
            fontsize=13, fontweight="bold", color="#FBBF24", ha="center")
    ax.text(50, 54.5, "Command Routing: SET | GET | DEL | EXISTS | DBSIZE | KEYS | CONFIG | INFO | EXPIRE | TTL",
            fontsize=9.5, color="#CBD5E1", ha="center")

    # 4 Modules Boxes
    modules = [
        ("Primary Storage", "HashMap\n(src/hash_map.py)\nChaining Buckets", 7, "#10B981"),
        ("LRU Manager", "LRUManager\n(src/lru_cache.py)\nDoublyLinkedList + Map", 29, "#6366F1"),
        ("TTL Manager", "TTLManager\n(src/ttl_manager.py)\nMinHeap + Map", 51, "#EC4899"),
        ("Memory Manager", "MemoryManager\n(src/memory_manager.py)\nUTF-8 Byte Eviction", 73, "#EF4444")
    ]

    for title, desc, x_pos, color in modules:
        rect = patches.FancyBboxPatch((x_pos, 20), 20, 24, boxstyle="round,pad=0.8",
                                      facecolor="#1E293B", edgecolor=color, linewidth=2)
        ax.add_patch(rect)
        ax.text(x_pos + 10, 39, title, fontsize=10.5, fontweight="bold", color=color, ha="center")
        ax.text(x_pos + 10, 29, desc, fontsize=8.5, color="#E2E8F0", ha="center")

        # Arrow from core
        ax.annotate('', xy=(x_pos + 10, 44), xytext=(x_pos + 10, 52),
                    arrowprops=dict(facecolor=color, edgecolor=color, arrowstyle="->", lw=1.8))

    # Bottom Footer
    ax.text(50, 8, "Self-Contained Data Structures: DoublyLinkedList | HashMap | MinHeap",
            fontsize=10.5, color="#64748B", ha="center")

    output_path = os.path.join(DIAGRAMS_DIR, "01_system_architecture.png")
    plt.tight_layout()
    plt.savefig(output_path, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Generated: {output_path}")


def generate_hashmap_chaining_diagram():
    """2. 체이닝 해시맵 & 리사이징 다이어그램"""
    fig, ax = plt.subplots(figsize=(12, 7), dpi=300)
    ax.set_facecolor("#0F172A")
    fig.patch.set_facecolor("#0F172A")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    ax.text(50, 93, "HashMap Architecture : djb2 Hash & Chaining", fontsize=17,
            fontweight="bold", color="#38BDF8", ha="center")
    ax.text(50, 88, "DoublyLinkedList Buckets + Load Factor 0.75 Resizing", fontsize=10.5,
            color="#94A3B8", ha="center")

    # Hash Function Box
    rect_hash = patches.FancyBboxPatch((6, 68), 24, 12, boxstyle="round,pad=0.8",
                                       facecolor="#1E293B", edgecolor="#38BDF8", linewidth=1.5)
    ax.add_patch(rect_hash)
    ax.text(18, 76, "djb2 Hash Function", fontsize=10, fontweight="bold", color="#38BDF8", ha="center")
    ax.text(18, 71, "h = (h * 33 + ord(c))\nidx = h % Capacity", fontsize=8.5, color="#E2E8F0", ha="center")

    # Arrow to buckets
    ax.annotate('', xy=(34, 74), xytext=(30, 74),
                arrowprops=dict(facecolor='#38BDF8', edgecolor='#38BDF8', arrowstyle="->", lw=2))

    # Buckets Table
    buckets = ["Bucket 0", "Bucket 1", "Bucket 2", "Bucket 3", "Bucket ...", f"Bucket {15}"]
    y_start = 78
    for i, b_name in enumerate(buckets):
        y = y_start - (i * 10)
        rect_b = patches.FancyBboxPatch((35, y), 16, 7, boxstyle="square,pad=0.2",
                                        facecolor="#334155", edgecolor="#64748B", linewidth=1)
        ax.add_patch(rect_b)
        ax.text(43, y + 3.5, b_name, fontsize=8.5, color="#F8FAFC", ha="center", va="center")

        # Bucket 1 chain
        if i == 1:
            ax.annotate('', xy=(56, y + 3.5), xytext=(51, y + 3.5),
                        arrowprops=dict(facecolor='#10B981', edgecolor='#10B981', arrowstyle="->", lw=2))
            
            # Node 1
            n1 = patches.FancyBboxPatch((56, y), 17, 7, boxstyle="round,pad=0.4",
                                        facecolor="#1E293B", edgecolor="#10B981", linewidth=1.5)
            ax.add_patch(n1)
            ax.text(64.5, y + 3.5, "Node(k1, v1)", fontsize=8, color="#A7F3D0", ha="center", va="center")

            ax.annotate('', xy=(78, y + 3.5), xytext=(73, y + 3.5),
                        arrowprops=dict(facecolor='#10B981', edgecolor='#10B981', arrowstyle="<->", lw=1.5))

            # Node 2 (collision)
            n2 = patches.FancyBboxPatch((78, y), 17, 7, boxstyle="round,pad=0.4",
                                        facecolor="#1E293B", edgecolor="#10B981", linewidth=1.5)
            ax.add_patch(n2)
            ax.text(86.5, y + 3.5, "Node(k9, v9)", fontsize=8, color="#A7F3D0", ha="center", va="center")

        # Bucket 3 chain
        if i == 3:
            ax.annotate('', xy=(56, y + 3.5), xytext=(51, y + 3.5),
                        arrowprops=dict(facecolor='#10B981', edgecolor='#10B981', arrowstyle="->", lw=2))
            n3 = patches.FancyBboxPatch((56, y), 17, 7, boxstyle="round,pad=0.4",
                                        facecolor="#1E293B", edgecolor="#10B981", linewidth=1.5)
            ax.add_patch(n3)
            ax.text(64.5, y + 3.5, "Node(k3, v3)", fontsize=8, color="#A7F3D0", ha="center", va="center")

    # Resizing Callout Box
    rect_callout = patches.FancyBboxPatch((8, 18), 84, 9, boxstyle="round,pad=0.8",
                                         facecolor="#1E293B", edgecolor="#F59E0B", linewidth=1.5)
    ax.add_patch(rect_callout)
    ax.text(50, 24, "Dynamic 2x Resizing Threshold: (size / capacity) > 0.75",
            fontsize=10.5, fontweight="bold", color="#FBBF24", ha="center")
    ax.text(50, 20, "Rehashing guarantees O(1) average lookup time by doubling buckets (16 -> 32 -> 64)",
            fontsize=9, color="#CBD5E1", ha="center")

    output_path = os.path.join(DIAGRAMS_DIR, "02_hashmap_chaining.png")
    plt.tight_layout()
    plt.savefig(output_path, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Generated: {output_path}")


def generate_lru_mechanism_diagram():
    """3. LRU 캐시 및 방출 메커니즘 다이어그램"""
    fig, ax = plt.subplots(figsize=(12, 7), dpi=300)
    ax.set_facecolor("#0F172A")
    fig.patch.set_facecolor("#0F172A")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    ax.text(50, 93, "O(1) LRU Tracking & Memory Eviction", fontsize=17,
            fontweight="bold", color="#38BDF8", ha="center")
    ax.text(50, 88, "DoublyLinkedList (Order) + HashMap (O(1) Direct Pointer Reference)",
            fontsize=10.5, color="#94A3B8", ha="center")

    # Node Map Box (Top)
    rect_map = patches.FancyBboxPatch((15, 68), 70, 14, boxstyle="round,pad=0.8",
                                      facecolor="#1E293B", edgecolor="#6366F1", linewidth=1.8)
    ax.add_patch(rect_map)
    ax.text(50, 78, "HashMap Node Pointers (key -> Node ref)", fontsize=11,
            fontweight="bold", color="#A5B4FC", ha="center")
    ax.text(50, 72, "key1 -> ref(Node1)  |  key2 -> ref(Node2)  |  key3 -> ref(Node3)",
            fontsize=9.5, color="#E2E8F0", ha="center")

    # DLL nodes (Bottom)
    # Head Sentinel -> Node 1 (MRU) -> Node 2 -> Node 3 (LRU) -> Tail Sentinel
    nodes_info = [
        ("HEAD", 10, "#475569", "Dummy Head"),
        ("Node 1 (k1)\n[MRU]", 27, "#10B981", "Most Recently Used"),
        ("Node 2 (k2)", 49, "#38BDF8", "Intermediate"),
        ("Node 3 (k3)\n[LRU]", 68, "#EF4444", "Least Recently Used"),
        ("TAIL", 88, "#475569", "Dummy Tail")
    ]

    for label, x_pos, border_col, sub in nodes_info:
        r = patches.FancyBboxPatch((x_pos, 35), 14, 15, boxstyle="round,pad=0.5",
                                   facecolor="#1E293B", edgecolor=border_col, linewidth=2)
        ax.add_patch(r)
        ax.text(x_pos + 7, 43, label, fontsize=8.5, fontweight="bold",
                color="#FFFFFF", ha="center", va="center")
        ax.text(x_pos + 7, 29, sub, fontsize=7, color="#94A3B8", ha="center")

    # Connect Nodes with bidirectional arrows
    pairs = [(24, 27), (41, 49), (63, 68), (82, 88)]
    for start_x, end_x in pairs:
        ax.annotate('', xy=(end_x, 42.5), xytext=(start_x, 42.5),
                    arrowprops=dict(facecolor='#94A3B8', edgecolor='#94A3B8', arrowstyle="<->", lw=1.5))

    # Pointer from HashMap to Node 2 (Move to Front Demo)
    ax.annotate('', xy=(56, 50), xytext=(50, 68),
                arrowprops=dict(facecolor='#F59E0B', edgecolor='#F59E0B', arrowstyle="->", lw=2, linestyle="--"))
    ax.text(60, 59, "GET k2 -> O(1) move_to_front()", fontsize=9, color="#FBBF24")

    # Eviction Alert Box
    rect_evict = patches.FancyBboxPatch((15, 10), 70, 11, boxstyle="round,pad=0.6",
                                        facecolor="#1E293B", edgecolor="#EF4444", linewidth=1.5)
    ax.add_patch(rect_evict)
    ax.text(50, 17.5, "When used_memory > maxmemory: O(1) remove_back() Evicts LRU Node 3",
            fontsize=10.5, fontweight="bold", color="#F87171", ha="center")
    ax.text(50, 13.5, "evicted_keys += 1  |  Storage & TTL cleanly detached without full table scan",
            fontsize=9, color="#CBD5E1", ha="center")

    output_path = os.path.join(DIAGRAMS_DIR, "03_lru_mechanism.png")
    plt.tight_layout()
    plt.savefig(output_path, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Generated: {output_path}")


def generate_ttl_minheap_diagram():
    """4. MinHeap 기반 TTL 관리 및 수명주기 다이어그램"""
    fig, ax = plt.subplots(figsize=(12, 7), dpi=300)
    ax.set_facecolor("#0F172A")
    fig.patch.set_facecolor("#0F172A")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    ax.text(50, 93, "MinHeap TTL Expiration & Lazy Deletion Lifecycle",
            fontsize=17, fontweight="bold", color="#38BDF8", ha="center")
    ax.text(50, 88, "O(1) Earliest Expiry Peek + O(log N) Push/Pop Heap Properties",
            fontsize=10.5, color="#94A3B8", ha="center")

    # Binary Tree Representation
    # Root: (t=100, k1)
    # Left: (t=150, k2), Right: (t=200, k3)
    tree_nodes = [
        ("(t=100, k1)\n[Root : Soonest]", 50, 68, "#EF4444"),
        ("(t=150, k2)", 30, 48, "#F59E0B"),
        ("(t=200, k3)", 70, 48, "#10B981"),
        ("(t=300, k4)", 20, 30, "#38BDF8"),
        ("(t=250, k5)", 40, 30, "#38BDF8")
    ]

    for label, x, y, border_col in tree_nodes:
        r = patches.FancyBboxPatch((x - 9, y - 5), 18, 10, boxstyle="round,pad=0.4",
                                   facecolor="#1E293B", edgecolor=border_col, linewidth=1.8)
        ax.add_patch(r)
        ax.text(x, y, label, fontsize=8, color="#FFFFFF", ha="center", va="center")

    # Tree edges
    edges = [((50, 63), (30, 53)), ((50, 63), (70, 53)),
             ((30, 43), (20, 35)), ((30, 43), (40, 35))]
    for start, end in edges:
        ax.plot([start[0], end[0]], [start[1], end[1]], color="#64748B", lw=1.5, zorder=0)

    # Explanation Column (Right/Bottom)
    rect_box = patches.FancyBboxPatch((10, 8), 80, 14, boxstyle="round,pad=0.6",
                                      facecolor="#1E293B", edgecolor="#38BDF8", linewidth=1.5)
    ax.add_patch(rect_box)
    ax.text(50, 18, "Dual Deletion Strategy : Lazy Check + Active Heap Scrubbing",
            fontsize=10.5, fontweight="bold", color="#38BDF8", ha="center")
    ax.text(50, 14, "1. Lazy Deletion: On GET/EXISTS, if now >= expire_at -> instant purge & return (nil)\n"
                    "2. Active Cleanup: On DBSIZE/KEYS, heap peek & pop all expired entries (O(k log N))\n"
                    "3. Stale Invalidation: If key updated by SET -> expire_map cleared -> stale heap pop bypassed",
            fontsize=8.5, color="#E2E8F0", ha="center")

    output_path = os.path.join(DIAGRAMS_DIR, "04_ttl_minheap_lifecycle.png")
    plt.tight_layout()
    plt.savefig(output_path, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Generated: {output_path}")


if __name__ == "__main__":
    generate_architecture_diagram()
    generate_hashmap_chaining_diagram()
    generate_lru_mechanism_diagram()
    generate_ttl_minheap_diagram()
    print("All 4 architecture diagrams successfully generated in diagrams/!")
