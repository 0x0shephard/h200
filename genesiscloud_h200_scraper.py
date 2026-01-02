#!/usr/bin/env python3
"""
Genesis Cloud H200 GPU Price Scraper
Extracts H200 pricing from Genesis Cloud

Reference: https://www.genesiscloud.com/pricing
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
from typing import Dict, Optional


class GenesisCloudH200Scraper:
    """Scraper for Genesis Cloud H200 pricing"""

    def __init__(self):
        self.name = "GenesisCloud"
        self.base_url = "https://www.genesiscloud.com/pricing"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }

    def get_h200_prices(self) -> Dict[str, str]:
        """Main method to extract H200 prices from Genesis Cloud"""
        print(f"🔍 Fetching {self.name} H200 pricing...")
        print("=" * 80)

        h200_prices = {}

        methods = [
            ("Genesis Cloud Pricing Page Scraping", self._try_pricing_page),
            ("Selenium Scraper", self._try_selenium_scraper),
        ]

        for method_name, method_func in methods:
            print(f"\n📋 Method: {method_name}")
            try:
                prices = method_func()
                if prices and self._validate_prices(prices):
                    h200_prices.update(prices)
                    print(f"   ✅ Found {len(prices)} H200 prices!")
                    break
                else:
                    print(f"   ❌ No valid prices found")
            except Exception as e:
                print(f"   ⚠️  Error: {str(e)[:100]}")
                continue

        if not h200_prices:
            print("\n⚠️  All methods failed - no known pricing available")

        normalized_prices = self._normalize_prices(h200_prices)

        print(f"\n✅ Final extraction: {len(normalized_prices)} H200 price variants")
        return normalized_prices

    def _validate_prices(self, prices: Dict[str, str]) -> bool:
        """Validate that prices are in a reasonable range for H200 GPUs"""
        if not prices:
            return False

        for variant, price_str in prices.items():
            if 'Error' in variant:
                continue
            try:
                price_match = re.search(r'\$?([0-9.]+)', str(price_str))
                if price_match:
                    price = float(price_match.group(1))
                    if 1 < price < 20:
                        return True
            except:
                continue
        return False

    def _try_pricing_page(self) -> Dict[str, str]:
        """Scrape the Genesis Cloud pricing page for H200 prices"""
        h200_prices = {}

        try:
            print(f"    Trying: {self.base_url}")
            response = requests.get(self.base_url, headers=self.headers, timeout=20)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                text_content = soup.get_text()

                print(f"      Content length: {len(text_content)}")

                if 'H200' not in text_content:
                    print(f"      ⚠️  No H200 content found")
                    return h200_prices

                print(f"      ✓ Found H200 content")

                found_prices = self._extract_from_tables(soup)
                if found_prices:
                    h200_prices.update(found_prices)
                    return h200_prices

                found_prices = self._extract_from_text(text_content)
                if found_prices:
                    h200_prices.update(found_prices)
                    return h200_prices

            else:
                print(f"      Status {response.status_code}")

        except Exception as e:
            print(f"      Error: {str(e)[:50]}...")

        return h200_prices

    def _extract_from_tables(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract H200 prices from HTML tables"""
        prices = {}

        tables = soup.find_all('table')
        print(f"      Found {len(tables)} tables")

        for table in tables:
            table_text = table.get_text()

            if 'H200' not in table_text:
                continue

            print(f"      📋 Processing table with H200 data")

            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                row_text = ' '.join([cell.get_text().strip() for cell in cells])

                if 'H200' in row_text and ('$' in row_text or 'USD' in row_text):
                    print(f"         Row: {row_text[:150]}")

                    price_matches = re.findall(r'\$([0-9.]+)', row_text)

                    for price_str in price_matches:
                        try:
                            price = float(price_str)
                            if 1.0 < price < 20.0:
                                variant_name = f"H200 (Genesis Cloud)"
                                if variant_name not in prices:
                                    prices[variant_name] = f"${price:.2f}/hr"
                                    print(f"        Table ✓ {variant_name} = ${price:.2f}/hr")
                        except ValueError:
                            continue

        return prices

    def _extract_from_text(self, text_content: str) -> Dict[str, str]:
        """Extract H200 prices from text content using regex patterns"""
        prices = {}

        patterns = [
            r'H200[^\$]*\$([0-9.]+)\s*(?:/hr|per hour|/hour)',
            r'H200[^\$]*\$([0-9.]+)',
            r'\$([0-9.]+)\s*(?:/hr|per hour)[^H]*H200',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)

            for price_str in matches:
                try:
                    price = float(price_str)
                    if 1.0 < price < 20.0:
                        variant_name = "H200 (Genesis Cloud)"
                        prices[variant_name] = f"${price:.2f}/hr"
                        print(f"        Pattern ✓ {variant_name} = ${price:.2f}/hr")
                        return prices
                except ValueError:
                    continue

        return prices

    def _try_selenium_scraper(self) -> Dict[str, str]:
        """Use Selenium to scrape JavaScript-loaded pricing"""
        h200_prices = {}

        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options

            print("    Setting up Selenium WebDriver...")

            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

            driver = webdriver.Chrome(options=chrome_options)

            try:
                print(f"    Loading Genesis Cloud pricing page...")
                driver.get(self.base_url)

                print("    Waiting for dynamic content to load...")
                time.sleep(5)

                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                text_content = soup.get_text()

                print(f"    ✓ Page loaded, content length: {len(text_content)}")

                if 'H200' in text_content:
                    print(f"      ✓ Found H200 content")

                    found_prices = self._extract_from_tables(soup)
                    if found_prices:
                        h200_prices.update(found_prices)
                    else:
                        found_prices = self._extract_from_text(text_content)
                        if found_prices:
                            h200_prices.update(found_prices)

            finally:
                driver.quit()
                print("    WebDriver closed")

        except ImportError:
            print("      ⚠️  Selenium not installed. Run: pip install selenium")
        except Exception as e:
            print(f"      ⚠️  Error: {str(e)[:100]}")

        return h200_prices

    def _normalize_prices(self, prices: Dict[str, str]) -> Dict[str, str]:
        """Normalize prices"""
        if not prices:
            return {}

        print("\n   📊 Normalizing Genesis Cloud H200 pricing...")

        for variant, price_str in prices.items():
            if 'Error' in variant:
                continue

            try:
                price_match = re.search(r'\$([0-9.]+)', price_str)
                if price_match:
                    price = float(price_match.group(1))
                    print(f"      {variant}: ${price:.2f}/hr")
            except (ValueError, TypeError) as e:
                print(f"      ⚠️ Error normalizing {variant}: {e}")
                continue

        return prices

    def save_to_json(self, prices: Dict[str, str], filename: str = "genesiscloud_h200_prices.json") -> bool:
        """Save results to a JSON file"""
        try:
            price_value = 0.0
            if prices:
                for variant, price_str in prices.items():
                    price_match = re.search(r'\$([0-9.]+)', price_str)
                    if price_match:
                        price_value = float(price_match.group(1))
                        break

            output_data = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "provider": self.name,
                "providers": {
                    "GenesisCloud": {
                        "name": "Genesis Cloud",
                        "url": self.base_url,
                        "variants": {
                            "H200 (Genesis Cloud)": {
                                "gpu_model": "H200",
                                "gpu_memory": "141GB",
                                "price_per_hour": price_value,
                                "currency": "USD",
                                "availability": "on-demand"
                            }
                        }
                    }
                },
                "notes": {
                    "gpu_model": "NVIDIA H200",
                    "gpu_memory": "141GB HBM3e",
                    "pricing_type": "On-Demand",
                    "source": self.base_url
                }
            }

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            print(f"💾 Results saved to: {filename}")
            return True

        except Exception as e:
            print(f"❌ Error saving to file: {str(e)}")
            return False


def main():
    """Main function to run the Genesis Cloud H200 scraper"""
    print("🚀 Genesis Cloud H200 GPU Pricing Scraper")
    print("=" * 80)

    scraper = GenesisCloudH200Scraper()

    start_time = time.time()
    prices = scraper.get_h200_prices()
    end_time = time.time()

    print(f"\n⏱️  Scraping completed in {end_time - start_time:.2f} seconds")

    if prices and 'Error' not in str(prices):
        print(f"\n✅ Successfully extracted {len(prices)} H200 price entries:\n")

        for variant, price in sorted(prices.items()):
            print(f"  • {variant:50s} {price}")

        scraper.save_to_json(prices)
    else:
        print("\n❌ No valid pricing data found")


if __name__ == "__main__":
    main()
