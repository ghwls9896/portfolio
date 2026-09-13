from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class MenuItem:
    id: str
    name: str
    price: int
    category: str
    ingredient_usage: Dict[str, float]

@dataclass
class InventoryItem:
    name: str
    unit: str
    stock: float
    reorder_level: float

@dataclass
class SaleItem:
    menu_id: str
    name: str
    unit_price: int
    qty: int

@dataclass
class Sale:
    ts: str
    table_no: int
    items: List[SaleItem]
    subtotal: int
    tax: int
    total: int
    method: str               # "cash" | "card"
    tendered: Optional[int]
    change: Optional[int]
