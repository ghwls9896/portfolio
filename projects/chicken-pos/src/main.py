from __future__ import annotations
import sys, os
sys.path.append(os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication
from views import MainWindow
def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
