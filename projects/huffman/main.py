import sys
from huffman.cli import main as cli_main
from huffman.gui import run_gui


if __name__ == "__main__":
    """
    프로그램 진입점.

    - 인자가 주어지고, 첫 번째 인자가 'c' 또는 'd'이면:
      → CLI 모드로 실행 (압축 / 복원)
    - 그 외의 경우:
      → GUI 실행
    """
    if len(sys.argv) >= 2 and sys.argv[1] in ("c", "d"):
        # CLI 모드
        raise SystemExit(cli_main(sys.argv))
    else:
        # GUI 모드
        run_gui()