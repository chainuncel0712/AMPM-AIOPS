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

    def seed_sample_products(self):
        samples = [
            Product("organ-memory-pro", "記憶體 Pro 版", ProductType.ORGAN, 2999,
                    "高效能記憶模組，支援向量檢索 + 長期記憶"),
            Product("organ-economy", "經濟引擎", ProductType.ORGAN, 4999,
                    "完整經濟系統：成本計算、ROI 預測、資源調度"),
            Product("tool-seo-master", "SEO 優化工具組", ProductType.TOOL, 1499,
                    "自動 SEO 分析、關鍵字建議、排名追蹤"),
            Product("agent-sales", "銷售代理", ProductType.AGENT, 9999,
                    "24/7 自動銷售代理，整合 CRM + 報價系統"),
            Product("license-studio", "工作室授權 (年)", ProductType.LICENSE, 19999,
                    "多租戶工作室平台授權，含 5 個工作空間"),
        ]
        for p in samples:
            self.catalog.add_product(p)
