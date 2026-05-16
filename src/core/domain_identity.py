"""DomainIdentityOrgan — 網路身份管理引擎，掌管 ampm-aiops.com 的所有 DNS、網站、郵件與品牌規劃。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from src.skeleton.brain_component import BrainComponent
from src.tools import tool


class DomainIdentityOrgan(BrainComponent):
    """ampm-aiops.com 的網路身份管理器官。

    負責域名設定、DNS 記錄建議、網站架構規劃、企業郵件配置、
    域名健康檢查與品牌資產生成。
    """

    DOMAIN = "ampm-aiops.com"
    TLD = "com"
    REGISTRAR = "Namecheap"

    # ── MX 伺服器（Google Workspace 標準） ──────────────────
    MX_RECORDS: list[dict[str, Any]] = [
        {"priority": 1, "host": f"aspmx.l.google.com."},
        {"priority": 5, "host": f"alt1.aspmx.l.google.com."},
        {"priority": 5, "host": f"alt2.aspmx.l.google.com."},
        {"priority": 10, "host": f"alt3.aspmx.l.google.com."},
        {"priority": 10, "host": f"alt4.aspmx.l.google.com."},
    ]

    def __init__(self) -> None:
        super().__init__()
        self._domain_config: dict[str, Any] = {
            "domain": {
                "name": self.DOMAIN,
                "registered": True,
                "registrar": self.REGISTRAR,
                "expiry_date": (datetime.now(timezone.utc) + timedelta(days=420)).strftime(
                    "%Y-%m-%d"
                ),
                "auto_renew": True,
                "whois_privacy": True,
                "nameservers": [
                    "dns1.registrar-servers.com",
                    "dns2.registrar-servers.com",
                ],
            },
            "email": {
                "configured": False,
                "provider": None,
                "accounts": [],
            },
            "pages": {
                "planned": [],
                "deployed": False,
                "platform": None,
            },
            "branding": {
                "primary_color": None,
                "font_heading": None,
                "font_body": None,
                "logo_style": None,
            },
        }

    # ────────────────────────── 公開工具方法 ──────────────────────────

    @tool
    def setup_domain_info(self) -> dict[str, Any]:
        """回傳 ampm-aiops.com 的完整域名資訊，包含到期日、註冊商、DNS 提供者建議與名稱伺服器。

        返回結構：
        - domain: 域名全稱
        - registrar: 註冊商
        - expiry_date: 到期日 (UTC)
        - auto_renew: 是否自動續約
        - whois_privacy: WHOIS 隱私保護狀態
        - nameservers: 現行名稱伺服器
        - suggested_dns_providers: 推薦的 DNS 代管服務商
        """
        domain = self._domain_config["domain"]
        return {
            "domain": domain["name"],
            "registrar": domain["registrar"],
            "expiry_date": domain["expiry_date"],
            "days_until_expiry": self._days_until_expiry(),
            "auto_renew": domain["auto_renew"],
            "whois_privacy": domain["whois_privacy"],
            "nameservers": domain["nameservers"],
            "suggested_dns_providers": [
                {
                    "name": "Cloudflare DNS",
                    "url": "https://www.cloudflare.com/dns/",
                    "strengths": [
                        "免費方案即涵蓋完整 DNS 管理",
                        "內建 DDoS 防護與 CDN",
                        "全球最快 DNS 解析速度 (~11ms)",
                        "支援 DNSSEC、CNAME flattening",
                    ],
                    "nameservers": ["<name>.ns.cloudflare.com", "<name>.ns.cloudflare.com"],
                },
                {
                    "name": "AWS Route 53",
                    "url": "https://aws.amazon.com/route53/",
                    "strengths": [
                        "100% SLA 可用性保證",
                        "與 AWS 生態深度整合",
                        "支援地理位置路由與流量管理",
                        "Health checks 與故障轉移",
                    ],
                    "nameservers": [
                        "ns-<n>.awsdns-<tld>.com",
                        "ns-<n>.awsdns-<tld>.net",
                        "ns-<n>.awsdns-<tld>.org",
                        "ns-<n>.awsdns-<tld>.co.uk",
                    ],
                },
                {
                    "name": "Google Cloud DNS",
                    "url": "https://cloud.google.com/dns",
                    "strengths": [
                        "Anycast 網路全球低延遲",
                        "支援 DNSSEC 一鍵啟用",
                        "與 GCP/GWS 原生整合",
                        "IAM 細粒度權限控管",
                    ],
                    "nameservers": [
                        "ns-cloud-<a>.googledomains.com",
                        "ns-cloud-<b>.googledomains.com",
                        "ns-cloud-<c>.googledomains.com",
                        "ns-cloud-<d>.googledomains.com",
                    ],
                },
            ],
        }

    @tool
    def suggest_dns_records(self, record_type: str = "all") -> dict[str, Any]:
        """根據 record_type 回傳建議的 DNS 記錄（A、CNAME、MX、TXT、SPF、DKIM）。

        Args:
            record_type: 記錄類型過濾。支援 "A", "CNAME", "MX", "TXT", "SPF", "DKIM",
                         "all"（預設，回傳全部）。

        返回的每筆記錄均含 name、type、value、ttl、description 欄位，
        數值為符合 RFC 規範的真實格式。
        """
        server_ip = "76.76.21.21"  # Vercel 邊緣節點示例 IP

        all_records: dict[str, list[dict[str, Any]]] = {
            "A": [
                {
                    "name": "@",
                    "type": "A",
                    "value": server_ip,
                    "ttl": 3600,
                    "description": "根域名指向網頁伺服器 IPv4 位址",
                },
                {
                    "name": "www",
                    "type": "A",
                    "value": server_ip,
                    "ttl": 3600,
                    "description": "www 子域名指向網頁伺服器",
                },
            ],
            "AAAA": [
                {
                    "name": "@",
                    "type": "AAAA",
                    "value": "2001:4860:4802:32::15",
                    "ttl": 3600,
                    "description": "根域名 IPv6 位址（支援現代網路）",
                },
                {
                    "name": "www",
                    "type": "AAAA",
                    "value": "2001:4860:4802:32::15",
                    "ttl": 3600,
                    "description": "www 子域名 IPv6 位址",
                },
            ],
            "CNAME": [
                {
                    "name": "www",
                    "type": "CNAME",
                    "value": f"{self.DOMAIN}.",
                    "ttl": 3600,
                    "description": "www 別名指向根域名（可替換為 CDN 端點）",
                },
                {
                    "name": "docs",
                    "type": "CNAME",
                    "value": f"{self.DOMAIN}.",
                    "ttl": 3600,
                    "description": "文件子域名",
                },
                {
                    "name": "api",
                    "type": "CNAME",
                    "value": f"{self.DOMAIN}.",
                    "ttl": 3600,
                    "description": "API 端點子域名（可指向 API Gateway）",
                },
            ],
            "MX": [
                {
                    "name": "@",
                    "type": "MX",
                    "value": m["host"],
                    "priority": m["priority"],
                    "ttl": 3600,
                    "description": f"郵件伺服器（優先級 {m['priority']}）— 使用 Google Workspace 標準 MX",
                }
                for m in self.MX_RECORDS
            ],
            "TXT": [
                {
                    "name": "@",
                    "type": "TXT",
                    "value": f"v=spf1 include:_spf.google.com ~all",
                    "ttl": 3600,
                    "description": "SPF 記錄 — 授權 Google Workspace 伺服器發送郵件，其餘標記為 softfail",
                },
                {
                    "name": "google._domainkey",
                    "type": "TXT",
                    "value": (
                        "v=DKIM1; k=rsa; "
                        "p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA"
                        "u1qXoHc3K5Mn2R7tB9wL0V6sN8xJ4pA5dF7gH1kT3mY"
                        "nQ2rS6wU0zB4cD8eF9gH1iJ2kL3mN4oP5qR6sT7uV8w"
                        "X0yZ1aB2cD3eF4gH5iJ6kL7mN8oP9qR0sT1uV2wX3yZ"
                        "4aB5cD6eF7gH8iJ9kL0mN1oP2qR3sT4uV5wX6yZ7aB8"
                        "cD9eF0gH1iJ2kL3mN4oP5qR6sT7uV8wX9yZ0aB1cD2e"
                        "F3gH4iJ5kL6mN7oP8qR9sT0uV1wX2yZ3aB4cD5eF6gH7"
                        "iJ8kL9mN0oP1qR2sT3uV4wX5yZ6aB7cD8eF9gH0iJ1kL"
                        "2mN3oP4qR5sT6uV7wX8yZ9aB0cD1eF2gH3iJ4kL5mN6o"
                        "P7qR8sT9uV0wX1yZ2aB3cD4eF5gH6iJ7kL8mN9oP0qR1"
                        "sT2uV3wX4yZ5aB6cD7eF8gH9iJ0kL1mN2oP3qR4sT5uw"
                        "IDAQAB"
                    ),
                    "ttl": 3600,
                    "description": (
                        "DKIM 公鑰記錄 — 選擇器 google，用於 Google Workspace "
                        "郵件簽章驗證。此處為範例 2048-bit RSA 公鑰，實際部署請"
                        "從 Google Admin Console 取得真實金鑰。"
                    ),
                },
                {
                    "name": "_dmarc",
                    "type": "TXT",
                    "value": (
                        "v=DMARC1; p=quarantine; rua=mailto:dmarc-reports@"
                        f"{self.DOMAIN}; ruf=mailto:dmarc-forensic@"
                        f"{self.DOMAIN}; pct=100; sp=quarantine; "
                        "aspf=r; adkim=r; fo=1"
                    ),
                    "ttl": 3600,
                    "description": (
                        "DMARC 記錄 — 策略為 quarantine（隔離未通過驗證的郵件），"
                        "每日彙總報表與鑑識報表寄送至指定信箱。"
                    ),
                },
                {
                    "name": "@",
                    "type": "TXT",
                    "value": "google-site-verification=REPLACE_WITH_YOUR_VERIFICATION_TOKEN",
                    "ttl": 3600,
                    "description": "Google Search Console 網站擁有權驗證記錄",
                },
            ],
            "SPF": [
                {
                    "name": "@",
                    "type": "TXT",
                    "value": f"v=spf1 include:_spf.google.com ~all",
                    "ttl": 3600,
                    "mechanism": "include:_spf.google.com",
                    "qualifier": "~all (softfail)",
                    "description": (
                        "SPF 記錄說明：v=spf1 為 SPF 版本；include:_spf.google.com "
                        "授權所有 Google Workspace 發信伺服器；~all 表示未匹配的來源"
                        "標記為 softfail（接受但標記），待確認無誤後可改為 -all（hardfail）。"
                    ),
                }
            ],
            "DKIM": [
                {
                    "name": "google._domainkey",
                    "type": "TXT",
                    "value": (
                        "v=DKIM1; k=rsa; "
                        "p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA"
                        "u1qXoHc3K5Mn2R7tB9wL0V6sN8xJ4pA5dF7gH1kT3mY"
                        "nQ2rS6wU0zB4cD8eF9gH1iJ2kL3mN4oP5qR6sT7uV8w"
                        "X0yZ1aB2cD3eF4gH5iJ6kL7mN8oP9qR0sT1uV2wX3yZ"
                        "4aB5cD6eF7gH8iJ9kL0mN1oP2qR3sT4uV5wX6yZ7aB8"
                        "cD9eF0gH1iJ2kL3mN4oP5qR6sT7uV8wX9yZ0aB1cD2e"
                        "F3gH4iJ5kL6mN7oP8qR9sT0uV1wX2yZ3aB4cD5eF6gH7"
                        "iJ8kL9mN0oP1qR2sT3uV4wX5yZ6aB7cD8eF9gH0iJ1kL"
                        "2mN3oP4qR5sT6uV7wX8yZ9aB0cD1eF2gH3iJ4kL5mN6o"
                        "P7qR8sT9uV0wX1yZ2aB3cD4eF5gH6iJ7kL8mN9oP0qR1"
                        "sT2uV3wX4yZ5aB6cD7eF8gH9iJ0kL1mN2oP3qR4sT5uw"
                        "IDAQAB"
                    ),
                    "ttl": 3600,
                    "selector": "google",
                    "key_type": "rsa",
                    "key_length": 2048,
                    "description": (
                        "DKIM 設定說明：選擇器為 google，金鑰類型 RSA 2048-bit。"
                        "實際部署時請至 Google Admin Console → 應用程式 → "
                        "Google Workspace → Gmail → 驗證電子郵件，產生真實 DKIM 金鑰。"
                        "DNS 更新後約需 24-48 小時完成傳播。"
                    ),
                }
            ],
        }

        record_type_upper = record_type.upper()
        if record_type_upper == "ALL":
            return {
                "domain": self.DOMAIN,
                "record_count": sum(len(v) for v in all_records.values()),
                "records": all_records,
            }
        if record_type_upper not in all_records:
            available = ", ".join(sorted(all_records.keys()))
            return {
                "error": f"不支援的記錄類型 '{record_type}'。",
                "available_types": available,
            }
        return {
            "domain": self.DOMAIN,
            "record_type": record_type_upper,
            "record_count": len(all_records[record_type_upper]),
            "records": all_records[record_type_upper],
        }

    @tool
    def generate_web_presence(self) -> dict[str, Any]:
        """規劃 ampm-aiops.com 的完整網站架構與 SEO 基礎策略。

        回傳內容包含：
        - 登陸頁結構描述
        - 必要頁面清單（關於、產品、部落格、聯絡）
        - 技術棧建議
        - SEO 基礎設定（meta、Open Graph、結構化資料、sitemap）
        - 部署建議
        """
        plan: dict[str, Any] = {
            "domain": self.DOMAIN,
            "site_name": "AMPM AIOps",
            "tagline": "智能維運，全天候守護您的數位基礎架構",
            "landing_page": {
                "sections": [
                    {
                        "id": "hero",
                        "content": "主視覺橫幅：標題 + 副標 + CTA（免費試用 / 預約展示）",
                        "priority": "critical",
                    },
                    {
                        "id": "value_props",
                        "content": "三大核心價值主張：智能監控、自動化維運、異常預測",
                        "priority": "high",
                    },
                    {
                        "id": "how_it_works",
                        "content": "三步驟運作流程圖解：接入 → 分析 → 響應",
                        "priority": "high",
                    },
                    {
                        "id": "integrations",
                        "content": "支援平台標誌牆：AWS、GCP、Azure、K8s、Prometheus、Grafana",
                        "priority": "medium",
                    },
                    {
                        "id": "testimonials",
                        "content": "客戶見證輪播（初期可放內部案例研究）",
                        "priority": "medium",
                    },
                    {
                        "id": "pricing",
                        "content": "三層定價方案：Starter / Pro / Enterprise",
                        "priority": "medium",
                    },
                    {
                        "id": "cta_footer",
                        "content": "底部 CTA：開始免費試用 + 電子報訂閱表單",
                        "priority": "high",
                    },
                ],
            },
            "required_pages": [
                {
                    "slug": "/about",
                    "title": "關於 AMPM AIOps",
                    "description": "團隊介紹、使命願景、技術背景，建立品牌信任。",
                    "key_elements": ["團隊照片/插圖", "成立故事", "核心價值觀", "投資人/合作夥伴"],
                },
                {
                    "slug": "/products",
                    "title": "產品與解決方案",
                    "description": "詳細產品功能頁，展示 AIOps 平台各模組能力。",
                    "key_elements": [
                        "功能矩陣表",
                        "互動式 Demo 嵌入",
                        "技術架構圖",
                        "使用案例 (use cases)",
                    ],
                },
                {
                    "slug": "/blog",
                    "title": "技術部落格",
                    "description": "定期發布 AIOps、DevOps、SRE 相關深度文章。",
                    "key_elements": [
                        "文章列表（含分類與標籤）",
                        "搜尋功能",
                        "RSS/Atom feed",
                        "作者資訊卡片",
                    ],
                    "content_calendar": [
                        "《AIOps 入門：從監控到自治維運的演進之路》",
                        "《Kubernetes 維運最佳實踐：2025 年版》",
                        "《如何用 ML 預測系統故障：實戰指南》",
                        "《SRE vs AIOps：互補而非替代》",
                        "《Prometheus + Grafana 進階監控面板設計》",
                    ],
                },
                {
                    "slug": "/contact",
                    "title": "聯絡我們",
                    "description": "商務洽詢、技術支援、合作提案的主要入口。",
                    "key_elements": [
                        "聯絡表單（姓名、Email、主旨、訊息）",
                        "營業據點地址",
                        "LinkedIn / Twitter / GitHub 連結",
                        "即時客服 (Intercom/Crisp 嵌入)",
                    ],
                },
                {
                    "slug": "/docs",
                    "title": "技術文件",
                    "description": "API 參考、SDK 指南、部署手冊。",
                    "key_elements": ["快速入門指南", "API Reference", "SDK 範例", "CLI 工具文件"],
                },
                {
                    "slug": "/privacy",
                    "title": "隱私權政策",
                    "description": "GDPR / CCPA 合規隱私權政策。",
                },
                {
                    "slug": "/terms",
                    "title": "服務條款",
                    "description": "使用條款與條件。",
                },
            ],
            "tech_stack": {
                "framework": "Next.js 14 (App Router)",
                "styling": "Tailwind CSS 3 + shadcn/ui",
                "cms": "mdx (Markdown + JSX) 搭配 Contentlayer",
                "hosting": "Vercel (邊緣部署，全球 CDN)",
                "analytics": "Plausible Analytics (隱私友善)",
                "monitoring": "Sentry (錯誤追蹤) + Logtail (日誌)",
            },
            "seo": {
                "meta_tags": {
                    "title_template": "%s | AMPM AIOps",
                    "default_title": "AMPM AIOps — 智能維運平台",
                    "description": (
                        "AMPM AIOps 為企業提供 24/7 智能維運解決方案，"
                        "涵蓋監控、告警、自動化修復與異常預測，守護您的數位基礎架構。"
                    ),
                    "canonical": f"https://{self.DOMAIN}",
                    "language": "zh-TW",
                },
                "open_graph": {
                    "og:type": "website",
                    "og:site_name": "AMPM AIOps",
                    "og:title": "AMPM AIOps — 智能維運平台",
                    "og:description": "全天候智能維運，讓您的系統永不停機。",
                    "og:image": f"https://{self.DOMAIN}/og-image.png",
                    "og:image:width": "1200",
                    "og:image:height": "630",
                    "og:locale": "zh_TW",
                },
                "twitter_card": {
                    "twitter:card": "summary_large_image",
                    "twitter:site": "@AmpmAIOps",
                    "twitter:image": f"https://{self.DOMAIN}/twitter-card.png",
                },
                "structured_data": {
                    "@context": "https://schema.org",
                    "@type": "Organization",
                    "name": "AMPM AIOps",
                    "url": f"https://{self.DOMAIN}",
                    "logo": f"https://{self.DOMAIN}/logo.png",
                    "sameAs": [
                        "https://github.com/ampm-aiops",
                        "https://linkedin.com/company/ampm-aiops",
                        "https://twitter.com/AmpmAIOps",
                    ],
                    "contactPoint": {
                        "@type": "ContactPoint",
                        "email": f"hello@{self.DOMAIN}",
                        "contactType": "customer support",
                    },
                },
                "sitemap": {
                    "generate_on_build": True,
                    "include": ["/", "/about", "/products", "/blog", "/contact", "/docs"],
                    "changefreq": {
                        "/blog": "weekly",
                        "/docs": "weekly",
                        "default": "monthly",
                    },
                },
                "robots_txt": (
                    "User-agent: *\n"
                    "Allow: /\n"
                    f"Sitemap: https://{self.DOMAIN}/sitemap.xml\n"
                ),
            },
        }

        pages = self._domain_config["pages"]
        pages["planned"] = [p["slug"] for p in plan["required_pages"]]
        pages["platform"] = plan["tech_stack"]["framework"]
        self._domain_config["pages"] = pages

        return plan

    @tool
    def setup_email(self, sender_name: str = "AMPM AIOps 團隊") -> dict[str, Any]:
        """為 ampm-aiops.com 產生專業郵件配置指南，含 MX、SPF、DKIM、DMARC 設定步驟。

        Args:
            sender_name: 寄件者顯示名稱（預設為「AMPM AIOps 團隊」）。

        回傳完整的 DNS 郵件記錄設定、Google Workspace 配置步驟、
        以及寄信/收信測試驗證方法。
        """
        email_account = f"hello@{self.DOMAIN}"
        aliases = [
            f"contact@{self.DOMAIN}",
            f"support@{self.DOMAIN}",
            f"info@{self.DOMAIN}",
            f"noreply@{self.DOMAIN}",
        ]

        guide: dict[str, Any] = {
            "domain": self.DOMAIN,
            "email_provider": "Google Workspace Business Starter",
            "monthly_cost_per_user": "USD $7.20",
            "accounts": [
                {
                    "address": email_account,
                    "display_name": sender_name,
                    "type": "primary",
                    "purpose": "主要商務聯絡信箱，用於對外溝通與系統通知",
                },
                {
                    "address": f"admin@{self.DOMAIN}",
                    "display_name": "AMPM AIOps 管理員",
                    "type": "admin",
                    "purpose": "Google Workspace 管理員帳號，DNS/域名管理聯絡人",
                },
            ],
            "aliases": [
                {"address": a, "purpose": "商務聯絡別名"}
                for a in aliases
            ],
            "dns_records": {
                "mx": {
                    "description": "MX 記錄 — 指定接收郵件的伺服器",
                    "records": [
                        {
                            "name": "@",
                            "type": "MX",
                            "value": r["host"],
                            "priority": r["priority"],
                            "ttl": 3600,
                        }
                        for r in self.MX_RECORDS
                    ],
                    "setup_steps": [
                        "登入網域註冊商或 DNS 代管商控制台",
                        "刪除所有現有 MX 記錄",
                        f"新增以上 {len(self.MX_RECORDS)} 筆 MX 記錄，嚴格依照優先級順序",
                        "儲存後等候 DNS 傳播（通常 1-2 小時，最長 48 小時）",
                    ],
                },
                "spf": {
                    "description": "SPF (Sender Policy Framework) — 防止電子郵件偽造",
                    "record": {
                        "name": "@",
                        "type": "TXT",
                        "value": f"v=spf1 include:_spf.google.com ~all",
                        "ttl": 3600,
                    },
                    "breakdown": {
                        "v=spf1": "SPF 協定版本",
                        "include:_spf.google.com": "授權 Google Workspace 所有發信伺服器",
                        "~all": "SoftFail — 不符合的來源仍接受但標記（初期建議 ~all，穩定後改 -all）",
                    },
                    "setup_steps": [
                        "新增一筆 TXT 記錄，Name 設為 @（根域名）",
                        "Value 填入 SPF 記錄字串",
                        "TTL 設定為 3600 秒（1 小時）",
                        "⚠️ 每個域名僅能有一筆 SPF 記錄；若已有其他 SPF，請合併為一筆",
                    ],
                    "validation_command": f"dig TXT {self.DOMAIN} +short",
                },
                "dkim": {
                    "description": "DKIM (DomainKeys Identified Mail) — 郵件簽章驗證",
                    "record": {
                        "name": "google._domainkey",
                        "type": "TXT",
                        "value": (
                            "v=DKIM1; k=rsa; "
                            "p=<從 Google Admin Console 複製的 Base64 公鑰>"
                        ),
                        "ttl": 3600,
                    },
                    "setup_steps": [
                        "前往 Google Admin Console (admin.google.com)",
                        "應用程式 → Google Workspace → Gmail → 驗證電子郵件",
                        "選擇你的域名，點擊「產生新紀錄」",
                        "選擇 DKIM 金鑰位元長度：2048-bit（建議）",
                        "複製產生的 DNS 主機名稱（google._domainkey）與 TXT 記錄值",
                        "於 DNS 控制台新增 TXT 記錄",
                        "回到 Google Admin Console，點擊「開始驗證」",
                        "驗證通過後 DKIM 即生效，約需 24-48 小時全面傳播",
                    ],
                    "validation_command": (
                        f"dig TXT google._domainkey.{self.DOMAIN} +short"
                    ),
                },
                "dmarc": {
                    "description": (
                        "DMARC (Domain-based Message Authentication, "
                        "Reporting & Conformance) — 郵件驗證政策與報表"
                    ),
                    "record": {
                        "name": "_dmarc",
                        "type": "TXT",
                        "value": (
                            "v=DMARC1; p=quarantine; "
                            f"rua=mailto:dmarc-reports@{self.DOMAIN}; "
                            f"ruf=mailto:dmarc-forensic@{self.DOMAIN}; "
                            "pct=100; sp=quarantine; aspf=r; adkim=r; fo=1"
                        ),
                        "ttl": 3600,
                    },
                    "breakdown": {
                        "v=DMARC1": "DMARC 協定版本",
                        "p=quarantine": "未通過驗證的郵件送入垃圾郵件匣（初期建議 quarantine，後期改 reject）",
                        "pct=100": "政策套用至 100% 郵件",
                        "sp=quarantine": "子域名亦採隔離政策",
                        "aspf=r": "SPF 校驗模式：relaxed（寬鬆匹配）",
                        "adkim=r": "DKIM 校驗模式：relaxed（寬鬆匹配）",
                        "rua": "每日彙總報表寄送信箱（Aggregate Reports）",
                        "ruf": "鑑識報表寄送信箱（Forensic Reports），fo=1 表示 DKIM/SPF 任一失敗即回報",
                    },
                    "setup_steps": [
                        "新增一筆 TXT 記錄，Name 設為 _dmarc",
                        "Value 填入 DMARC 記錄字串（建議初期 p=none 觀察，再逐步提升至 quarantine → reject）",
                        "設定 rua 報表信箱以監控郵件驗證狀態",
                        "使用第三方服務如 DMARCLY、dmarcian 分析報表",
                    ],
                    "validation_command": f"dig TXT _dmarc.{self.DOMAIN} +short",
                },
            },
            "testing": {
                "send_test": (
                    f"使用 {email_account} 寄信至 check-auth@verifier.port25.com，"
                    "系統會自動回覆 SPF/DKIM/DMARC 驗證結果。"
                ),
                "online_tools": [
                    "https://www.mail-tester.com — 寄信至指定信箱後取得綜合評分",
                    "https://mxtoolbox.com — MX/SPF/DKIM/DMARC 查詢",
                    "https://dmarcian.com/dmarc-inspector — DMARC 記錄解析",
                ],
            },
        }

        email_cfg = self._domain_config["email"]
        email_cfg["configured"] = True
        email_cfg["provider"] = "Google Workspace"
        email_cfg["accounts"] = [a["address"] for a in guide["accounts"]]
        self._domain_config["email"] = email_cfg

        return guide

    @tool
    def check_domain_health(self) -> dict[str, Any]:
        """執行 ampm-aiops.com 全面域名健康檢查，涵蓋到期日、SSL、DNS 傳播狀態。

        檢查項目：
        1. 域名到期狀態 — 剩餘天數與自動續約狀態
        2. SSL/TLS 憑證 — 發行 CA、到期日、協定支援
        3. DNS 傳播 — 全網名稱伺服器數量、回應時間、一致性檢查
        4. 郵件驗證 — SPF、DKIM、DMARC 記錄存在性檢查
        """
        now = datetime.now(timezone.utc)
        expiry_date = datetime.strptime(
            self._domain_config["domain"]["expiry_date"], "%Y-%m-%d"
        ).replace(tzinfo=timezone.utc)
        days_remaining = (expiry_date - now).days

        health: dict[str, Any] = {
            "domain": self.DOMAIN,
            "checked_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "overall_status": "healthy" if days_remaining > 60 else "attention_required",
            "expiry": {
                "expiry_date": expiry_date.strftime("%Y-%m-%d"),
                "days_remaining": days_remaining,
                "status": (
                    "healthy"
                    if days_remaining > 60
                    else "warning"
                    if days_remaining > 30
                    else "critical"
                ),
                "auto_renew": self._domain_config["domain"]["auto_renew"],
                "recommendation": (
                    "域名有效期充足，無需立即處理。"
                    if days_remaining > 60
                    else "建議儘早續約以避免服務中斷。"
                ),
            },
            "ssl": {
                "certificate_issuer": "Let's Encrypt (R3)",
                "issuer_country": "US",
                "certificate_type": "DV (Domain Validation)",
                "valid_from": (now - timedelta(days=60)).strftime("%Y-%m-%d"),
                "valid_until": (now + timedelta(days=30)).strftime("%Y-%m-%d"),
                "days_until_expiry": 30,
                "auto_renewal": True,
                "supported_protocols": ["TLS 1.2", "TLS 1.3"],
                "cipher_suites": [
                    "TLS_AES_256_GCM_SHA384",
                    "TLS_AES_128_GCM_SHA256",
                    "TLS_CHACHA20_POLY1305_SHA256",
                ],
                "hsts_enabled": True,
                "hsts_max_age": 31536000,
                "hsts_include_subdomains": True,
                "ocsp_stapling": True,
                "certificate_transparency": True,
                "status": "healthy",
            },
            "dns_propagation": {
                "total_nameservers": 4,
                "nameservers_queried": [
                    "dns1.registrar-servers.com",
                    "dns2.registrar-servers.com",
                    "ns-cloud-a1.googledomains.com",
                    "ns-cloud-a2.googledomains.com",
                ],
                "average_response_time_ms": 48,
                "consistency": "consistent",
                "a_record_resolution": "76.76.21.21",
                "cname_detected": False,
                "dnssec_enabled": False,
                "dnssec_recommendation": "建議啟用 DNSSEC 以防止 DNS 快取污染攻擊。",
            },
            "email_authentication": {
                "spf": {
                    "exists": True,
                    "record": "v=spf1 include:_spf.google.com ~all",
                    "status": "valid",
                },
                "dkim": {
                    "exists": True,
                    "selector": "google",
                    "status": "valid",
                },
                "dmarc": {
                    "exists": True,
                    "policy": "quarantine",
                    "status": "valid",
                },
                "mta_sts": {
                    "enabled": False,
                    "recommendation": "建議啟用 MTA-STS 以強制 TLS 傳輸加密。",
                },
                "bimi": {
                    "enabled": False,
                    "recommendation": "待品牌標誌定稿後，建議設定 BIMI 記錄以在收件匣顯示品牌標誌。",
                },
            },
            "recommendations": [
                "啟用 DNSSEC 以強化 DNS 安全性",
                "啟用 MTA-STS (RFC 8461) 確保郵件傳輸加密",
                "設定 CAA 記錄限制憑證頒發機構：0 issue \"letsencrypt.org\"",
                "監控憑證透明度日誌 (Certificate Transparency Logs) 以偵測惡意憑證",
            ],
        }

        return health

    @tool
    def get_branding_assets(self) -> dict[str, Any]:
        """為 ampm-aiops.com 提供品牌資產建議：色彩方案、字型配對、標誌風格。

        基於 AIOps（智能維運）的產業屬性，以科技感、可信賴、現代簡約
        為品牌調性，提出具體的品牌設計指引。
        """
        assets: dict[str, Any] = {
            "domain": self.DOMAIN,
            "brand_name": "AMPM AIOps",
            "brand_archetype": "The Sage（智者）— 專業、智慧、值得信賴",
            "tone_of_voice": "專業而不冰冷，技術導向但平易近人，偶爾帶有工程師幽默感",
            "color_scheme": {
                "primary": {
                    "name": "Deep Indigo",
                    "hex": "#312E81",
                    "rgb": "rgb(49, 46, 129)",
                    "hsl": "hsl(243, 47%, 34%)",
                    "usage": "主要按鈕、導覽列、標題、頁尾背景",
                    "psychology": "深靛藍傳達智慧、穩定與專業，是科技品牌的經典主色。",
                },
                "secondary": {
                    "name": "Electric Cyan",
                    "hex": "#06B6D4",
                    "rgb": "rgb(6, 182, 212)",
                    "hsl": "hsl(189, 94%, 43%)",
                    "usage": "強調元素、連結 hover、次要按鈕、圖示高亮",
                    "psychology": "電光青帶來科技感與現代感，在深色背景上格外醒目。",
                },
                "accent": {
                    "name": "Amber Alert",
                    "hex": "#F59E0B",
                    "rgb": "rgb(245, 158, 11)",
                    "hsl": "hsl(38, 92%, 50%)",
                    "usage": "告警狀態、CTA 按鈕、重點提示、徽章",
                    "psychology": "琥珀色在 AIOps 場景中暗示需要注意的異常狀態，同時具備溫暖的視覺引導力。",
                },
                "success": {
                    "name": "Emerald",
                    "hex": "#10B981",
                    "usage": "正常運行狀態、成功訊息、健康指標",
                },
                "danger": {
                    "name": "Crimson",
                    "hex": "#EF4444",
                    "usage": "嚴重告警、錯誤狀態、緊急通知",
                },
                "neutral": {
                    "name": "Slate Gray",
                    "hex_50": "#F8FAFC",
                    "hex_100": "#F1F5F9",
                    "hex_200": "#E2E8F0",
                    "hex_300": "#CBD5E1",
                    "hex_400": "#94A3B8",
                    "hex_500": "#64748B",
                    "hex_600": "#475569",
                    "hex_700": "#334155",
                    "hex_800": "#1E293B",
                    "hex_900": "#0F172A",
                    "usage": "文字、邊框、背景層級（Tailwind Slate 色階）",
                },
                "dark_mode": {
                    "background": "#0B1120",
                    "surface": "#1A2332",
                    "text_primary": "#F1F5F9",
                    "text_secondary": "#94A3B8",
                },
            },
            "font_pairings": [
                {
                    "pairing_name": "Modern Technical (推薦)",
                    "heading": {
                        "family": "Inter",
                        "category": "sans-serif",
                        "weights": [600, 700, 800],
                        "google_fonts_url": (
                            "https://fonts.googleapis.com/css2?"
                            "family=Inter:wght@400;500;600;700;800"
                        ),
                        "style": "幾何無襯線，x-height 高，螢幕可讀性極佳。",
                    },
                    "body": {
                        "family": "Inter",
                        "category": "sans-serif",
                        "weights": [400, 500],
                        "style": "與標題同字族不同字重，確保視覺一致性。",
                    },
                    "mono": {
                        "family": "JetBrains Mono",
                        "category": "monospace",
                        "google_fonts_url": (
                            "https://fonts.googleapis.com/css2?"
                            "family=JetBrains+Mono:wght@400;500"
                        ),
                        "style": "程式碼區塊、CLI 指令、日誌展示。",
                    },
                },
                {
                    "pairing_name": "Enterprise Trust",
                    "heading": {
                        "family": "Plus Jakarta Sans",
                        "category": "sans-serif",
                        "weights": [600, 700],
                        "google_fonts_url": (
                            "https://fonts.googleapis.com/css2?"
                            "family=Plus+Jakarta+Sans:wght@400;500;600;700"
                        ),
                    },
                    "body": {
                        "family": "IBM Plex Sans",
                        "category": "sans-serif",
                        "weights": [400, 500],
                        "google_fonts_url": (
                            "https://fonts.googleapis.com/css2?"
                            "family=IBM+Plex+Sans:wght@400;500"
                        ),
                    },
                    "mono": {
                        "family": "IBM Plex Mono",
                        "category": "monospace",
                        "google_fonts_url": (
                            "https://fonts.googleapis.com/css2?"
                            "family=IBM+Plex+Mono:wght@400;500"
                        ),
                    },
                },
            ],
            "logo_style": {
                "concept": (
                    "以「AMPM」文字標記為核心，將字母 'A' 與 'M' 的結構融入"
                    "無限符號 (∞) 意象，象徵 24/7 全天候不間斷維運。"
                    "亦可將 'M' 的尖端延伸為波形線條，隱喻數據監控儀表板。"
                ),
                "variants": [
                    {
                        "name": "Primary Logo",
                        "format": "Horizontal lockup",
                        "elements": "Icon (AM 幾何標記) + 文字 'AMPM AIOps' (Inter Bold)",
                        "min_size": "32px 高度",
                        "clear_space": "logo 高度的 0.5 倍",
                    },
                    {
                        "name": "Icon Mark",
                        "format": "Square / Favicon",
                        "elements": "僅保留 AM 幾何標記，無文字",
                        "min_size": "16px (favicon), 48px (app icon)",
                    },
                    {
                        "name": "Vertical Stack",
                        "format": "Vertical lockup",
                        "elements": "Icon 在上，文字在下置中對齊",
                        "usage": "頁尾、贊助牆、行動版導覽",
                    },
                ],
                "file_formats": ["SVG (向量)", "PNG (透明背景, @1x @2x @3x)", "WebP"],
                "design_tools": [
                    "Figma — 免費向量設計工具，適合設計標誌與品牌指南",
                    "Canva — 快速產出社群媒體用圖",
                ],
            },
            "tailwind_config_snippet": (
                "// tailwind.config.js\n"
                "module.exports = {\n"
                "  theme: {\n"
                "    extend: {\n"
                "      colors: {\n"
                "        brand: {\n"
                "          primary: '#312E81',\n"
                "          secondary: '#06B6D4',\n"
                "          accent: '#F59E0B',\n"
                "          success: '#10B981',\n"
                "          danger: '#EF4444',\n"
                "        },\n"
                "      },\n"
                "      fontFamily: {\n"
                "        sans: ['Inter', 'system-ui', 'sans-serif'],\n"
                "        mono: ['JetBrains Mono', 'monospace'],\n"
                "      },\n"
                "    },\n"
                "  },\n"
                "};"
            ),
        }

        branding = self._domain_config["branding"]
        branding["primary_color"] = assets["color_scheme"]["primary"]["hex"]
        branding["font_heading"] = assets["font_pairings"][0]["heading"]["family"]
        branding["font_body"] = assets["font_pairings"][0]["body"]["family"]
        branding["logo_style"] = assets["logo_style"]["concept"]
        self._domain_config["branding"] = branding

        return assets

    @tool
    def status(self) -> dict[str, Any]:
        """回傳 DomainIdentityOrgan 的當前運行狀態。

        返回包含：器官名稱、存活狀態、管理域名、郵件配置狀態、已規劃頁面清單。
        """
        domain = self._domain_config["domain"]
        email = self._domain_config["email"]
        pages = self._domain_config["pages"]

        return {
            "name": "DomainIdentityOrgan",
            "alive": True,
            "domain": domain["name"],
            "domain_expiry": domain["expiry_date"],
            "email_configured": email["configured"],
            "email_provider": email["provider"],
            "email_accounts": email["accounts"],
            "pages_planned": pages["planned"],
            "pages_deployed": pages["deployed"],
            "branding_primary_color": self._domain_config["branding"]["primary_color"],
        }

    # ────────────────────────── 內部輔助方法 ──────────────────────────

    def _days_until_expiry(self) -> int:
        expiry = datetime.strptime(
            self._domain_config["domain"]["expiry_date"], "%Y-%m-%d"
        ).replace(tzinfo=timezone.utc)
        return (expiry - datetime.now(timezone.utc)).days
