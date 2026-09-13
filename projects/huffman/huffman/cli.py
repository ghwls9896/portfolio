"""
cli.py

명령행 인터페이스:
- 압축:  python main.py c <input.txt> <output.huf>
- 복원:  python main.py d <input.huf> <output.txt>
"""

import time
from .fileio import compress_file, decompress_file
from .stats import print_stats


def main(argv):
    """
    argv: list[str]
        sys.argv와 동일한 형식의 리스트

    return: int
        종료 코드 (0: 성공, 1: 사용법 오류 등)
    """
    if len(argv) < 4:
        print("Usage:")
        print("  Compress   : python main.py c <input.txt> <output.huf>")
        print("  Decompress : python main.py d <input.huf> <output.txt>")
        return 1

    mode = argv[1]
    in_path = argv[2]
    out_path = argv[3]

    if mode == "c":
        # 압축
        t0 = time.perf_counter()
        orig, comp, _ = compress_file(in_path, out_path)
        t1 = time.perf_counter()
        print_stats(orig, comp, t1 - t0, "Compression")
        return 0

    elif mode == "d":
        # 복원
        t0 = time.perf_counter()
        orig, comp, _ = decompress_file(in_path, out_path)
        t1 = time.perf_counter()
        print_stats(orig, comp, t1 - t0, "Decompression")
        return 0

    else:
        print("Unknown mode:", mode)
        print("Use 'c' for compress, 'd' for decompress.")
        return 1
