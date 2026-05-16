import json, uuid, time
from pathlib import Path
from typing import Optional
from enum import Enum

class ProductType(str, Enum):
    ORGAN = "organ"
    TOOL = "tool"
    AGENT = "agent"
    LICENSE = "license"

class Product:
    def __init__(self, id: str, name: str, type: ProductType, price_cents: int,
                 description: str = "", metadata: dict = None):
        self.id = id
        self.name = name
        self.type = type
        self.price_cents = price_cents
        self.description = description
        self.metadata = metadata or {}
        self.created_at = time.time()

    def to_dict(self):
        return {"id": self.id, "name": self.name, "type": self.type.value,
                "price_cents": self.price_cents, "description": self.description,
                "metadata": self.metadata}

    @staticmethod
    def from_dict(d):
        return Product(d["id"], d["name"], ProductType(d["type"]),
                       d["price_cents"], d.get("description", ""), d.get("metadata"))

class CartItem:
    def __init__(self, product_id: str, qty: int = 1):
        self.product_id = product_id
        self.qty = qty

class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FULFILLED = "fulfilled"
    REFUNDED = "refunded"

class Order:
    def __init__(self, buyer_id: str, items: list[CartItem], total_cents: int,
                 commission_cents: int = 0, status: OrderStatus = OrderStatus.PENDING):
        self.id = str(uuid.uuid4())[:12]
        self.buyer_id = buyer_id
        self.items = items
        self.total_cents = total_cents
        self.commission_cents = commission_cents
        self.status = status
        self.created_at = time.time()
        self.paid_at: Optional[float] = None
        self.stripe_payment_intent: Optional[str] = None

    def to_dict(self):
        return {"id": self.id, "buyer_id": self.buyer_id,
                "items": [{"product_id": i.product_id, "qty": i.qty} for i in self.items],
                "total_cents": self.total_cents, "commission_cents": self.commission_cents,
                "status": self.status.value, "created_at": self.created_at,
                "paid_at": self.paid_at, "stripe_payment_intent": self.stripe_payment_intent}

    @staticmethod
    def from_dict(d):
        o = Order(d["buyer_id"],
                  [CartItem(i["product_id"], i["qty"]) for i in d["items"]],
                  d["total_cents"], d["commission_cents"], OrderStatus(d["status"]))
        o.id = d["id"]
        o.created_at = d["created_at"]
        o.paid_at = d.get("paid_at")
        o.stripe_payment_intent = d.get("stripe_payment_intent")
        return o

class CommissionTier:
    def __init__(self, rate: float = 0.10, min_cents: int = 0):
        self.rate = rate
        self.min_cents = min_cents

class ProductCatalog:
    def __init__(self, data_dir: str = "data/commerce"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.products: dict[str, Product] = {}
        self.orders: dict[str, Order] = {}
        self.commission = CommissionTier()
        self._load()

    def _load(self):
        pf = self.data_dir / "products.json"
        of = self.data_dir / "orders.json"
        if pf.exists():
            for d in json.loads(pf.read_text()):
                p = Product.from_dict(d)
                self.products[p.id] = p
        if of.exists():
            for d in json.loads(of.read_text()):
                o = Order.from_dict(d)
                self.orders[o.id] = o

    def _save(self):
        (self.data_dir / "products.json").write_text(
            json.dumps([p.to_dict() for p in self.products.values()], ensure_ascii=False, indent=2))
        (self.data_dir / "orders.json").write_text(
            json.dumps([o.to_dict() for o in self.orders.values()], ensure_ascii=False, indent=2))

    def add_product(self, product: Product):
        self.products[product.id] = product
        self._save()

    def remove_product(self, product_id: str):
        self.products.pop(product_id, None)
        self._save()

    def get_product(self, product_id: str) -> Optional[Product]:
        return self.products.get(product_id)

    def list_products(self, type: Optional[ProductType] = None) -> list[Product]:
        if type:
            return [p for p in self.products.values() if p.type == type]
        return list(self.products.values())

    def create_order(self, buyer_id: str, items: list[CartItem]) -> Order:
        total = sum(self.products[i.product_id].price_cents * i.qty
                    for i in items if i.product_id in self.products)
        commission = max(int(total * self.commission.rate), self.commission.min_cents)
        order = Order(buyer_id, items, total, commission)
        self.orders[order.id] = order
        self._save()
        return order

    def fulfill_order(self, order_id: str):
        o = self.orders.get(order_id)
        if o and o.status == OrderStatus.PAID:
            o.status = OrderStatus.FULFILLED
            o.paid_at = time.time()
            self._save()
            return True
        return False
