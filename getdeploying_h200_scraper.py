#!/usr/bin/env python3
"""
GetDeploying H200 GPU Price Aggregator
Scrapes getdeploying.com for comprehensive H200 pricing across all providers.
Extracts prices along with provider names and saves to JSON.

Reference: https://getdeploying.com/gpus/nvidia-h200
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
from typing import Dict, List, Tuple


class GetDeployingH200Scraper:
    """H200 price aggregator from getdeploying.com"""

    def __init__(self):
        self.name = "GetDeploying"
        self.base_url = "https://getdeploying.com/gpus/nvidia-h200"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        # Known H200 providers on GetDeploying
        self.known_providers = [
            'AWS', 'Amazon', 'Azure', 'Microsoft', 'Google Cloud', 'GCP',
            'Oracle', 'CoreWeave', 'Lambda Labs', 'Lambda',
            'Nebius', 'Crusoe', 'Vultr', 'RunPod', 'Vast.ai', 'Vast',
            'FluidStack', 'Hyperstack', 'Civo', 'Shadeform',
            'Spheron', 'Akash', 'Prime Intellect', 'PrimeIntellect',
            'Valdi', 'Verda', 'Fal.ai', 'GMI Cloud', 'GMI',
            'JarvisLabs', 'Hyperbolic', 'IonStream',
            'AIME', 'AceCloud', 'Ace Cloud', 'LeaderGPU', 'Leader GPU',
            'ComputeThisHub', 'Compute This Hub',
            'Siam.ai', 'Sesterce', 'Ori',
            'HydraHost', 'Hydra Host', 'IREN', 'Iren',
        ]

    def get_h200_prices(self) -> Dict[str, any]:
        """Main method to extract all H200 prices and organize by provider"""
        print(f"🔍 Fetching {self.name} H200 pricing...")
        print("=" * 60)

        all_prices = {}

        methods = [
            ("Selenium Scraper", self._try_selenium),
            ("Direct Requests", self._try_requests),
        ]

        for method_name, method_func in methods:
            print(f"\n📋 Method: {method_name}")
            try:
                prices, raw_data = method_func()
                if prices:
                    all_prices.update(prices)
                    print(f"   ✅ Found {len(prices)} providers with H200 prices!")
                    break
            except Exception as e:
                print(f"   ⚠️  Error: {str(e)[:100]}")

        return all_prices

    def _try_selenium(self) -> Tuple[Dict, List]:
        """Use Selenium to scrape the pricing table (JS-rendered content)"""
        prices = {}
        raw_data = []

        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options

            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

            driver = webdriver.Chrome(options=chrome_options)
            try:
                print("      Loading GetDeploying H200 page...")
                driver.get(self.base_url)
                time.sleep(8)

                # Scroll to force lazy-loading
                for _ in range(5):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)

                soup = BeautifulSoup(driver.page_source, 'html.parser')
                raw_data = self._extract_from_page(soup)
                prices = self._organize_prices(raw_data)

                if prices:
                    print(f"      ✓ Extracted prices from {len(prices)} providers")
                    for provider, price_info in list(prices.items())[:10]:
                        print(f"        - {provider}: ${price_info.get('price_per_gpu', 'N/A')}/hr")

            finally:
                driver.quit()

        except ImportError:
            print("      Selenium not installed - pip install selenium")
        except Exception as e:
            print(f"      Selenium error: {str(e)[:100]}")

        return prices, raw_data

    def _try_requests(self) -> Tuple[Dict, List]:
        """Fallback: try direct requests (works if page isn't JS-gated)"""
        prices = {}
        raw_data = []

        try:
            print("      Fetching page with requests...")
            response = requests.get(self.base_url, headers=self.headers, timeout=20)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                raw_data = self._extract_from_page(soup)
                prices = self._organize_prices(raw_data)
                print(f"      ✓ Page fetched, content length: {len(response.content)}")
        except Exception as e:
            print(f"      Requests error: {str(e)[:50]}")

        return prices, raw_data

    def _extract_from_page(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract all H200 pricing entries from the page"""
        entries = []

        # Method 1: Table rows
        tables = soup.find_all('table')
        print(f"      Found {len(tables)} tables")

        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    entry = self._parse_table_row(cells)
                    if entry and entry.get('provider') and entry.get('price'):
                        entries.append(entry)

        # Method 2: Card/div layouts
        cards = soup.find_all(['div', 'article'], class_=re.compile(r'card|price|row|item', re.I))
        for card in cards:
            card_text = card.get_text(separator=' ')
            entry = self._parse_card_text(card_text)
            if entry and entry.get('provider') and entry.get('price'):
                if not any(e.get('provider') == entry.get('provider') and
                           e.get('price') == entry.get('price') for e in entries):
                    entries.append(entry)

        # Method 3: General text extraction
        text = soup.get_text(separator=' ')
        text_entries = self._extract_from_text(text)
        for entry in text_entries:
            if not any(e.get('provider') == entry.get('provider') for e in entries):
                entries.append(entry)

        print(f"      Extracted {len(entries)} raw price entries")
        return entries

    def _parse_table_row(self, cells: list) -> Dict:
        """Parse a table row to extract provider, gpu count, price info"""
        entry = {}

        row_text = ' '.join([cell.get_text().strip() for cell in cells])

        # Find provider
        for provider in self.known_providers:
            if provider.lower() in row_text.lower():
                entry['provider'] = self._normalize_provider(provider)
                break

        if not entry.get('provider'):
            # Try links inside cells
            for cell in cells:
                for link in cell.find_all('a'):
                    link_text = link.get_text().strip()
                    for provider in self.known_providers:
                        if provider.lower() in link_text.lower():
                            entry['provider'] = self._normalize_provider(provider)
                            break

        if not entry.get('provider'):
            return None

        # Extract price
        for pattern in [
            r'\$([0-9]+\.?[0-9]*)\s*/?(?:hr|hour|GPU)',
            r'\$([0-9]+\.?[0-9]*)',
        ]:
            m = re.search(pattern, row_text, re.IGNORECASE)
            if m:
                try:
                    price = float(m.group(1))
                    # H200 prices typically $1–30/hr per GPU
                    if 1.0 < price < 150.0:
                        entry['price'] = price
                        break
                except ValueError:
                    continue

        # GPU count
        gpu_m = re.search(r'(\d+)\s*x?\s*(?:GPU|H200)', row_text, re.IGNORECASE)
        entry['gpu_count'] = int(gpu_m.group(1)) if gpu_m else 1

        # Billing type
        rt_lower = row_text.lower()
        if 'spot' in rt_lower:
            entry['billing'] = 'spot'
        elif 'reserved' in rt_lower or 'commit' in rt_lower:
            entry['billing'] = 'reserved'
        else:
            entry['billing'] = 'on_demand'

        return entry if 'price' in entry else None

    def _parse_card_text(self, text: str) -> Dict:
        """Parse card/div text for pricing info"""
        entry = {}

        for provider in self.known_providers:
            if provider.lower() in text.lower():
                entry['provider'] = self._normalize_provider(provider)
                break

        if not entry.get('provider'):
            return None

        m = re.search(r'\$([0-9]+\.?[0-9]*)', text)
        if m:
            try:
                price = float(m.group(1))
                if 1.0 < price < 150.0:
                    entry['price'] = price
            except ValueError:
                pass

        gpu_m = re.search(r'(\d+)\s*x?\s*(?:GPU|H200)', text, re.IGNORECASE)
        entry['gpu_count'] = int(gpu_m.group(1)) if gpu_m else 1
        entry['billing'] = 'spot' if 'spot' in text.lower() else 'on_demand'

        return entry if 'price' in entry else None

    def _extract_from_text(self, text: str) -> List[Dict]:
        """Extract pricing from general page text"""
        entries = []

        for provider in self.known_providers:
            pattern = rf'{re.escape(provider)}[^\$]{{0,100}}\$([0-9]+\.?[0-9]*)'
            for match in re.findall(pattern, text, re.IGNORECASE):
                try:
                    price = float(match)
                    if 1.0 < price < 150.0:
                        entries.append({
                            'provider': self._normalize_provider(provider),
                            'price': price,
                            'gpu_count': 1,
                            'billing': 'on_demand',
                        })
                except ValueError:
                    continue

        return entries

    def _normalize_provider(self, provider: str) -> str:
        """Normalize provider names to canonical forms used by H200 scrapers"""
        provider_map = {
            'aws': 'AWS',
            'amazon': 'AWS',
            'azure': 'Azure',
            'microsoft': 'Azure',
            'google cloud': 'Google Cloud',
            'gcp': 'Google Cloud',
            'oracle': 'Oracle',
            'coreweave': 'CoreWeave',
            'lambda labs': 'Lambda Labs',
            'lambda': 'Lambda Labs',
            'nebius': 'Nebius',
            'crusoe': 'Crusoe',
            'vultr': 'Vultr',
            'runpod': 'RunPod',
            'vast.ai': 'Vast.ai',
            'vast': 'Vast.ai',
            'fluidstack': 'FluidStack',
            'hyperstack': 'Hyperstack',
            'civo': 'Civo',
            'shadeform': 'Shadeform',
            'spheron': 'Spheron',
            'akash': 'Akash',
            'prime intellect': 'Prime Intellect',
            'primeintellect': 'Prime Intellect',
            'valdi': 'Valdi',
            'verda': 'Verda',
            'fal.ai': 'Fal.ai',
            'gmi cloud': 'GMI Cloud',
            'gmi': 'GMI Cloud',
            'jarvislabs': 'JarvisLabs',
            'hyperbolic': 'Hyperbolic',
            'ionstream': 'IonStream',
            'aime': 'AIME',
            'acecloud': 'AceCloud',
            'ace cloud': 'AceCloud',
            'leadergpu': 'LeaderGPU',
            'leader gpu': 'LeaderGPU',
            'computethishub': 'ComputeThisHub',
            'compute this hub': 'ComputeThisHub',
            'siam.ai': 'Siam.ai',
            'sesterce': 'Sesterce',
            'ori': 'Ori',
            'hydrahost': 'HydraHost',
            'hydra host': 'HydraHost',
            'iren': 'IREN',
        }
        return provider_map.get(provider.lower(), provider)

    def _organize_prices(self, raw_data: List[Dict]) -> Dict[str, Dict]:
        """Organize prices by provider, averaging per-GPU prices across all listings"""
        provider_prices: Dict[str, List[float]] = {}

        for entry in raw_data:
            provider = entry.get('provider')
            if not provider:
                continue

            price = entry.get('price', 0)
            gpu_count = entry.get('gpu_count', 1)
            per_gpu = price / gpu_count if gpu_count > 0 else price

            provider_prices.setdefault(provider, []).append(per_gpu)

        organized = {}
        for provider, prices in provider_prices.items():
            if prices:
                avg_price = sum(prices) / len(prices)
                organized[provider] = {
                    'price_per_gpu': round(avg_price, 2),
                    'price_count': len(prices),
                    'min_price': round(min(prices), 2),
                    'max_price': round(max(prices), 2),
                }

        return organized

    def save_to_json(self, prices: Dict, filename: str = "getdeploying_h200_prices.json"):
        """Save prices to JSON file"""
        output = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source": self.name,
            "source_url": self.base_url,
            "gpu_model": "H200",
            "fetch_status": "success" if prices else "failed",
            "provider_count": len(prices),
            "prices": prices,
            "notes": {
                "pricing_unit": "USD per GPU per hour",
                "data_source": self.base_url,
            }
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"💾 Results saved to: {filename}")
        return True


def main():
    print("🚀 GetDeploying H200 GPU Price Aggregator")
    print("=" * 60)

    scraper = GetDeployingH200Scraper()
    prices = scraper.get_h200_prices()

    if prices:
        print(f"\n📊 H200 Prices from {len(prices)} providers:")
        print("-" * 40)
        for provider, info in sorted(prices.items(), key=lambda x: x[1].get('price_per_gpu', 999)):
            price = info.get('price_per_gpu', 'N/A')
            print(f"   {provider:25s}: ${price}/hr")
    else:
        print("\n❌ No H200 prices found")

    scraper.save_to_json(prices)


if __name__ == "__main__":
    main()
