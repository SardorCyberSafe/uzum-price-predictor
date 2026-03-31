"""
UZUM MARKET — NARX BASHORAT TIZIMI
Uzum.uz saytidan jonli ma'lumot olib, ML model o'qitadi.

O'rnatish (o'z kompyuteringizda):
  pip install requests pandas numpy scikit-learn joblib selenium
  # Yoki Playwright:
  pip install playwright && playwright install chromium

Ishga tushirish:
  python uzum_price_predictor.py
"""

import requests
import pandas as pd
import numpy as np
import re
import os
import json
import time
from urllib.parse import quote
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder
import joblib
import warnings

warnings.filterwarnings("ignore")


# ========================
# KATEGORIYALAR VA PATTERNLAR
# ========================
CATEGORIES = {
    "ram": {
        "name": "Operativ pamyat (RAM)",
        "query": "оперативная память",
        "patterns": {
            "has_ddr3": r"ddr3",
            "has_ddr4": r"ddr4",
            "has_ddr5": r"ddr5",
            "has_4gb": r"4\s*gb",
            "has_8gb": r"8\s*gb",
            "has_16gb": r"16\s*gb",
            "has_32gb": r"32\s*gb",
            "has_64gb": r"64\s*gb",
            "has_laptop": r"laptop|sodimm|notebook",
            "has_gaming": r"gaming|rgb|hyperx|corsair|g\.skill",
            "has_kit": r"kit|2\s*x|2x",
            "has_2400": r"2400",
            "has_2666": r"2666",
            "has_3200": r"3200",
            "has_3600": r"3600",
            "has_4800": r"4800",
            "has_5600": r"5600",
        },
    },
    "phone": {
        "name": "Telefonlar",
        "query": "смартфон",
        "patterns": {
            "has_samsung": r"samsung",
            "has_iphone": r"iphone|apple",
            "has_xiaomi": r"xiaomi|redmi|poco",
            "has_realme": r"realme",
            "has_64gb": r"64\s*gb",
            "has_128gb": r"128\s*gb",
            "has_256gb": r"256\s*gb",
            "has_512gb": r"512\s*gb",
            "has_5g": r"5g",
            "has_pro": r"pro\b",
            "has_ultra": r"ultra",
        },
    },
    "laptop": {
        "name": "Noutbuklar",
        "query": "ноутбук",
        "patterns": {
            "has_macbook": r"macbook",
            "has_lenovo": r"lenovo",
            "has_hp": r"\bhp\b",
            "has_asus": r"asus",
            "has_acer": r"acer",
            "has_i5": r"i5",
            "has_i7": r"i7",
            "has_ryzen5": r"ryzen\s*5",
            "has_ryzen7": r"ryzen\s*7",
            "has_8gb": r"8\s*gb",
            "has_16gb": r"16\s*gb",
            "has_256ssd": r"256",
            "has_512ssd": r"512",
            "has_gaming": r"gaming|rtx|gtx",
        },
    },
    "headphone": {
        "name": "Quloqchinlar",
        "query": "наушники",
        "patterns": {
            "has_airpods": r"airpods",
            "has_samsung": r"samsung",
            "has_jbl": r"\bjbl\b",
            "has_sony": r"\bsony\b",
            "has_wireless": r"wireless|bluetooth",
            "has_anc": r"anc|noise",
            "has_pro": r"pro\b",
        },
    },
    "watch": {
        "name": "Soatlar",
        "query": "умные часы",
        "patterns": {
            "has_apple": r"apple",
            "has_samsung": r"samsung",
            "has_xiaomi": r"xiaomi",
            "has_huawei": r"huawei",
            "has_pro": r"pro\b",
            "has_ultra": r"ultra",
            "has_gps": r"\bgps\b",
            "has_nfc": r"\bnfc\b",
        },
    },
    "tv": {
        "name": "Televizorlar",
        "query": "телевизор",
        "patterns": {
            "has_samsung": r"samsung",
            "has_lg": r"\blg\b",
            "has_tcl": r"\btcl\b",
            "has_hisense": r"hisense",
            "has_43": r"43",
            "has_50": r"50",
            "has_55": r"55",
            "has_65": r"65",
            "has_4k": r"4k|ultra\s*hd",
            "has_oled": r"oled",
            "has_qled": r"qled",
        },
    },
    "tablet": {
        "name": "Planshetlar",
        "query": "планшет",
        "patterns": {
            "has_ipad": r"ipad",
            "has_samsung": r"samsung",
            "has_lenovo": r"lenovo",
            "has_xiaomi": r"xiaomi",
            "has_64gb": r"64\s*gb",
            "has_128gb": r"128\s*gb",
            "has_256gb": r"256\s*gb",
            "has_wifi": r"wifi",
            "has_lte": r"lte|4g",
        },
    },
    "fridge": {
        "name": "Muzlatgichlar",
        "query": "холодильник",
        "patterns": {
            "has_samsung": r"samsung",
            "has_lg": r"\blg\b",
            "has_beko": r"\bbeko\b",
            "has_haier": r"haier",
            "has_no_frost": r"no\s*frost",
            "has_200": r"200",
            "has_300": r"300",
            "has_400": r"400",
            "has_inverter": r"inverter",
        },
    },
    "washer": {
        "name": "Kir yuvish mashinalari",
        "query": "стиральная машина",
        "patterns": {
            "has_samsung": r"samsung",
            "has_lg": r"\blg\b",
            "has_beko": r"\bbeko\b",
            "has_haier": r"haier",
            "has_5kg": r"5\s*kg",
            "has_6kg": r"6\s*kg",
            "has_7kg": r"7\s*kg",
            "has_8kg": r"8\s*kg",
            "has_inverter": r"inverter",
        },
    },
}


