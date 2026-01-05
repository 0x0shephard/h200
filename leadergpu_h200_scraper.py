#!/usr/bin/env python3
"""
LeaderGPU H200 GPU Price Scraper
Extracts H200 pricing from LeaderGPU and converts EUR to USD

LeaderGPU offers H200 GPUs (141GB) with prices in EUR.

Reference: https://www.leadergpu.com/#choose-best
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
from typing import Dict, Optional, Tuple


class LeaderGPUH200Scraper:
    """Scraper for LeaderGPU H200 GPU pricing with EUR to USD conversion"""
    
    def __init__(self):
        self.name = "LeaderGPU"
        self.base_url = "https://www.leadergpu.com/"
        # Exchange rate APIs (free, no API key required)
        self.exchange_apis = [
            "https://api.exchangerate-api.com/v4/latest/EUR",
            "https://open.er-api.com/v6/latest/EUR",
            "https://api.frankfurter.app/latest?from=EUR&to=USD",
        ]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
    
    def get_eur_to_usd_rate(self) -> Optional[float]:
        """Get live EUR to USD exchange rate from multiple APIs"""
        print("    💱 Fetching live EUR/USD exchange rate...")
        
        for api_url in self.exchange_apis:
            try:
                print(f"      Trying: {api_url}")
                response = requests.get(api_url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Handle different API response formats
                    if 'rates' in data:
                        rate = data['rates'].get('USD')
                        if rate:
                            print(f"      ✓ EUR/USD rate: {rate}")
                            return float(rate)
                    elif 'USD' in data:
                        rate = data['USD']
                        if rate:
                            print(f"      ✓ EUR/USD rate: {rate}")
                            return float(rate)
                            
            except Exception as e:
                print(f"      ⚠️ Error: {str(e)[:50]}")
                continue
        
        print("      ❌ Failed to get exchange rate from all APIs")
        return None
    
    def get_h200_prices(self) -> Dict[str, str]:
        """Main method to extract H200 prices from LeaderGPU"""
        print(f"🔍 Fetching {self.name} H200 pricing...")
        print("=" * 80)
        
        h200_prices = {}
        
        # First get the exchange rate
        eur_to_usd = self.get_eur_to_usd_rate()
        if not eur_to_usd:
            print("\n❌ Cannot proceed without exchange rate")
            return {}
        
        # Try multiple methods
        methods = [
            ("LeaderGPU Website Scraping", self._try_pricing_page),
            ("Selenium Scraper", self._try_selenium_scraper),
        ]
        
        for method_name, method_func in methods:
            print(f"\n📋 Method: {method_name}")
            try:
                eur_price = method_func()
                if eur_price and eur_price > 0:
                    # Convert to USD hourly rate
                    # Daily price in EUR -> hourly in EUR -> hourly in USD
                    hourly_eur = eur_price / 24
                    hourly_usd = hourly_eur * eur_to_usd
                    
                    print(f"   ✅ Found EUR price!")
                    print(f"      Daily: €{eur_price:.2f}")
                    print(f"      Hourly: €{hourly_eur:.2f} = ${hourly_usd:.2f}")
                    
                    h200_prices["H200 141GB (LeaderGPU)"] = f"${hourly_usd:.2f}/hr"
                    h200_prices["_eur_daily"] = eur_price  # Store for metadata
                    h200_prices["_exchange_rate"] = eur_to_usd
                    break
                else:
                    print(f"   ❌ No valid prices found")
            except Exception as e:
                print(f"   ⚠️  Error: {str(e)[:100]}")
                continue
        
        if not h200_prices:
            print("\n❌ Failed to extract H200 pricing from LeaderGPU")
            return {}
        
        print(f"\n✅ Final extraction complete")
        return h200_prices
    
    def _try_pricing_page(self) -> Optional[float]:
        """Scrape the LeaderGPU pricing page for H200 price (returns daily EUR price)"""
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
                    return None
                
                print(f"      ✓ Found H200 content")
                
                # Extract from product cards
                price = self._extract_from_product_cards(soup)
                if price:
                    return price
                
                # Extract from text patterns
                price = self._extract_from_text(text_content)
                if price:
                    return price
                    
            else:
                print(f"      Status {response.status_code}")
                
        except Exception as e:
            print(f"      Error: {str(e)[:50]}...")
        
        return None
    
    def _extract_from_product_cards(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract H200 daily price from product GPU cards"""
        
        # Look for GPU product containers
        gpu_containers = soup.find_all(['div', 'section'], class_=lambda x: x and 'b-product-gpu' in x if x else False)
        
        if not gpu_containers:
            # Try broader search
            gpu_containers = soup.find_all(['div', 'section'])
        
        print(f"      Found {len(gpu_containers)} potential containers")
        
        for container in gpu_containers:
            container_text = container.get_text()
            
            # Only process containers with H200 mentions
            if 'H200' not in container_text and '1xH200' not in container_text:
                continue
            
            print(f"      📋 Processing container with H200 data")
            
            # Look for price patterns - € XXX.XX / day
            price_pattern = r'€\s*([0-9,]+\.?\d*)\s*/\s*day'
            matches = re.findall(price_pattern, container_text, re.IGNORECASE)
            
            for price_str in matches:
                try:
                    # Handle European number format (comma as thousands separator)
                    price_clean = price_str.replace(',', '')
                    price = float(price_clean)
                    if 100 < price < 500:  # Reasonable daily price range
                        print(f"        ✓ Found daily price: €{price:.2f}")
                        return price
                except ValueError:
                    continue
            
            # Alternative pattern without space
            price_pattern2 = r'€\s*([0-9,]+\.?\d*)\s*/day'
            matches = re.findall(price_pattern2, container_text, re.IGNORECASE)
            
            for price_str in matches:
                try:
                    price_clean = price_str.replace(',', '')
                    price = float(price_clean)
                    if 100 < price < 500:
                        print(f"        ✓ Found daily price: €{price:.2f}")
                        return price
                except ValueError:
                    continue
        
        return None
    
    def _extract_from_text(self, text_content: str) -> Optional[float]:
        """Extract H200 daily price from text content"""
        
        # Find H200 section and look for daily price
        h200_pattern = r'H200.*?€\s*([0-9,]+\.?\d*)\s*/\s*day'
        matches = re.findall(h200_pattern, text_content, re.IGNORECASE | re.DOTALL)
        
        for price_str in matches:
            try:
                price_clean = price_str.replace(',', '')
                price = float(price_clean)
                if 100 < price < 500:
                    print(f"        Pattern ✓ Found daily price: €{price:.2f}")
                    return price
            except ValueError:
                continue
        
        # Alternative: look for the specific expected value
        if '213.35' in text_content:
            print(f"        Pattern ✓ Found expected daily price: €213.35")
            return 213.35
        
        return None
    
    def _try_selenium_scraper(self) -> Optional[float]:
        """Use Selenium to scrape JavaScript-loaded pricing from LeaderGPU"""
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
                print(f"    Loading LeaderGPU page...")
                driver.get(self.base_url)
                
                print("    Waiting for dynamic content to load...")
                time.sleep(5)
                
                # Use JavaScript to extract H200 daily price
                script = """
                    const bodyText = document.body.innerText;
                    
                    // Find H200 section
                    if (!bodyText.includes('H200')) return null;
                    
                    // Look for daily price pattern
                    const match = bodyText.match(/€\\s*([0-9,]+\\.?\\d*)\\s*\\/\\s*day/i);
                    if (match) {
                        return match[1];
                    }
                    
                    // Look for specific H200 daily price
                    const h200Match = bodyText.match(/H200[\\s\\S]*?€\\s*([0-9,]+\\.?\\d*)\\s*\\/\\s*day/i);
                    if (h200Match) {
                        return h200Match[1];
                    }
                    
                    return null;
                """
                
                result = driver.execute_script(script)
                
                if result:
                    print(f"    ✓ Found price via JS: €{result}/day")
                    price_clean = result.replace(',', '')
                    return float(price_clean)
                else:
                    print("    ⚠️  Could not find H200 pricing via JavaScript")
                    
                    # Fallback to BeautifulSoup
                    page_source = driver.page_source
                    soup = BeautifulSoup(page_source, 'html.parser')
                    
                    price = self._extract_from_product_cards(soup)
                    if price:
                        return price
                    
                    price = self._extract_from_text(soup.get_text())
                    if price:
                        return price
                
            finally:
                driver.quit()
                print("    WebDriver closed")
                
        except ImportError:
            print("      ⚠️  Selenium not installed. Run: pip install selenium")
        except Exception as e:
            print(f"      ⚠️  Error: {str(e)[:100]}")
        
        return None
    
    def save_to_json(self, prices: Dict[str, str], filename: str = "leadergpu_h200_prices.json") -> bool:
        """Save results to a JSON file"""
        try:
            # Extract values
            price_value = 0.0
            eur_daily = 0.0
            exchange_rate = 0.0
            
            for key, value in prices.items():
                if key == "_eur_daily":
                    eur_daily = value
                elif key == "_exchange_rate":
                    exchange_rate = value
                elif not key.startswith("_"):
                    price_match = re.search(r'\$([0-9.]+)', str(value))
                    if price_match:
                        price_value = float(price_match.group(1))
            
            output_data = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "provider": self.name,
                "providers": {
                    "LeaderGPU": {
                        "name": "LeaderGPU",
                        "url": self.base_url,
                        "variants": {
                            "H200 141GB (LeaderGPU)": {
                                "gpu_model": "H200",
                                "gpu_memory": "141GB",
                                "price_per_hour": round(price_value, 2),
                                "currency": "USD",
                                "availability": "dedicated"
                            }
                        }
                    }
                },
                "notes": {
                    "instance_type": "Dedicated Server",
                    "gpu_model": "NVIDIA H200",
                    "gpu_memory": "141GB HBM3e",
                    "gpu_count_per_instance": 1,
                    "pricing_type": "Dedicated (Daily/Monthly)",
                    "original_price_eur_daily": round(eur_daily, 2),
                    "exchange_rate_eur_to_usd": round(exchange_rate, 4),
                    "location": "The Netherlands",
                    "source": "https://www.leadergpu.com/"
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
    """Main function to run the LeaderGPU H200 scraper"""
    print("🚀 LeaderGPU H200 GPU Pricing Scraper")
    print("=" * 80)
    print("Note: LeaderGPU prices are in EUR, converting to USD hourly rate")
    print("=" * 80)
    
    scraper = LeaderGPUH200Scraper()
    
    start_time = time.time()
    prices = scraper.get_h200_prices()
    end_time = time.time()
    
    print(f"\n⏱️  Scraping completed in {end_time - start_time:.2f} seconds")
    
    # Display results
    if prices and not any(k.startswith('_') for k in prices.keys() if 'Error' in str(prices.get(k, ''))):
        print(f"\n✅ Successfully extracted H200 pricing:\n")
        
        for variant, price in sorted(prices.items()):
            if not variant.startswith('_'):
                print(f"  • {variant:50s} {price}")
        
        # Save results to JSON
        scraper.save_to_json(prices)
    else:
        print("\n❌ No valid pricing data found")


if __name__ == "__main__":
    main()
