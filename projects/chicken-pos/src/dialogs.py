from __future__ import annotations
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QComboBox, QLineEdit, QLabel, QPushButton,
    QHBoxLayout, QMessageBox, QFileDialog, QTextEdit, QVBoxLayout
)
from models import Sale

class PaymentDialog(QDialog):
    def __init__(self, total: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("💳 결제")
        self.total = total
        self.method = "cash"
        self.tendered = None
        self.change = None

        layout = QFormLayout()
        self.method_cb = QComboBox()
        self.method_cb.addItems(["현금", "카드"])
        self.method_cb.currentTextChanged.connect(self._toggle_cash)
        layout.addRow("지불 방법", self.method_cb)

        self.tender_edit = QLineEdit()
        self.tender_edit.setPlaceholderText("현금일 때 지불액 입력")
        layout.addRow("지불액", self.tender_edit)

        self.change_lbl = QLabel(f"총 금액: {self.total}원")
        layout.addRow(self.change_lbl)

        btns = QHBoxLayout()
        calc = QPushButton("계산")
        ok = QPushButton("확인")
        calc.clicked.connect(self._calc)
        ok.clicked.connect(self._ok)
        btns.addWidget(calc); btns.addWidget(ok)
        layout.addRow(btns)
        self.setLayout(layout)
        self._toggle_cash("현금")

    def _toggle_cash(self, text):
        is_cash = (text == "현금")
        self.tender_edit.setEnabled(is_cash)
        if not is_cash:
            self.tender_edit.clear()
            self.change_lbl.setText(f"총 금액: {self.total}원")

    def _calc(self):
        if self.method_cb.currentText() == "카드":
            self.method = "card"
            QMessageBox.information(self, "카드", "카드 결제 선택됨")
            return
        try:
            tender = int(self.tender_edit.text())
        except ValueError:
            QMessageBox.warning(self, "오류", "지불액을 숫자로 입력하세요")
            return
        if tender < self.total:
            QMessageBox.warning(self, "부족", "지불액이 부족합니다.")
            return
        self.method = "cash"
        self.tendered = tender
        self.change = tender - self.total
        self.change_lbl.setText(f"거스름돈: {self.change}원")

    def _ok(self):
        if self.method_cb.currentText() == "카드":
            self.method = "card"
        elif self.tendered is None:
            QMessageBox.warning(self, "오류", "현금 결제는 계산 버튼을 눌러주세요.")
            return
        self.accept()


class ReceiptDialog(QDialog):
    def __init__(self, shop: str, sale: Sale, itemized: bool, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🧾 영수증 미리보기")
        layout = QVBoxLayout()
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setStyleSheet("background:#1E1E1E; color:white; font-family:Consolas;")
        layout.addWidget(self.text)
        save = QPushButton("TXT로 저장")
        save.clicked.connect(self._save)
        layout.addWidget(save)
        self.setLayout(layout)
        self._populate(shop, sale, itemized)

    def _populate(self, shop: str, sale: Sale, itemized: bool):
        lines = [f"=== {shop} ===", f"일시: {sale.ts}", f"테이블: {sale.table_no}"]
        if itemized:
            lines.append("\n[품목]")
            for it in sale.items:
                lines.append(f"- {it.name} x{it.qty} = {it.unit_price * it.qty}원")
        lines.append(f"\n합계: {sale.subtotal}원")
        if sale.tax:
            lines.append(f"세금: {sale.tax}원")
        lines.append(f"총액: {sale.total}원")
        lines.append(f"결제수단: {'현금' if sale.method == 'cash' else '카드'}")
        if sale.method == "cash":
            lines.append(f"지불액: {sale.tendered}원 / 거스름돈: {sale.change}원")
        self.text.setPlainText("\n".join(lines))

    def _save(self):
        path, _ = QFileDialog.getSaveFileName(self, "영수증 저장", "receipt.txt", "Text Files (*.txt)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.text.toPlainText())