# ========================
# UZUM SCRAPER
# ========================
class UzumScraper:
    """Uzum.uz saytidan mahsulot ma'lumotlarini olish"""

    def __init__(self, method="selenium"):
        self.method = method
        self.driver = None
        self.browser = None
        self.pw = None
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "application/json",
                "Accept-Language": "ru-RU,ru;q=0.9,uz;q=0.8",
                "Origin": "https://uzum.uz",
                "Referer": "https://uzum.uz/",
            }
        )

    def _init_selenium(self):
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options

            opts = Options()
            opts.add_argument("--headless=new")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--disable-gpu")
            opts.add_argument("--window-size=1920,1080")
            opts.add_argument("--disable-blink-features=AutomationControlled")
            opts.add_experimental_option("excludeSwitches", ["enable-logging"])
            self.driver = webdriver.Chrome(options=opts)
            self.driver.set_page_load_timeout(30)
            print("  ✅ Selenium ChromeDriver ishga tushdi")
            return True
        except Exception as e:
            print(f"  ❌ Selenium: {e}")
            return False

    def _init_playwright(self):
        try:
            from playwright.sync_api import sync_playwright

            self.pw = sync_playwright().start()
            self.browser = self.pw.chromium.launch(headless=True)
            print("  ✅ Playwright ishga tushdi")
            return True
        except Exception as e:
            print(f"  ❌ Playwright: {e}")
            return False

    def _parse_price(self, text):
        """Narx matnidan son ajratish"""
        if not text:
            return 0
        digits = re.sub(r"[^\d]", "", text)
        return int(digits) if digits else 0

    def _extract_from_html(self, html, query):
        """HTML dan mahsulotlarni regex bilan ajratish"""
        products = []
        # JSON ichidan ma'lumot olish
        json_pattern = r'"title"\s*:\s*"([^"]+)"'
        price_pattern = r'"amount"\s*:\s*(\d+)'
        brand_pattern = r'"brand"\s*:\s*\{\s*"name"\s*:\s*"([^"]*)"'

        titles = re.findall(json_pattern, html)
        prices = re.findall(price_pattern, html)
        brands = re.findall(brand_pattern, html)

        for i in range(min(len(titles), len(prices))):
            title = titles[i]
            price = int(prices[i])
            brand = brands[i] if i < len(brands) else ""
            if price > 0 and len(title) > 3:
                products.append(
                    {
                        "name": title,
                        "price": price,
                        "brand": brand,
                        "category": query,
                        "rating": 0,
                        "review_count": 0,
                        "sold_count": 0,
                        "discount": 0,
                    }
                )
        return products

    def scrape_selenium(self, query, max_pages=3):
        """Selenium orqali scraping"""
        if not self.driver and not self._init_selenium():
            return []

        all_products = []
        for page in range(1, max_pages + 1):
            url = f"https://uzum.uz/ru/search?query={quote(query)}&page={page}"
            try:
                self.driver.get(url)
                time.sleep(4)

                # Mahsulot kartochkalarini topish
                cards = self.driver.find_elements(
                    "css selector", "a[href*='/product/']"
                )
                if not cards:
                    cards = self.driver.find_elements(
                        "css selector", "[data-test='productTile']"
                    )

                if not cards:
                    print(f"    Sahifa {page}: mahsulot topilmadi")
                    break

                seen = set()
                for card in cards[:60]:
                    try:
                        href = card.get_attribute("href") or ""
                        if href in seen:
                            continue
                        seen.add(href)

                        name_el = None
                        for selector in [
                            "[data-test='product-title']",
                            "span[class*='title']",
                            "h3",
                        ]:
                            try:
                                name_el = card.find_element("css selector", selector)
                                break
                            except:
                                pass

                        price_el = None
                        for selector in [
                            "[data-test='product-price']",
                            "span[class*='price']",
                            "span[class*='sum']",
                        ]:
                            try:
                                price_el = card.find_element("css selector", selector)
                                break
                            except:
                                pass

                        name = name_el.text.strip() if name_el else ""
                        price_text = price_el.text.strip() if price_el else ""
                        price = self._parse_price(price_text)

                        brand = ""
                        try:
                            brand_el = card.find_element(
                                "css selector", "[data-test='product-brand']"
                            )
                            brand = brand_el.text.strip()
                        except:
                            pass

                        if name and price > 0:
                            all_products.append(
                                {
                                    "name": name,
                                    "price": price,
                                    "brand": brand,
                                    "category": query,
                                    "rating": 0,
                                    "review_count": 0,
                                    "sold_count": 0,
                                    "discount": 0,
                                }
                            )
                    except:
                        continue

                print(f"    Sahifa {page}: {len(all_products)} mahsulot")
                time.sleep(2)

            except Exception as e:
                print(f"    Xatolik sahifa {page}: {e}")
                break

        return all_products

    def scrape_playwright(self, query, max_pages=3):
        """Playwright orqali scraping"""
        if not self.browser and not self._init_playwright():
            return []

        all_products = []
        for page in range(1, max_pages + 1):
            url = f"https://uzum.uz/ru/search?query={quote(query)}&page={page}"
            pg = None
            try:
                pg = self.browser.new_page()
                pg.goto(url, wait_until="networkidle", timeout=30000)
                pg.wait_for_timeout(3000)

                cards = pg.query_selector_all('a[href*="/product/"]')
                if not cards:
                    cards = pg.query_selector_all('[data-test="productTile"]')

                if not cards:
                    pg.close()
                    break

                seen = set()
                for card in cards[:60]:
                    try:
                        href = card.get_attribute("href") or ""
                        if href in seen:
                            continue
                        seen.add(href)

                        name_el = card.query_selector('[data-test="product-title"]')
                        price_el = card.query_selector('[data-test="product-price"]')
                        brand_el = card.query_selector('[data-test="product-brand"]')

                        name = name_el.inner_text().strip() if name_el else ""
                        price_text = price_el.inner_text().strip() if price_el else ""
                        price = self._parse_price(price_text)
                        brand = brand_el.inner_text().strip() if brand_el else ""

                        if name and price > 0:
                            all_products.append(
                                {
                                    "name": name,
                                    "price": price,
                                    "brand": brand,
                                    "category": query,
                                    "rating": 0,
                                    "review_count": 0,
                                    "sold_count": 0,
                                    "discount": 0,
                                }
                            )
                    except:
                        continue

                print(f"    Sahifa {page}: {len(all_products)} mahsulot")
                pg.close()
                time.sleep(2)

            except Exception as e:
                print(f"    Xatolik sahifa {page}: {e}")
                if pg:
                    pg.close()
                break

        return all_products

    def scrape_api(self, query, max_pages=3):
        """API orqali (agar ishlasa)"""
        all_products = []
        endpoints = [
            "https://api.uzum.uz/api/product/search",
            "https://api.umarket.uz/api/v2/search/product",
        ]
        for endpoint in endpoints:
            for page in range(1, max_pages + 1):
                try:
                    resp = self.session.get(
                        endpoint,
                        params={"q": query, "page": page, "size": 60},
                        timeout=15,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        items = data.get("payload", {}).get(
                            "items", data.get("result", {}).get("items", [])
                        )
                        for item in items:
                            price_data = item.get("price", {})
                            price = (
                                price_data.get("amount", 0)
                                if isinstance(price_data, dict)
                                else price_data
                            )
                            brand_data = item.get("brand", {})
                            brand = (
                                brand_data.get("name", "")
                                if isinstance(brand_data, dict)
                                else ""
                            )
                            cat_data = item.get("category", {})
                            cat = (
                                cat_data.get("name", "")
                                if isinstance(cat_data, dict)
                                else ""
                            )
                            if price > 0:
                                all_products.append(
                                    {
                                        "name": item.get("title", ""),
                                        "price": price,
                                        "brand": brand,
                                        "category": cat or query,
                                        "rating": item.get("rating", 0),
                                        "review_count": item.get("reviewCount", 0),
                                        "sold_count": item.get("soldCount", 0),
                                        "discount": item.get("discountPercent", 0),
                                    }
                                )
                        print(f"    API sahifa {page}: {len(items)} mahsulot")
                        if not items:
                            break
                    else:
                        break
                except:
                    break
                time.sleep(1)
            if all_products:
                break
        return all_products

    def scrape(self, query, max_pages=3):
        """Asosiy scraping funksiyasi"""
        print(f"\n  🔍 Qidirilmoqda: '{query}' (method: {self.method})")

        if self.method == "selenium":
            return self.scrape_selenium(query, max_pages)
        elif self.method == "playwright":
            return self.scrape_playwright(query, max_pages)
        elif self.method == "api":
            return self.scrape_api(query, max_pages)
        else:
            # Auto: avval API, keyin Playwright, keyin Selenium
            products = self.scrape_api(query, max_pages)
            if products:
                return products
            products = self.scrape_playwright(query, max_pages)
            if products:
                return products
            products = self.scrape_selenium(query, max_pages)
            return products

    def scrape_product_by_url(self, url):
        """Bitta mahsulot URL dan ma'lumot olish"""
        if self.driver:
            try:
                self.driver.get(url)
                time.sleep(3)
                name = self.driver.find_element("css selector", "h1").text.strip()
                price_text = self.driver.find_element(
                    "css selector", "[data-test='product-price']"
                ).text.strip()
                price = self._parse_price(price_text)
                return {
                    "name": name,
                    "price": price,
                    "brand": "",
                    "category": "",
                    "rating": 0,
                    "review_count": 0,
                    "sold_count": 0,
                    "discount": 0,
                }
            except:
                pass
        return None

    def close(self):
        if self.driver:
            self.driver.quit()
        if self.browser:
            self.browser.close()
        if self.pw:
            self.pw.stop()


# ========================
# ML MODEL
# ========================
class UzumPricePredictor:
    def __init__(self):
        self.model = None
        self.feature_cols = []
        self.label_encoders = {}
        self.text_patterns = {}

    def prepare_data(self, df, text_patterns):
        if "old_price" not in df.columns:
            df["old_price"] = 0

        df["name_length"] = df["name"].str.len()
        df["word_count"] = df["name"].str.split().str.len()
        df["has_number"] = df["name"].str.contains(r"\d").astype(int)
        df["digit_count"] = df["name"].str.count(r"\d")
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        df = df.dropna(subset=["price"])
        df = df[df["price"] > 0]

        name_lower = df["name"].str.lower()
        for fname, pattern in text_patterns.items():
            df[fname] = name_lower.str.contains(pattern, regex=True).astype(int)

        for col in ["category", "brand"]:
            if col in df.columns:
                le = LabelEncoder()
                vals = df[col].fillna("unknown").astype(str)
                df[col + "_encoded"] = le.fit_transform(vals)
                self.label_encoders[col] = le

        base_cols = [
            "name_length",
            "word_count",
            "has_number",
            "digit_count",
            "rating",
            "review_count",
            "sold_count",
            "discount",
        ]
        self.feature_cols = (
            base_cols
            + list(text_patterns.keys())
            + [
                c + "_encoded"
                for c in self.label_encoders
                if c + "_encoded" in df.columns
            ]
        )
        self.feature_cols = [c for c in self.feature_cols if c in df.columns]
        self.text_patterns = text_patterns

        return df[self.feature_cols].fillna(0), df["price"]

    def train(self, df, text_patterns):
        print("\n" + "=" * 60)
        print("  MODEL O'QITILMOQDA")
        print("=" * 60)

        X, y = self.prepare_data(df, text_patterns)
        print(f"  Namuna: {len(X)} | Xususiyatlar: {len(self.feature_cols)}")
        print(f"  Narx: {y.min():,.0f} - {y.max():,.0f} so'm")

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        self.model = GradientBoostingRegressor(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.08,
            min_samples_split=4,
            subsample=0.85,
            random_state=42,
        )
        self.model.fit(X_train, y_train)

        y_pred = self.model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)

        print(f"  MAE: {mae:,.0f} | RMSE: {rmse:,.0f} | R²: {r2:.4f}")

        imp = pd.DataFrame(
            {
                "f": self.feature_cols,
                "i": self.model.feature_importances_,
            }
        ).sort_values("i", ascending=False)
        print(f"  Muhim: {', '.join(imp.head(5)['f'].tolist())}")
        return {"mae": mae, "rmse": rmse, "r2": r2}

    def predict(self, product_data):
        df = pd.DataFrame([product_data])
        if "old_price" not in df.columns:
            df["old_price"] = 0
        df["name_length"] = df["name"].str.len()
        df["word_count"] = df["name"].str.split().str.len()
        df["has_number"] = df["name"].str.contains(r"\d").astype(int)
        df["digit_count"] = df["name"].str.count(r"\d")

        name_lower = df["name"].str.lower()
        for fname, pattern in self.text_patterns.items():
            df[fname] = name_lower.str.contains(pattern, regex=True).astype(int)

        for col, le in self.label_encoders.items():
            if col in df.columns:
                df[col + "_encoded"] = (
                    df[col]
                    .fillna("unknown")
                    .astype(str)
                    .apply(lambda x: le.transform([x])[0] if x in le.classes_ else 0)
                )

        X = pd.DataFrame(0, index=[0], columns=self.feature_cols)
        for col in self.feature_cols:
            if col in df.columns:
                val = df[col].iloc[0]
                X.at[0, col] = val if pd.notna(val) else 0

        return max(self.model.predict(X)[0], 0)

    def save(self, path):
        os.makedirs(path, exist_ok=True)
        joblib.dump(self.model, f"{path}/model.pkl")
        joblib.dump(self.label_encoders, f"{path}/encoders.pkl")
        joblib.dump(self.feature_cols, f"{path}/feature_cols.pkl")
        joblib.dump(self.text_patterns, f"{path}/text_patterns.pkl")
        print(f"  💾 Saqlandi: {path}/")

    def load(self, path):
        self.model = joblib.load(f"{path}/model.pkl")
        self.label_encoders = joblib.load(f"{path}/encoders.pkl")
        self.feature_cols = joblib.load(f"{path}/feature_cols.pkl")
        self.text_patterns = joblib.load(f"{path}/text_patterns.pkl")


