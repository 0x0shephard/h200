#!/usr/bin/env python3
"""
Valdi H200 GPU Price Scraper
Extracts H200 pricing from Valdi GPU marketplace

Valdi lists multiple H200 GPU offerings from various providers.
This scraper gets all H200 prices and calculates the average.

Reference: https://gpulist.valdi.ai/?gpu_type=h200&page=1
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
from typing import Dict, List, Optional


class ValdiH200Scraper:
    """Scraper for Valdi H200 GPU pricing with averaging"""
    
    def __init__(self):
        self.name = "Valdi"
        self.base_url = "https://gpulist.valdi.ai/?gpu_type=h200&page=1"
        self.api_url = "https://gpulist.valdi.ai"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
    
    def get_h200_prices(self) -> Dict[str, str]:
        """Main method to extract all H200 prices from Valdi and average them"""
        print(f"🔍 Fetching {self.name} H200 pricing...")
        print("=" * 80)
        
        all_prices = []
        
        # Try multiple methods
        methods = [
            ("Valdi GPU List Scraping", self._try_pricing_page),
            ("Selenium Scraper (Multiple Pages)", self._try_selenium_scraper),
        ]
        
        for method_name, method_func in methods:
            print(f"\n📋 Method: {method_name}")
            try:
                prices = method_func()
                if prices:
                    all_prices.extend(prices)
                    print(f"   ✅ Found {len(prices)} H200 prices!")
                    break
                else:
                    print(f"   ❌ No valid prices found")
            except Exception as e:
                print(f"   ⚠️  Error: {str(e)[:100]}")
                continue
        
        if not all_prices:
            print("\n❌ Failed to extract H200 pricing from Valdi")
            return {}
        
        # Calculate average
        avg_price = sum(all_prices) / len(all_prices)
        min_price = min(all_prices)
        max_price = max(all_prices)
        
        print(f"\n   📊 Price Statistics:")
        print(f"      Min: ${min_price:.2f}/hr")
        print(f"      Max: ${max_price:.2f}/hr")
        print(f"      Average: ${avg_price:.2f}/hr")
        print(f"      Count: {len(all_prices)} listings")
        
        result = {
            "H200 (Valdi Avg)": f"${avg_price:.2f}/hr",
            "_all_prices": all_prices,
            "_min": min_price,
            "_max": max_price,
            "_count": len(all_prices)
        }
        
        print(f"\n✅ Final extraction complete")
        return result
    
    def _try_pricing_page(self) -> List[float]:
        """Scrape the Valdi GPU list page for H200 prices"""
        all_prices = []
        
        # Try multiple pages
        for page in range(1, 4):  # Check up to 3 pages
            try:
                url = f"https://gpulist.valdi.ai/?gpu_type=h200&page={page}"
                print(f"    Trying: {url}")
                response = requests.get(url, headers=self.headers, timeout=20)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    text_content = soup.get_text()
                    
                    print(f"      Content length: {len(text_content)}")
                    
                    # Check if page contains H200 data
                    if 'H200' not in text_content:
                        print(f"      ⚠️  No H200 content found on page {page}")
                        break
                    
                    # Extract prices from this page
                    page_prices = self._extract_prices(soup, text_content)
                    if page_prices:
                        all_prices.extend(page_prices)
                        print(f"      ✓ Found {len(page_prices)} prices on page {page}")
                    else:
                        print(f"      No new prices on page {page}")
                        break
                        
                else:
                    print(f"      Status {response.status_code}")
                    break
                    
            except Exception as e:
                print(f"      Error: {str(e)[:50]}...")
                break
        
        return all_prices
    
    def _extract_prices(self, soup: BeautifulSoup, text_content: str) -> List[float]:
        """Extract all H200 prices from page content"""
        prices = []
        
        # Method 1: Look for /hour price patterns in GPU listing cards
        # Pattern: $XX.XX/hour
        price_pattern = r'\$([0-9,]+\.?\d*)/hour'
        matches = re.findall(price_pattern, text_content, re.IGNORECASE)
        
        for price_str in matches:
            try:
                # Remove commas and convert to float
                price_clean = price_str.replace(',', '')
                price = float(price_clean)
                # Valid H200 prices are typically $15-35/hour for 8-GPU instances
                if 10.0 < price < 50.0:
                    if price not in prices:  # Avoid duplicates
                        prices.append(price)
                        print(f"        ✓ Found price: ${price:.2f}/hr")
            except ValueError:
                continue
        
        # Method 2: Look for links to GPU pages and extract prices
        gpu_links = soup.find_all('a', href=lambda x: x and '/gpu/' in x if x else False)
        for link in gpu_links:
            link_text = link.get_text()
            if '/hour' in link_text:
                price_match = re.search(r'\$([0-9,]+\.?\d*)/hour', link_text)
                if price_match:
                    try:
                        price_clean = price_match.group(1).replace(',', '')
                        price = float(price_clean)
                        if 10.0 < price < 50.0 and price not in prices:
                            prices.append(price)
                            print(f"        ✓ Found price from link: ${price:.2f}/hr")
                    except ValueError:
                        continue
        
        return prices
    
    def _try_selenium_scraper(self) -> List[float]:
        """Use Selenium to scrape JavaScript-loaded pricing from Valdi"""
        all_prices = []
        
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
                # Process multiple pages
                for page in range(1, 4):  # Up to 3 pages
                    url = f"https://gpulist.valdi.ai/?gpu_type=h200&page={page}"
                    print(f"    Loading page {page}...")
                    driver.get(url)
                    
                    print("    Waiting for dynamic content to load...")
                    time.sleep(5)
                    
                    # Use JavaScript to extract all H200 prices
                    script = """
                        const cards = document.querySelectorAll('a[href^="/gpu/"]');
                        const prices = [];
                        
                        cards.forEach(card => {
                            const text = card.innerText;
                            // Look for price pattern
                            const priceMatch = text.match(/\\$([\\d,]+\\.?\\d*)\\/hour/);
                            if (priceMatch) {
                                const price = parseFloat(priceMatch[1].replace(',', ''));
                                if (price > 10 && price < 50) {
                                    prices.push(price);
                                }
                            }
                        });
                        
                        return prices;
                    """
                    
                    result = driver.execute_script(script)
                    
                    if result and len(result) > 0:
                        for price in result:
                            if price not in all_prices:
                                all_prices.append(price)
                                print(f"    ✓ Page {page}: ${price:.2f}/hr")
                    else:
                        print(f"    No more prices on page {page}")
                        break
                    
                    # Check if there's a next page
                    try:
                        next_button = driver.find_element(By.CSS_SELECTOR, 'a[aria-label="Go to next page"]')
                        if not next_button.is_enabled():
                            break
                    except:
                        break
                
            finally:
                driver.quit()
                print("    WebDriver closed")
                
        except ImportError:
            print("      ⚠️  Selenium not installed. Run: pip install selenium")
        except Exception as e:
            print(f"      ⚠️  Error: {str(e)[:100]}")
        
        return all_prices
    
    def save_to_json(self, prices: Dict[str, str], filename: str = "valdi_h200_prices.json") -> bool:
        """Save results to a JSON file"""
        try:
            # Extract values
            avg_price = 0.0
            all_prices = []
            min_price = 0.0
            max_price = 0.0
            count = 0
            
            for key, value in prices.items():
                if key == "_all_prices":
                    all_prices = value
                elif key == "_min":
                    min_price = value
                elif key == "_max":
                    max_price = value
                elif key == "_count":
                    count = value
                elif not key.startswith("_"):
                    price_match = re.search(r'\$([0-9.]+)', str(value))
                    if price_match:
                        avg_price = float(price_match.group(1))
            
            output_data = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "provider": self.name,
                "providers": {
                    "Valdi": {
                        "name": "Valdi GPU Marketplace",
                        "url": self.base_url,
                        "variants": {
                            "H200 (Valdi Avg)": {
                                "gpu_model": "H200",
                                "gpu_memory": "141GB",
                                "price_per_hour": round(avg_price, 2),
                                "currency": "USD",
                                "availability": "marketplace"
                            }
                        }
                    }
                },
                "notes": {
                    "instance_type": "Various (8x H200)",
                    "gpu_model": "NVIDIA H200",
                    "gpu_memory": "141GB HBM3e",
                    "gpu_count_per_instance": 8,
                    "pricing_type": "Marketplace Aggregator",
                    "price_statistics": {
                        "average": round(avg_price, 2),
                        "minimum": round(min_price, 2),
                        "maximum": round(max_price, 2),
                        "listing_count": count,
                        "all_prices": [round(p, 2) for p in all_prices]
                    },
                    "source": "https://gpulist.valdi.ai/?gpu_type=h200"
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
    """Main function to run the Valdi H200 scraper"""
    print("🚀 Valdi H200 GPU Pricing Scraper")
    print("=" * 80)
    print("Note: Valdi aggregates multiple H200 offerings - this scraper averages them")
    print("=" * 80)
    
    scraper = ValdiH200Scraper()
    
    start_time = time.time()
    prices = scraper.get_h200_prices()
    end_time = time.time()
    
    print(f"\n⏱️  Scraping completed in {end_time - start_time:.2f} seconds")
    
    # Display results
    if prices:
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
