"""
NotebookLM용 단일 소스 텍스트 파일 빌더 스크립트 (scripts/build_notebooklm_source.py)
오직 실제 핵심 구현 소스 코드(2단 주석 포함)만을 순수하게 취합하여
Google NotebookLM 업로드용 NOTEBOOKLM_FULL_SOURCE.txt를 생성합니다.
(테스트 코드, 기획 문서, 프롬프트 가이드는 엄격히 제외)
"""

import os

# 프로젝트 루트 디렉토리
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(ROOT_DIR, "NOTEBOOKLM_FULL_SOURCE.txt")

# 수집 대상 핵심 프로덕션 소스 파일 순서
SOURCE_FILES = [
    "src/doubly_linked_list.py",
    "src/hash_map.py",
    "src/min_heap.py",
    "src/lru_cache.py",
    "src/memory_manager.py",
    "src/ttl_manager.py",
    "src/mini_redis.py",
    "src/cli.py",
    "main.py"
]


def build_notebooklm_source():
    """모든 핵심 프로덕션 소스코드를 단일 텍스트 파일로 합칩니다."""
    combined_content = []
    
    header = (
        "================================================================================\n"
        "  MINI REDIS : ZERO BUILT-IN COLLECTIONS CORE PRODUCTION SOURCE CODE\n"
        "  Total Production Modules: 9 Files (Pure Python 3.8+ From-Scratch Implementation)\n"
        "  Includes 2-Tier Comments: [1st Technical Specification] + [2nd Junior Daily Analogy]\n"
        "================================================================================\n\n"
    )
    combined_content.append(header)

    total_lines = 0

    for rel_path in SOURCE_FILES:
        abs_path = os.path.join(ROOT_DIR, rel_path)
        if not os.path.exists(abs_path):
            print(f"Warning: File not found: {abs_path}")
            continue

        with open(abs_path, "r", encoding="utf-8") as f:
            code = f.read()

        line_count = len(code.splitlines())
        total_lines += line_count

        file_banner = (
            f"\n\n{'#' * 80}\n"
            f"# FILE: {rel_path} (Lines: {line_count})\n"
            f"{'#' * 80}\n\n"
        )
        combined_content.append(file_banner)
        combined_content.append(code)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write("".join(combined_content))

    print(f"Successfully generated: {OUTPUT_FILE}")
    print(f"Total files: {len(SOURCE_FILES)} files | Total lines: {total_lines} lines")


if __name__ == "__main__":
    build_notebooklm_source()