# ========================
# ASOSIY DASTUR
# ========================
def main():
    print("=" * 60)
    print("  UZUM MARKET — NARX BASHORAT")
    print("  Ma'lumot: uzum.uz/ru/search?query=...")
    print("=" * 60)

    print("\n📂 Kategoriyalar:")
    cat_list = list(CATEGORIES.keys())
    for i, key in enumerate(cat_list, 1):
        print(f"  {i}. {CATEGORIES[key]['name']}")
    print(f"  {len(cat_list) + 1}. Boshqa (o'z so'rovingiz)")

    print("\n🔧 Scraping usuli:")
    print("  1. selenium  (Chrome kerak)")
    print("  2. playwright (playwright install kerak)")
    print("  3. api       (faqat API)")
    print("  4. auto      (hammasini sinaydi)")

    method_choice = (
        input("\n👉 Usul tanlang [selenium]: ").strip().lower() or "selenium"
    )
    method_map = {"1": "selenium", "2": "playwright", "3": "api", "4": "auto"}
    method = method_map.get(method_choice, method_choice)

    cat_choice = input("👉 Kategoriya raqami: ").strip()
    cat_key = None
    try:
        idx = int(cat_choice) - 1
        if idx < len(cat_list):
            cat_key = cat_list[idx]
    except:
        pass

    if not cat_key:
        custom = input("🔍 Qidiruv so'zi: ").strip()
        if not custom:
            print("❌ Kiritilmadi!")
            return
        cat_key = "custom"
        CATEGORIES["custom"] = {
            "name": custom,
            "query": custom,
            "patterns": {},
        }

    cat = CATEGORIES[cat_key]
    print(f"\n✅ {cat['name']} — '{cat['query']}'")

    scraper = UzumScraper(method=method)
    predictor = UzumPricePredictor()

    # Ma'lumot yig'ish
    data_file = f"uzum_data_{cat_key}.csv"
    all_products = []

    if os.path.exists(data_file):
        use = input("  Tayyor fayl bor. Ishlatilsinmi? (ha/yoq) [ha]: ").lower()
        if use not in ("yoq", "n", "no"):
            all_products = pd.read_csv(data_file).to_dict("records")
            print(f"  ✅ {len(all_products)} mahsulot fayldan yuklandi")

    if not all_products:
        print(f"\n📡 Uzum.uz dan yig'ilmoqda...")
        products = scraper.scrape(cat["query"], max_pages=3)
        scraper.close()
        all_products.extend(products)

        if all_products:
            df = pd.DataFrame(all_products)
            df.to_csv(data_file, index=False, encoding="utf-8-sig")
            print(f"\n✅ {len(df)} mahsulot saqlandi: {data_file}")
        else:
            print("\n⚠️ Saytdan ma'lumot olinmadi!")
            print("\n📋 Yechimlar:")
            print("  1. pip install selenium")
            print("     → ChromeDriver o'rnating")
            print("  2. pip install playwright && playwright install chromium")
            print("  3. O'z kompyuteringizda ishga tushiring")
            return
    else:
        df = pd.DataFrame(all_products)

    if len(df) < 10:
        print(f"  ❌ Kam ma'lumot! ({len(df)} ta, kamida 10 ta kerak)")
        return

    # O'qitish
    metrics = predictor.train(df, cat["patterns"])
    model_path = f"model_{cat_key}"
    predictor.save(model_path)

    # Test bashoratlar
    print("\n" + "=" * 60)
    print("  TEST BASHORATLAR")
    print("=" * 60)

    test_items = df["name"].head(3).tolist()
    for name in test_items:
        product = {
            "name": name,
            "price": 0,
            "old_price": 0,
            "brand": "",
            "category": cat["name"],
            "rating": 4.5,
            "review_count": 30,
            "sold_count": 100,
            "discount": 10,
        }
        pred = predictor.predict(product)
        actual = df[df["name"] == name]["price"].values
        actual_str = f" (haqiqiy: {actual[0]:,.0f})" if len(actual) > 0 else ""
        print(f"  📦 {name}")
        print(f"  💰 Bashorat: {pred:,.0f} so'm{actual_str}")

    # Interaktiv
    print("\n" + "=" * 60)
    print("  INTERAKTIV — mahsulot nomi yoki URL kiriting")
    print("  Chiqish: exit")
    print("=" * 60)

    while True:
        user_input = input("\n📝 > ").strip()
        if user_input.lower() in ("exit", "chiqish", "q", "quit"):
            print("\n👋 Xayr!")
            break
        if not user_input:
            continue

        if user_input.startswith("http"):
            scraper2 = UzumScraper(method=method)
            product = scraper2.scrape_product_by_url(user_input)
            scraper2.close()
            if product:
                pred = predictor.predict(product)
                print(f"  📦 {product['name']}")
                print(f"  💰 {pred:,.0f} so'm")
            else:
                print("  ❌ Mahsulot topilmadi")
        else:
            product = {
                "name": user_input,
                "price": 0,
                "old_price": 0,
                "brand": "",
                "category": cat["name"],
                "rating": 4.5,
                "review_count": 30,
                "sold_count": 100,
                "discount": 10,
            }
            pred = predictor.predict(product)
            print(f"  📦 {user_input}")
            print(f"  💰 {pred:,.0f} so'm")


if __name__ == "__main__":
    main()
