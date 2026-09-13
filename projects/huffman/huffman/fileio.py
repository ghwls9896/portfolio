"""
fileio.py

파일 단위로 허프만 압축/복원을 수행한다.

압축 파일 포맷 (이진 파일):
[헤더] + [압축된 데이터 바디]

헤더 구성:
- 256개의 uint32 (리틀엔디언) : 각 바이트 값(0~255)의 등장 빈도
- 1바이트 uint8              : 마지막 데이터 바이트에서 패딩 비트 수 (0~7)

바디:
- encode_data()로 생성된 압축된 비트 바이트열
"""

import struct
from .freq import build_freq_table
from .tree import build_huffman_tree, build_codes
from .codec import encode_data, decode_data

HEADER_FREQ_COUNT = 256
HEADER_FREQ_SIZE = 4      # uint32 → 4 bytes
HEADER_PADDING_SIZE = 1   # uint8  → 1 byte
HEADER_SIZE = HEADER_FREQ_COUNT * HEADER_FREQ_SIZE + HEADER_PADDING_SIZE


def compress_file(in_path, out_path):
    """
    in_path 경로의 파일을 허프만 코딩으로 압축하여 out_path 경로에 이진 파일로 저장한다.

    헤더에:
    - 문자 빈도표(허프만 테이블 정보)
    - 패딩 비트 수
    를 기록한다.

    return: (int, int, list[int])
        - original_size  : 원본 파일 크기(바이트)
        - compressed_size: 압축 파일 크기(바이트)
        - freqs          : 빈도표 (보고서/GUI용 추가 정보)
    """
    # 원본 파일 전체를 바이트로 읽는다.
    with open(in_path, "rb") as f:
        data = f.read()

    # 빈 파일인 경우: 빈도표는 전부 0, 패딩 0만 기록
    if not data:
        freqs = [0] * 256
        with open(out_path, "wb") as f:
            # 256개 빈도 기록
            for val in freqs:
                f.write(struct.pack("<I", val))  # 리틀엔디언 uint32
            # 패딩 비트 수 기록
            f.write(struct.pack("B", 0))        # uint8
        return 0, HEADER_SIZE, freqs

    # 1) 빈도표 생성
    freqs = build_freq_table(data)

    # 2) 허프만 트리 구성
    root = build_huffman_tree(freqs)

    # 3) 허프만 코드 생성 (바이트값 -> 비트 문자열)
    codes = build_codes(root)

    # 4) 실제 데이터 인코딩
    encoded_bytes, padding = encode_data(data, codes)

    # 5) 헤더 + 바디를 파일에 기록
    with open(out_path, "wb") as f:
        # (a) 빈도표: 256개의 uint32
        for val in freqs:
            f.write(struct.pack("<I", val))
        # (b) 패딩 비트 수: uint8
        f.write(struct.pack("B", padding))
        # (c) 압축된 비트 데이터
        f.write(encoded_bytes)

    original_size = len(data)
    compressed_size = HEADER_SIZE + len(encoded_bytes)
    return original_size, compressed_size, freqs


def decompress_file(in_path, out_path):
    """
    허프만 압축된 파일(in_path)을 읽어 허프만 트리를 복원한 뒤,
    원본 데이터를 out_path 경로에 복원한다.

    return: (int, int, list[int])
        - original_size  : 복원된 원본 데이터 크기(바이트)
        - compressed_size: 압축 파일 크기(바이트)
        - freqs          : 복원에 사용한 빈도표
    """
    with open(in_path, "rb") as f:
        header = f.read(HEADER_SIZE)
        if len(header) != HEADER_SIZE:
            raise ValueError("Invalid compressed file: header too short")

        # 1) 헤더에서 빈도표 256개 읽기
        freqs = []
        offset = 0
        for _ in range(HEADER_FREQ_COUNT):
            (val,) = struct.unpack_from("<I", header, offset)
            offset += HEADER_FREQ_SIZE
            freqs.append(val)

        # 2) 패딩 비트 수 (마지막 바이트에서 실제로 쓰이지 않는 비트 수)
        padding = header[HEADER_FREQ_COUNT * HEADER_FREQ_SIZE]

        # 3) 나머지는 전부 압축된 바디 데이터
        bit_bytes = f.read()

    total_symbols = sum(freqs)

    # 원본이 빈 파일이었던 경우
    if total_symbols == 0:
        with open(out_path, "wb") as f:
            f.write(b"")
        compressed_size = HEADER_SIZE
        return 0, compressed_size, freqs

    # 허프만 트리 재구성
    root = build_huffman_tree(freqs)

    # 비트열을 따라가며 복원
    decoded = decode_data(bit_bytes, padding, root, total_symbols)

    with open(out_path, "wb") as f:
        f.write(decoded)

    compressed_size = HEADER_SIZE + len(bit_bytes)
    original_size = len(decoded)
    return original_size, compressed_size, freqs
