"""
Huffman coding package.

모듈 구성:
- freq.py    : 입력 데이터에서 문자(바이트) 빈도 계산
- tree.py    : 허프만 트리 및 코드 생성
- codec.py   : 허프만 코드 기반 인코딩/디코딩
- fileio.py  : 파일 단위 압축/복원 (헤더 + 데이터)
- stats.py   : 압축률, 평균 비트 수 등 통계 계산
- cli.py     : 명령행 인터페이스
- gui.py     : Tkinter 기반 GUI
"""