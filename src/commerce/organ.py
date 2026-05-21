from pathlib import Path
from .models import ProductCatalog, Product, ProductType, CartItem
from .payment import StripeClient


class CommerceOrgan:
    def __init__(self, data_dir: str = "data/commerce", stripe_key: str = ""):
        self.catalog = ProductCatalog(data_dir)
        self.stripe = StripeClient(stripe_key)
        self.name = "commerce"

    def is_alive(self):
        return True

    def tier_products(self) -> list:
        """回傳版本授權商品清單（供 README / 儀表板使用）"""
        return [
            {
                "id": "license-pro-monthly",
                "name": "黑曜專業版 💎",
                "type": "license",
                "price": "$29/月",
                "price_cents": 2900,
                "description": "40 器官 + SEO/廣告 + AI 內容 + 200 工具",
                "features": [
                    "40 個核心器官", "自我診斷 / 修復", "Telegram Bot",
                    "SEO / 廣告零件", "AI 內容生成",
                    "工具系統 (200+ 個)", "優先技術支援",
                ],
            },
            {
                "id": "license-pro-yearly",
                "name": "黑曜專業版 💎 (年)",
                "type": "license",
                "price": "$290/年 (省 17%)",
                "price_cents": 29000,
                "description": "專業版年繳優惠",
                "features": [],
            },
            {
                "id": "license-enterprise-monthly",
                "name": "黑曜企業版 🏢",
                "type": "license",
                "price": "$99/月",
                "price_cents": 9900,
                "description": "50 器官 + 雲端託管 + 專屬支援 + SLA",
                "features": [
                    "50 個核心器官", "雲端託管服務", "專屬技術支援",
                    "定製新零件", "SLA 保障",
                    "工具系統 (250+ 個)", "文明級記憶",
                ],
            },
            {
                "id": "license-enterprise-yearly",
                "name": "黑曜企業版 🏢 (年)",
                "type": "license",
                "price": "$990/年 (省 17%)",
                "price_cents": 99000,
                "description": "企業版年繳優惠",
                "features": [],
            },
        ]

    def seed_sample_products(self):
        for pdef in self.tier_products():
            self.catalog.add_product(Product(
                id=pdef["id"],
                name=pdef["name"],
                type=ProductType.LICENSE,
                price_cents=pdef["price_cents"],
                description=pdef["description"],
                metadata={"features": pdef["features"], "type": "license"},
            ))
