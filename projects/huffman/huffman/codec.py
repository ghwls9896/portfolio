"""
codec.py

허프만 코드(문자별 비트 문자열)를 이용해:
- 원본 데이터(바이트열)를 압축된 비트 바이트열로 인코딩
- 반대로 비트 바이트열을 원본 데이터로 디코딩
"""


def encode_data(data: bytes, codes):
    """
    주어진 데이터와 허프만 코드 딕셔너리를 이용해 압축된 바이트열을 만든다.

    data: bytes
        원본 데이터
    codes: dict[int, str]
        바이트 값 -> 허프만 코드 (예: 65 -> "0101")

    return: (bytes, int)
        - 첫 번째: 압축된 바이트열
        - 두 번째: 마지막 바이트에 채워넣은 패딩 비트 수 (0~7)
    """
    if not data:
        return b"", 0

    # 바이트들을 허프만 코드로 변환하여 하나의 긴 비트 문자열로 만든다.
    bitstring = "".join(codes[b] for b in data)

    out_bytes = bytearray()
    current = 0        # 현재 만들고 있는 1바이트
    bits_filled = 0    # current에 채워진 비트 수 (0~7)

    for bit in bitstring:
        current <<= 1             # 왼쪽으로 1비트 밀고
        if bit == "1":            # 새 비트를 LSB에 추가
            current |= 1
        bits_filled += 1

        if bits_filled == 8:
            # 바이트가 꽉 찼으면 결과에 추가
            out_bytes.append(current)
            current = 0
            bits_filled = 0

    # 마지막에 남은 비트가 있다면 패딩으로 채워서 1바이트로 만든다.
    padding = 0
    if bits_filled > 0:
        # 남은 비트 수만큼 왼쪽으로 밀어 상위 비트에 위치시킴
        current <<= (8 - bits_filled)
        padding = 8 - bits_filled
        out_bytes.append(current)

    return bytes(out_bytes), padding


def decode_data(bit_bytes: bytes, padding_bits: int, root, total_symbols: int):
    """
    압축된 비트 바이트열을 허프만 트리를 이용해 원본 데이터로 복원한다.

    bit_bytes: bytes
        압축된 비트 데이터 (바이트 단위)
    padding_bits: int
        마지막 바이트에서 실제로는 사용하지 않는 패딩 비트 수 (0~7)
    root:
        허프만 트리의 루트 노드
    total_symbols: int
        원본 데이터의 전체 문자(바이트) 개수

    return: bytes
        복원된 원본 데이터
    """
    if total_symbols == 0:
        return b""

    result = bytearray()
    node = root

    total_bits = len(bit_bytes) * 8 - padding_bits  # 실제 유효 비트 개수
    bit_index = 0

    for byte_val in bit_bytes:
        for i in range(8):
            if bit_index >= total_bits:
                break

            # MSB부터 차례대로 비트 추출
            bit = (byte_val >> (7 - i)) & 1
            node = node.left if bit == 0 else node.right

            # 리프 노드에 도달하면 원래 바이트 하나 복원
            if node.byte is not None:
                result.append(node.byte)
                node = root
                if len(result) == total_symbols:
                    return bytes(result)

            bit_index += 1

    return bytes(result)
