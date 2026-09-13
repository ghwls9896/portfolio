from __future__ import annotations
from typing import Dict
from collections import defaultdict
import os
from PyQt6.QtCore import QTime  # ✅ 파일 맨 위에 이미 QDate 임포트 되어 있으니 이것만 추가

from PyQt6.QtCore import Qt, QTime, QTimer, QSize, QDate
from PyQt6.QtGui import QIcon, QPixmap, QFont, QColor
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QTableWidget,
    QTableWidgetItem, QPushButton, QTabWidget, QMessageBox, QComboBox, QDateEdit,
     QGridLayout, QScrollArea, QLineEdit, QInputDialog 
)

from PyQt6.QtCharts import QChart, QChartView, QLineSeries
from PyQt6.QtGui import QPainter
from store import Store
from dialogs import PaymentDialog, ReceiptDialog
from models import MenuItem, Sale, SaleItem


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.store = Store()
        self.store.load()
        self.setWindowTitle(f"{self.store.config.get('shop_name')} POS")
        self.resize(1250, 780)
        self.setFixedSize(1250, 780)  # 창 크기 고정

        self.carts: Dict[int, Dict[str, int]] = {
            i + 1: {} for i in range(self.store.config.get("table_count", 6))
        }
        self.current_table = 1

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.tabs.addTab(self._build_orders_tab(), "🍗 주문")
        self.tabs.addTab(self._build_stats_tab(), "📊 통계/관리")
        self._stats_auth = False  # ✅ 관리자 인증 상태
        self.tabs.currentChanged.connect(self._on_tab_changed)

        # 시계
        self.status = self.statusBar()
        self.clock = QLabel("")
        self.status.addPermanentWidget(self.clock)
        timer = QTimer(self)
        timer.timeout.connect(self._tick)
        timer.start(1000)
        self._tick()

        # 스타일 적용
        self._apply_theme()

    # ===================== 테마 =====================
    def _apply_theme(self):
        self.setStyleSheet("""
            QMainWindow { background:#FFF8E1; }
            QLabel { color:#212121; font-family:'Segoe UI'; font-size:14px; }
            QTabWidget::pane { border: 2px solid #FFE082; }
            QTabBar::tab {
                background:#FFF59D; color:#4E342E; padding:8px 16px; margin-right:3px;
                border-top-left-radius:8px; border-top-right-radius:8px;
                font-weight:600;
            }
            QTabBar::tab:selected { background:#FFD54F; }
            QListWidget {
                background:#FFF9C4; color:#4E342E; border:1px solid #FFB300; font-weight:600;
            }
            QLineEdit {
                background:#FFFDE7; color:#212121; border:1px solid #FFCA28;
                border-radius:8px; padding:6px 10px;
            }
            QComboBox {
                background:#FFFDE7; color:#212121; border:1px solid #FFCA28;
                border-radius:8px; padding:6px 10px;
            }
            QComboBox QAbstractItemView {
                background:#FFF8E1; selection-background-color:#FFB300; selection-color:#212121;
            }
            QPushButton {
                background:#FFB300; color:#212121; font-weight:800;
                border-radius:14px; padding:10px 14px; border:2px solid #FF8F00;
            }
            QPushButton:hover { background:#FFD54F; }
            QPushButton:pressed { background:#E53935; color:white; border-color:#E53935; }
            QTableWidget {
                background:#FFFDE7; color:#212121; gridline-color:#BCAAA4;
                selection-background-color:#FFE082; selection-color:#212121;
                border:1px solid #FFCC80; border-radius:10px;
            }
            QHeaderView::section {
                background:#FFE082; color:#4E342E; font-weight:700; padding:6px;
                border:none;
            }
            QScrollArea { border:none; }
        """)

    def _tick(self):
        from datetime import datetime
        self.clock.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # ===================== 주문 탭 =====================
    def _build_orders_tab(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)

        # 왼쪽: 테이블 선택
        left = QVBoxLayout()
        left.addWidget(QLabel("🍽️ 테이블"))
        self.table_list = QListWidget()
        for i in range(1, self.store.config.get("table_count", 6) + 1):
            self.table_list.addItem(f"Table {i}")
        self.table_list.setCurrentRow(0)
        self.table_list.currentRowChanged.connect(self._change_table)
        left.addWidget(self.table_list)
        layout.addLayout(left, 1)

        # 중앙: 메뉴
        mid = QVBoxLayout()
        bar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("메뉴 검색 (예: 숯불, 양념, 치즈)")
        self.category_cb = QComboBox()
        self.category_cb.addItems(["전체", "후라이드", "숯불", "사이드", "소스", "음료"])
        apply_btn = QPushButton("적용")
        apply_btn.clicked.connect(self._rebuild_menu_grid)
        bar.addWidget(self.search_edit)
        bar.addWidget(self.category_cb)
        bar.addWidget(apply_btn)
        mid.addLayout(bar)

        self.menu_scroll = QScrollArea()
        self.menu_scroll.setWidgetResizable(True)
        self.menu_scroll.setMinimumHeight(600)
        self.menu_wrap = QWidget()
        self.menu_grid = QGridLayout(self.menu_wrap)
        self.menu_grid.setContentsMargins(10, 10, 10, 10)
        self.menu_grid.setHorizontalSpacing(12)
        self.menu_grid.setVerticalSpacing(18)
        self.menu_scroll.setWidget(self.menu_wrap)
        mid.addWidget(self.menu_scroll)
        layout.addLayout(mid, 2)
        self._rebuild_menu_grid()

        # 오른쪽: 주문표
        right = QVBoxLayout()
        topbar = QHBoxLayout()
        self.total_lbl = QLabel("TOTAL: 0원")
        self.total_lbl.setFont(QFont("Segoe UI", 18, QFont.Weight.Black))
        self.total_lbl.setStyleSheet("color:#E53935;")
        self.mode_cb = QComboBox()
        self.mode_cb.addItems(["매장", "포장"])
        topbar.addWidget(self.total_lbl)
        topbar.addStretch(1)
        topbar.addWidget(self.mode_cb)
        right.addLayout(topbar)

        self.cart_tbl = QTableWidget(0, 5)
        self.cart_tbl.setHorizontalHeaderLabels(["메뉴", "단가", "수량", "금액", "ID"])
        self.cart_tbl.setColumnHidden(4, True)
        right.addWidget(self.cart_tbl)

        btns = QHBoxLayout()
        b_pay = QPushButton("💵 결제")
        b_clear = QPushButton("🧹 전체취소")
        b_receipt = QPushButton("🧾 영수증")
        for b in (b_pay, b_clear, b_receipt):
            btns.addWidget(b)
        b_pay.clicked.connect(self._pay)
        b_clear.clicked.connect(self._clear_cart)
        b_receipt.clicked.connect(lambda: self._preview_receipt(True))
        right.addLayout(btns)
        layout.addLayout(right, 2)
        return w

    # ===================== 메뉴 표시 =====================
    def _menu_items_filtered(self):
        kw = self.search_edit.text().strip().lower()
        cat = self.category_cb.currentText()
        items = list(self.store.menu.values())
        if cat != "전체":
            items = [m for m in items if m.category == cat]
        if kw:
            items = [m for m in items if kw in m.name.lower()]
        return items

    def _rebuild_menu_grid(self):
        # 기존 위젯 제거
        while self.menu_grid.count():
            w = self.menu_grid.takeAt(0).widget()
            if w:
                w.deleteLater()

        img_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "img")
        items = self._menu_items_filtered()

        COLS = 3  # 한 줄당 3개 고정

        for idx, mi in enumerate(items):
            # 카드 하나당 QWidget으로 구성
            card = QWidget()
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(6, 6, 6, 6)
            card_layout.setSpacing(4)

            # 이미지
            img_label = QLabel()
            img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img_path = os.path.join(img_dir, f"{mi.id}.png")
            if os.path.exists(img_path):
                pix = QPixmap(img_path).scaled(
                    120, 120,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                img_label.setPixmap(pix)
            else:
                img_label.setText("(이미지 없음)")

            # 텍스트
            name_lbl = QLabel(f"{mi.name}")
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_lbl.setStyleSheet("font-weight:600; color:#3E2723;")

            price_lbl = QLabel(f"₩{mi.price:,}")
            price_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            price_lbl.setStyleSheet("color:#BF360C; font-weight:700;")

            # 버튼 (추가용)
            btn = QPushButton("추가")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background:#FFB300; border-radius:10px;
                    color:#212121; font-weight:600;
                }
                QPushButton:hover { background:#FFD54F; }
                QPushButton:pressed { background:#E53935; color:white; }
            """)
            btn.clicked.connect(lambda _, name=mi.name: self._add_menu_by_name(name))

            # 카드 배치
            card_layout.addWidget(img_label)
            card_layout.addWidget(name_lbl)
            card_layout.addWidget(price_lbl)
            card_layout.addWidget(btn)
            card_layout.addStretch(1)

            # 카드 스타일
            card.setStyleSheet("""
                QWidget {
                    background:#FFF9C4;
                    border:1px solid #FFB300;
                    border-radius:12px;
                }
            """)

            card.setFixedSize(140, 185)

            # 3개씩 고정 배치
            row = idx // COLS
            col = idx % COLS
            self.menu_grid.addWidget(card, row, col, Qt.AlignmentFlag.AlignCenter)

        # 여백 및 간격
        self.menu_grid.setHorizontalSpacing(14)
        self.menu_grid.setVerticalSpacing(16)
        self.menu_grid.setContentsMargins(10, 10, 10, 10)
    # ===================== 주문 관련 =====================
    def _add_menu_by_name(self, name: str):
        mid = next((m.id for m in self.store.menu.values() if m.name == name), None)
        if not mid:
            return
        cart = self.carts[self.current_table]
        cart[mid] = cart.get(mid, 0) + 1
        self._refresh_cart()

    def _change_table(self, row: int):
        if not hasattr(self, "cart_tbl"):
            return
        self.current_table = row + 1
        self._refresh_cart()

    def _refresh_cart(self):
        cart = self.carts[self.current_table]
        self.cart_tbl.setRowCount(0)
        total = 0
        for mid, qty in cart.items():
            mi = self.store.menu[mid]
            row = self.cart_tbl.rowCount()
            self.cart_tbl.insertRow(row)
            self.cart_tbl.setItem(row, 0, QTableWidgetItem(mi.name))
            self.cart_tbl.setItem(row, 1, QTableWidgetItem(str(mi.price)))
            self.cart_tbl.setItem(row, 2, QTableWidgetItem(str(qty)))
            self.cart_tbl.setItem(row, 3, QTableWidgetItem(str(mi.price * qty)))
            self.cart_tbl.setItem(row, 4, QTableWidgetItem(mi.id))
            total += mi.price * qty
        self.total_lbl.setText(f"TOTAL: {total:,}원")

    def _clear_cart(self):
        self.carts[self.current_table].clear()
        self._refresh_cart()

    def _pay(self):
        cart = self.carts[self.current_table]
        if not cart:
            QMessageBox.information(self, "안내", "주문 내역이 비어 있습니다.")
            return
        total = sum(self.store.menu[mid].price * qty for mid, qty in cart.items())
        dlg = PaymentDialog(total, self)
        if not dlg.exec():
            return
        method = "cash" if dlg.method == "cash" else "card"
        tendered = dlg.tendered if method == "cash" else None
        try:
            sale, warnings = self.store.make_sale(self.current_table, cart, method, tendered)
        except ValueError as e:
            QMessageBox.warning(self, "오류", str(e))
            return
        self.carts[self.current_table].clear()
        self._refresh_cart()
        if warnings:
            QMessageBox.warning(self, "재고 경고", "\n".join(warnings))
        ReceiptDialog(self.store.config.get("shop_name"), sale, True, self).exec()

    def _preview_receipt(self, itemized: bool):
        cart = self.carts[self.current_table]
        if not cart:
            QMessageBox.information(self, "안내", "주문 내역이 비어 있습니다.")
            return
        items = []
        subtotal = 0
        for mid, qty in cart.items():
            mi = self.store.menu[mid]
            items.append(SaleItem(menu_id=mid, name=mi.name, unit_price=mi.price, qty=qty))
            subtotal += mi.price * qty
        sale = Sale(ts="미결제", table_no=self.current_table, items=items,
                    subtotal=subtotal, tax=0, total=subtotal,
                    method="?", tendered=None, change=None)
        ReceiptDialog(self.store.config.get("shop_name"), sale, itemized, self).exec()

    # ===================== 통계 탭 =====================
     # ===================== 통계 탭 =====================
    def _build_stats_tab(self) -> QWidget:
        from PyQt6.QtCharts import QChart, QChartView
        from PyQt6.QtWidgets import QSpinBox, QHeaderView
        from PyQt6.QtGui import QPainter

        w = QWidget()
        v = QVBoxLayout(w)

        # 월 선택만 남김
        bar = QHBoxLayout()
        bar.addWidget(QLabel("📅 월 선택:"))
        self.month_spin = QSpinBox()
        self.month_spin.setRange(1, 12)
        self.month_spin.setValue(QDate.currentDate().month())
        self.month_spin.valueChanged.connect(self._refresh_stats)
        bar.addWidget(self.month_spin)
        bar.addStretch(1)
        v.addLayout(bar)

        # 그래프
        self.chart = QChart()
        self.chart.setTitle("📈 일자별 매출 추이 (월 단위)")
        self.chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.chart_view.setMinimumHeight(320)
        v.addWidget(self.chart_view)

        # 재고 요약 테이블
        v.addWidget(QLabel("📦 현재 재고 현황"))
        self.inv_table = QTableWidget(0, 4)
        self.inv_table.setHorizontalHeaderLabels(["품목", "단위", "재고량", "경고 기준"])
        self.inv_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        v.addWidget(self.inv_table)

        # 요약 텍스트
        self.stats_lbl = QLabel("📊 매출 통계가 여기에 표시됩니다.")
        self.stats_lbl.setStyleSheet("font-weight:600; margin-top:10px;")
        v.addWidget(self.stats_lbl)

        return w


    def _refresh_stats(self):
        from PyQt6.QtCharts import QLineSeries, QDateTimeAxis, QValueAxis
        from PyQt6.QtCore import QDateTime, QDate, QTime, Qt
        from PyQt6.QtGui import QColor

        self.chart.removeAllSeries()
        for axis in self.chart.axes():
            self.chart.removeAxis(axis)

        series = QLineSeries()
        series.setName("일자별 매출(₩)")
        series.setColor(QColor("#FF9800"))

        total_rev = 0
        qty_by_menu = defaultdict(int)

        selected_month = self.month_spin.value()
        current_year = QDate.currentDate().year()

        # 이번 달의 1일 ~ 말일까지
        start_date = QDate(current_year, selected_month, 1)
        end_date = start_date.addMonths(1).addDays(-1)

        daily_sales = defaultdict(int)

        # 일자별 매출 합산
        for s in self.store.sales:
            dt = QDateTime.fromString(s.ts, "yyyy-MM-dd HH:mm:ss")
            d = dt.date()
            if d.year() == current_year and d.month() == selected_month:
                daily_sales[d.day()] += s.total
                total_rev += s.total
                for it in s.items:
                    qty_by_menu[it.name] += it.qty

        # 누락된 날짜(매출 0원)도 표시
        for day in range(1, end_date.day() + 1):
            point_time = QDateTime(QDate(current_year, selected_month, day), QTime(12, 0, 0))
            series.append(point_time.toSecsSinceEpoch() * 1000, daily_sales.get(day, 0))

        self.chart.addSeries(series)

        # X축: 일자 (모든 날짜 표시)
        axis_x = QDateTimeAxis()
        axis_x.setFormat("dd")
        axis_x.setTitleText(f"{selected_month}월 일자")
        axis_x.setRange(
            QDateTime(start_date, QTime(0, 0, 0)),
            QDateTime(end_date, QTime(23, 59, 59))
        )
        axis_x.setTickCount(end_date.day())  # ✅ 하루하루 전부 눈금 표시

        # Y축
        axis_y = QValueAxis()
        axis_y.setTitleText("매출(원)")

        self.chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)
        self.chart.legend().setVisible(False)

        # 재고 테이블
        self.inv_table.setRowCount(0)
        for inv in self.store.inventory.values():
            row = self.inv_table.rowCount()
            self.inv_table.insertRow(row)
            self.inv_table.setItem(row, 0, QTableWidgetItem(inv.name))
            self.inv_table.setItem(row, 1, QTableWidgetItem(inv.unit))
            self.inv_table.setItem(row, 2, QTableWidgetItem(f"{inv.stock:.2f}"))
            self.inv_table.setItem(row, 3, QTableWidgetItem(f"{inv.reorder_level:.2f}"))
            if inv.stock <= inv.reorder_level:
                for c in range(4):
                    self.inv_table.item(row, c).setBackground(QColor("#FFCDD2"))

        # 통계 요약
        lines = [f"총 매출액: ₩{total_rev:,}", "", "[메뉴별 판매 수량]"]
        for name, q in qty_by_menu.items():
            lines.append(f"- {name}: {q}개")
        self.stats_lbl.setText("\n".join(lines))
    # ===================== 관리자 탭 =====================
    def _build_admin_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(QLabel("🧑‍🍳 관리자 기능"))
        v.addWidget(QLabel("• data/config.json, menu.json, inventory.json 수정으로 관리"))
        btn = QPushButton("현재 재고 요약 보기")
        btn.clicked.connect(self._show_inv)
        v.addWidget(btn)
        self.inv_lbl = QLabel("")
        v.addWidget(self.inv_lbl)
        return w

    def _show_inv(self):
        lines = ["[재고 현황]"]
        for inv in self.store.inventory.values():
            lines.append(f"- {inv.name}: {inv.stock:.2f}{inv.unit} (경고 {inv.reorder_level}{inv.unit})")
        self.inv_lbl.setText("\n".join(lines))
    def _on_tab_changed(self, idx: int):
        """📊 통계/관리 탭 접근 시 비밀번호 검사"""
        STATS_TAB_INDEX = 1  # 📊 통계/관리 탭이 두 번째(0부터 시작)
        if idx != STATS_TAB_INDEX:
            return
        if self._stats_auth:
            return

        pwd, ok = QInputDialog.getText(
            self, "관리자 인증", "비밀번호를 입력하세요:",
            QLineEdit.EchoMode.Password
        )

        if not ok or pwd.strip() != "admin":  # ✅ 비밀번호 실패
            QMessageBox.warning(self, "접근 불가", "비밀번호가 틀렸거나 취소되었습니다.")
            self.tabs.setCurrentIndex(0)  # 다시 주문 탭으로 돌려보냄
        else:
            self._stats_auth = True
            QMessageBox.information(self, "인증 성공", "관리자 권한이 확인되었습니다.")
