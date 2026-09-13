"""
stats.py

압축 전/후 크기와 시간으로부터
- 압축률
- 문자당 평균 비트 수
를 계산하고 출력하는 기능을 제공한다.
"""


def compute_stats(original_size, compressed_size):
    """
    original_size: int
        압축 전 데이터 크기 (바이트)
    compressed_size: int
        압축 후 데이터 크기 (바이트)

    return: dict
        - compression_ratio : 1 - (압축후 / 압축전)
        - avg_bits_per_char : 문자당 평균 비트 수
    """
    if original_size == 0:
        return {
            "compression_ratio": 0.0,
            "avg_bits_per_char": 0.0,
        }

    compression_ratio = 1.0 - (compressed_size / original_size)
    avg_bits_per_char = (compressed_size * 8.0) / original_size

    return {
        "compression_ratio": compression_ratio,
        "avg_bits_per_char": avg_bits_per_char,
    }


def print_stats(original_size, compressed_size, elapsed, mode_desc):
    """
    CLI 모드에서 압축 / 복원 결과를 터미널에 출력한다.

    elapsed: float
        경과 시간 (초)
    mode_desc: str
        "Compression" 또는 "Decompression" 등 설명 문자열
    """
    if original_size == 0:
        print(f"{mode_desc}: empty file")
        return

    stats = compute_stats(original_size, compressed_size)
    print(f"{mode_desc}:")
    print(f"  original size       : {original_size} bytes")
    print(f"  compressed size     : {compressed_size} bytes")
    print(f"  compression         : {stats['compression_ratio'] * 100:.2f}%")
    print(f"  avg bits per char   : {stats['avg_bits_per_char']:.3f} bits")
    print(f"  elapsed time        : {elapsed * 1000:.2f} ms")
