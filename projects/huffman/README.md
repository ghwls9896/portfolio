# Huffman · 바이트 단위 무손실 압축

문자 빈도에서 이진 트리를 만들고, 자주 등장하는 바이트에 짧은 비트 코드를 배정하는 학습 프로젝트입니다. 실제 GUI는 **Tkinter**입니다.

## 실행
Python 3.10 이상과 Tkinter를 사용합니다. 프로젝트 폴더에서 실행합니다.
```bash
python main.py
python main.py c samples/example_korean.txt sample.huf
python main.py d sample.huf restored.txt
```
## 구조와 흐름
`freq.py` → `tree.py` → `codec.py` → `fileio.py` 순서로 빈도 계산, 코드 생성, 비트 인코딩, 파일 저장을 나눴습니다. `cli.py`와 `gui.py`는 동일한 압축 로직을 사용합니다.

파일 헤더는 256개 uint32 빈도와 패딩 길이 1바이트로 **1,025바이트**입니다. 따라서 작은 파일은 압축 후 더 커질 수 있습니다. 압축률을 판단할 때 본문뿐 아니라 헤더도 포함해야 합니다.

## 범위
파일 전체와 비트 문자열을 메모리에 보관하므로 대용량 스트리밍 압축용은 아닙니다. 손상된 입력에 대한 포괄적 검증은 후속 개선 항목입니다.

[노션 설명](https://app.notion.com/p/2bc1b45f6f078057ad93e2354077d3e8)
