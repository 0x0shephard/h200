#!/usr/bin/env python3
import requests, re, json, time
from bs4 import BeautifulSoup
from typing import Dict

class CrusoeH200Scraper:
    def __init__(self):
        self.name, self.url = "Crusoe", "https://www.crusoe.ai/cloud/pricing"
        self.headers = {'User-Agent': 'Mozilla/5.0'}
    
    def get_h200_prices(self) -> Dict[str, str]:
        print(f"🔍 Fetching {self.name} H200 pricing...\n" + "="*80)
        prices = {}
        for method_name, func in [("Pricing Page", self._scrape), ("Selenium", self._selenium)]:
            print(f"\n📋 Method: {method_name}")
            try:
                prices = func()
                if prices: 
                    print(f"   ✅ Found {len(prices)} prices!")
                    break
                print("   ❌ No valid prices")
            except Exception as e:
                print(f"   ⚠️  Error: {str(e)[:80]}")
        if prices: self.save_to_json(prices)
        print(f"\n✅ Final: {len(prices)} price variants")
        return prices
    
    def _scrape(self) -> Dict[str, str]:
        r = requests.get(self.url, headers=self.headers, timeout=20)
        if r.status_code == 200:
            text = BeautifulSoup(r.content, 'html.parser').get_text()
            print(f"      Content: {len(text)} chars")
            if 'H200' in text:
                for p in re.findall(r'H200[^\$]*\$([0-9.]+)', text, re.I):
                    if 0.5 < float(p) < 20: return {"H200 (Crusoe)": f"${float(p):.2f}/hr"}
        return {}
    
    def _selenium(self) -> Dict[str, str]:
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            opts = Options()
            opts.add_argument('--headless'); opts.add_argument('--no-sandbox')
            driver = webdriver.Chrome(options=opts)
            driver.get(self.url); time.sleep(5)
            text = BeautifulSoup(driver.page_source, 'html.parser').get_text()
            driver.quit()
            if 'H200' in text:
                for p in re.findall(r'H200[^\$]*\$([0-9.]+)', text, re.I):
                    if 0.5 < float(p) < 20: return {"H200 (Crusoe)": f"${float(p):.2f}/hr"}
        except: pass
        return {}
    
    def save_to_json(self, prices: Dict[str, str], filename="crusoe_h200_prices.json"):
        pv = float(re.search(r'([0-9.]+)', list(prices.values())[0]).group(1)) if prices else 0.0
        with open(filename, 'w') as f:
            json.dump({"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "provider": self.name, 
                      "providers": {"Crusoe": {"name": "Crusoe", "url": self.url, 
                      "variants": {"H200 (Crusoe)": {"gpu_model": "H200", "gpu_memory": "141GB", 
                      "price_per_hour": pv, "currency": "USD", "availability": "on-demand"}}}}}, f, indent=2)
        print(f"💾 Saved: {filename}")

if __name__ == "__main__":
    CrusoeH200Scraper().get_h200_prices()
