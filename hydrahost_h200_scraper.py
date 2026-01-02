#!/usr/bin/env python3
"""
HydraHost H200 GPU Price Scraper
Extracts H200 pricing from HydraHost

Reference: https://hydrahost.com/
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
from typing import Dict


class HydraHostH200Scraper:
    def __init__(self):
        self.name = "HydraHost"
        self.base_url = "https://hydrahost.com/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }

    def get_h200_prices(self) -> Dict[str, str]:
        print(f"🔍 Fetching {self.name} H200 pricing...")
        print("=" * 80)
        h200_prices = {}
        
        for method_name, method_func in [
            ("HydraHost Page Scraping", self._try_scraping),
            ("Selenium Scraper", self._try_selenium),
        ]:
            print(f"\n📋 Method: {method_name}")
            try:
                prices = method_func()
                if prices and any(0.5 < float(re.search(r'([0-9.]+)', p).group(1)) < 20 for p in prices.values() if re.search(r'([0-9.]+)', p)):
                    h200_prices.update(prices)
                    print(f"   ✅ Found {len(prices)} H200 prices!")
                    break
                print(f"   ❌ No valid prices found")
            except Exception as e:
                print(f"   ⚠️  Error: {str(e)[:100]}")
        
        if not h200_prices:
            print("\n⚠️  All methods failed")
        
        print(f"\n✅ Final extraction: {len(h200_prices)} H200 price variants")
        if h200_prices:
            self.save_to_json(h200_prices)
        return h200_prices

    def _try_scraping(self) -> Dict[str, str]:
        print(f"    Trying: {self.base_url}")
        response = requests.get(self.base_url, headers=self.headers, timeout=20)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text()
            print(f"      Content length: {len(text)}")
            if 'H200' in text:
                print("      ✓ Found H200 content")
                for pattern in [r'H200[^\$]*\$([0-9.]+)', r'\$([0-9.]+)[^H]*H200']:
                    for price_str in re.findall(pattern, text, re.IGNORECASE):
                        price = float(price_str)
                        if 0.5 < price < 20:
                            return {"H200 (HydraHost)": f"${price:.2f}/hr"}
        return {}

    def _try_selenium(self) -> Dict[str, str]:
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            driver = webdriver.Chrome(options=options)
            
            driver.get(self.base_url)
            time.sleep(5)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            driver.quit()
            
            text = soup.get_text()
            if 'H200' in text:
                for price_str in re.findall(r'H200[^\$]*\$([0-9.]+)', text, re.IGNORECASE):
                    price = float(price_str)
                    if 0.5 < price < 20:
                        return {"H200 (HydraHost)": f"${price:.2f}/hr"}
        except:
            pass
        return {}

    def save_to_json(self, prices: Dict[str, str], filename: str = "hydrahost_h200_prices.json"):
        price_value = float(re.search(r'([0-9.]+)', list(prices.values())[0]).group(1)) if prices else 0.0
        output_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "provider": self.name,
            "providers": {
                "HydraHost": {
                    "name": "HydraHost",
                    "url": self.base_url,
                    "variants": {
                        "H200 (HydraHost)": {
                            "gpu_model": "H200",
                            "gpu_memory": "141GB",
                            "price_per_hour": price_value,
                            "currency": "USD",
                            "availability": "on-demand"
                        }
                    }
                }
            }
        }
        with open(filename, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"💾 Results saved to: {filename}")

if __name__ == "__main__":
    scraper = HydraHostH200Scraper()
    scraper.get_h200_prices()
