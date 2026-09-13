"""
freq.py

입력 데이터(바이트열)에서 각 바이트(0~255)의 등장 횟수를 세어
크기 256짜리 빈도 리스트를 반환한다.
"""


def build_freq_table(data: bytes):
   
    freqs = [0] * 256  # 0~255 바이트 값에 대한 카운트
    for b in data:
        freqs[b] += 1
    return freqs
