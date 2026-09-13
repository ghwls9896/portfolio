from __future__ import annotations
import json, os
from datetime import datetime
from typing import Dict, List, Tuple
from dataclasses import asdict

from models import MenuItem, InventoryItem, SaleItem, Sale

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")
MENU_PATH = os.path.join(DATA_DIR, "menu.json")
INV_PATH = os.path.join(DATA_DIR, "inventory.json")
SALES_PATH = os.path.join(DATA_DIR, "sales.json")

class Store:
    def __init__(self):
        self.config: Dict = {}
        self.menu: Dict[str, MenuItem] = {}
        self.inventory: Dict[str, InventoryItem] = {}
        self.sales: List[Sale] = []

    def load(self):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            self.config = json.load(f)
        with open(MENU_PATH, "r", encoding="utf-8") as f:
            self.menu = {m["id"]: MenuItem(**m) for m in json.load(f)}
        with open(INV_PATH, "r", encoding="utf-8") as f:
            self.inventory = {i["name"]: InventoryItem(**i) for i in json.load(f)}

        if os.path.exists(SALES_PATH):
            with open(SALES_PATH, "r", encoding="utf-8") as f:
                raw = json.load(f)
        else:
            raw = []

        self.sales = [
            Sale(
                ts=s["ts"], table_no=s["table_no"],
                items=[SaleItem(**it) for it in s["items"]],
                subtotal=s["subtotal"], tax=s["tax"], total=s["total"],
                method=s["method"], tendered=s.get("tendered"), change=s.get("change")
            ) for s in raw
        ]

    def save_inventory(self):
        with open(INV_PATH, "w", encoding="utf-8") as f:
            json.dump([asdict(x) for x in self.inventory.values()],
                      f, ensure_ascii=False, indent=2)

    def append_sale(self, sale: Sale):
        self.sales.append(sale)
        with open(SALES_PATH, "w", encoding="utf-8") as f:
            json.dump([{
                "ts": s.ts, "table_no": s.table_no,
                "items": [asdict(it) for it in s.items],
                "subtotal": s.subtotal, "tax": s.tax, "total": s.total,
                "method": s.method, "tendered": s.tendered, "change": s.change
            } for s in self.sales], f, ensure_ascii=False, indent=2)

    def deduct_inventory(self, order_items: List[Tuple[MenuItem, int]]) -> List[str]:
        warnings = []
        for mi, qty in order_items:
            for ing, per in mi.ingredient_usage.items():
                if ing in self.inventory:
                    used = per * qty
                    if self.inventory[ing].stock < used:
                        raise ValueError(f"[재고 부족] {ing} 재고가 부족합니다.")
                    self.inventory[ing].stock = max(0, self.inventory[ing].stock - used)

        self.save_inventory()

        # 경고 기준
        th = float(self.config.get("low_stock_threshold", 0.0))
        for inv in self.inventory.values():
            if inv.stock <= max(inv.reorder_level, th):
                warnings.append(f"[재고 경고] {inv.name}: {inv.stock:.2f}{inv.unit} 남음")
        return warnings

    def make_sale(self, table_no: int, cart: Dict[str, int],
                  method: str, tendered: int | None) -> Tuple[Sale, List[str]]:
        items: List[SaleItem] = []
        subtotal = 0
        for mid, qty in cart.items():
            mi = self.menu[mid]
            items.append(SaleItem(menu_id=mid, name=mi.name,
                                  unit_price=mi.price, qty=qty))
            subtotal += mi.price * qty

        tax_rate = float(self.config.get("tax_rate", 0.0))
        tax = int(round(subtotal * tax_rate))
        total = subtotal + tax
        change = None
        if method == "cash":
            if tendered is None or tendered < total:
                raise ValueError("현금 지불액이 부족합니다.")
            change = tendered - total

        sale = Sale(
            ts=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            table_no=table_no,
            items=items, subtotal=subtotal, tax=tax, total=total,
            method=method, tendered=tendered, change=change
        )

        order_items = [(self.menu[mid], qty) for mid, qty in cart.items()]
        warnings = self.deduct_inventory(order_items)
        self.append_sale(sale)
        return sale, warnings
