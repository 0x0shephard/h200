#!/usr/bin/env python3
"""
Spheron Network H200 GPU Price Scraper
Extracts H200 pricing from Spheron Network

Spheron offers H200 GPUs with decentralized compute.

Reference: https://www.spheron.network/
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
from typing import Dict, Optional


class SpheronH200Scraper:
    """Scraper for Spheron Network H200 GPU pricing"""
    
    def __init__(self):
        self.name = "Spheron"
        self.base_url = "https://www.spheron.network/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
    
    def get_h200_prices(self) -> Dict[str, str]:
        """Main method to extract H200 prices from Spheron"""
        print(f"🔍 Fetching {self.name} H200 pricing...")
        print("=" * 80)
        
        h200_prices = {}
        
        # Try multiple methods
        methods = [
            ("Spheron Website Scraping", self._try_pricing_page),
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
            print("\n❌ Failed to extract H200 pricing from Spheron")
            return {}
        
        print(f"\n✅ Final extraction complete")
        return h200_prices
    
    def _validate_prices(self, prices: Dict[str, str]) -> bool:
        """Validate that prices are in a reasonable range"""
        if not prices:
            return False
        
        for variant, price_str in prices.items():
            if 'Error' in variant:
                continue
            try:
                price_match = re.search(r'\$?([0-9.]+)', str(price_str))
                if price_match:
                    price = float(price_match.group(1))
                    # Spheron H200 pricing is around $1-3/hr
                    if 0.5 < price < 5.0:
                        return True
            except:
                continue
        return False
    
    def _try_pricing_page(self) -> Dict[str, str]:
        """Scrape the Spheron website for H200 pricing"""
        h200_prices = {}
        
        try:
            print(f"    Trying: {self.base_url}")
            response = requests.get(self.base_url, headers=self.headers, timeout=20)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                text_content = soup.get_text()
                
                print(f"      Content length: {len(text_content)}")
                
                # Check if page contains H200 data
                if 'H200' not in text_content:
                    print(f"      ⚠️  No H200 content found")
                    return h200_prices
                
                print(f"      ✓ Found H200 content")
                
                # Extract prices
                prices = self._extract_prices(soup, text_content)
                if prices:
                    h200_prices.update(prices)
                    
            else:
                print(f"      Status {response.status_code}")
                
        except Exception as e:
            print(f"      Error: {str(e)[:50]}...")
        
        return h200_prices
    
    def _extract_prices(self, soup: BeautifulSoup, text_content: str) -> Dict[str, str]:
        """Extract H200 prices from page content"""
        prices = {}
        
        # Look for H200 section and its price
        # The format is: H200 followed by specs and then $X.XX/hr
        
        # Pattern 1: Find H200 block with price
        h200_pattern = r'H200[^$]*\$([0-9.]+)/hr'
        matches = re.findall(h200_pattern, text_content, re.IGNORECASE | re.DOTALL)
        
        for price_str in matches:
            try:
                price = float(price_str)
                if 0.5 < price < 5.0:
                    print(f"        ✓ Found H200 price: ${price:.2f}/hr")
                    prices["H200 141GB (Spheron)"] = f"${price:.2f}/hr"
                    return prices
            except ValueError:
                continue
        
        # Pattern 2: Look for h3 tags with H200 and nearby price
        h3_tags = soup.find_all('h3')
        for h3 in h3_tags:
            if 'H200' in h3.get_text():
                # Look in parent container for price
                parent = h3.parent
                for _ in range(5):  # Walk up a few levels
                    if parent:
                        parent_text = parent.get_text()
                        price_match = re.search(r'\$([0-9.]+)/hr', parent_text)
                        if price_match:
                            price = float(price_match.group(1))
                            if 0.5 < price < 5.0:
                                print(f"        ✓ Found H200 price in parent: ${price:.2f}/hr")
                                prices["H200 141GB (Spheron)"] = f"${price:.2f}/hr"
                                return prices
                        parent = parent.parent
        
        # Pattern 3: Direct text search for specific expected value
        if '$1.56/hr' in text_content or '$1.56 /hr' in text_content:
            print(f"        ✓ Found expected H200 price: $1.56/hr")
            prices["H200 141GB (Spheron)"] = "$1.56/hr"
            return prices
        
        return prices
    
    def _try_selenium_scraper(self) -> Dict[str, str]:
        """Use Selenium to scrape JavaScript-loaded pricing from Spheron"""
        h200_prices = {}
        
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            
            print("    Setting up Selenium WebDriver...")
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            driver = webdriver.Chrome(options=chrome_options)
            
            try:
                print(f"    Loading Spheron page...")
                driver.get(self.base_url)
                
                print("    Waiting for dynamic content to load...")
                time.sleep(5)
                
                # Use JavaScript to extract H200 pricing
                script = """
                    // Find H200 heading
                    const h3s = Array.from(document.querySelectorAll('h3'));
                    const h200h3 = h3s.find(h => h.textContent.trim() === 'H200');
                    
                    if (!h200h3) return null;
                    
                    // Walk up to find the row container
                    let row = h200h3.parentElement;
                    for (let i = 0; i < 5; i++) {
                        if (!row) break;
                        const text = row.innerText;
                        const priceMatch = text.match(/\\$([0-9.]+)\\/hr/);
                        if (priceMatch) {
                            return {
                                gpu: 'H200',
                                price: priceMatch[1],
                                fullText: text.substring(0, 200)
                            };
                        }
                        row = row.parentElement;
                    }
                    
                    // Fallback: search entire page
                    const bodyText = document.body.innerText;
                    const h200Section = bodyText.match(/H200[^$]*\\$([0-9.]+)\\/hr/i);
                    if (h200Section) {
                        return {
                            gpu: 'H200',
                            price: h200Section[1],
                            fullText: 'Found via text search'
                        };
                    }
                    
                    return null;
                """
                
                result = driver.execute_script(script)
                
                if result and result.get('price'):
                    price = float(result['price'])
                    if 0.5 < price < 5.0:
                        h200_prices["H200 141GB (Spheron)"] = f"${price:.2f}/hr"
                        print(f"    ✓ Found: ${price:.2f}/hr")
                else:
                    print("    ⚠️  Could not find H200 pricing via JavaScript")
                    
                    # Fallback to BeautifulSoup
                    page_source = driver.page_source
                    soup = BeautifulSoup(page_source, 'html.parser')
                    prices = self._extract_prices(soup, soup.get_text())
                    if prices:
                        h200_prices.update(prices)
                
            finally:
                driver.quit()
                print("    WebDriver closed")
                
        except ImportError:
            print("      ⚠️  Selenium not installed. Run: pip install selenium")
        except Exception as e:
            print(f"      ⚠️  Error: {str(e)[:100]}")
        
        return h200_prices
    
    def save_to_json(self, prices: Dict[str, str], filename: str = "spheron_h200_prices.json") -> bool:
        """Save results to a JSON file"""
        try:
            # Extract price
            price_value = 0.0
            for variant, price_str in prices.items():
                price_match = re.search(r'\$([0-9.]+)', price_str)
                if price_match:
                    price_value = float(price_match.group(1))
                    break
            
            output_data = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "provider": self.name,
                "providers": {
                    "Spheron": {
                        "name": "Spheron Network",
                        "url": self.base_url,
                        "variants": {
                            "H200 141GB (Spheron)": {
                                "gpu_model": "H200",
                                "gpu_memory": "141GB",
                                "price_per_hour": round(price_value, 2),
                                "currency": "USD",
                                "availability": "on-demand"
                            }
                        }
                    }
                },
                "notes": {
                    "instance_type": "Decentralized Compute",
                    "gpu_model": "NVIDIA H200",
                    "gpu_memory": "141GB",
                    "ram": "200GB",
                    "vcpus": 16,
                    "storage": "465GB",
                    "gpu_count_per_instance": 1,
                    "pricing_type": "On-Demand",
                    "source": "https://www.spheron.network/"
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
    """Main function to run the Spheron H200 scraper"""
    print("🚀 Spheron Network H200 GPU Pricing Scraper")
    print("=" * 80)
    print("Note: Spheron offers decentralized H200 GPU compute")
    print("=" * 80)
    
    scraper = SpheronH200Scraper()
    
    start_time = time.time()
    prices = scraper.get_h200_prices()
    end_time = time.time()
    
    print(f"\n⏱️  Scraping completed in {end_time - start_time:.2f} seconds")
    
    # Display results
    if prices:
        print(f"\n✅ Successfully extracted H200 pricing:\n")
        
        for variant, price in sorted(prices.items()):
            print(f"  • {variant:50s} {price}")
        
        # Save results to JSON
        scraper.save_to_json(prices)
    else:
        print("\n❌ No valid pricing data found")


if __name__ == "__main__":
    main()
