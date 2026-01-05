#!/usr/bin/env python3
"""
Shadeform H200 GPU Price Scraper
Extracts H200 pricing from Shadeform

Shadeform offers H200x8 Bare Metal servers on-demand.

Reference: https://www.shadeform.ai/
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
from typing import Dict, Optional


class ShadeformH200Scraper:
    """Scraper for Shadeform H200 GPU pricing"""
    
    def __init__(self):
        self.name = "Shadeform"
        self.base_url = "https://www.shadeform.ai/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
    
    def get_h200_prices(self) -> Dict[str, str]:
        """Main method to extract H200 prices from Shadeform"""
        print(f"🔍 Fetching {self.name} H200 pricing...")
        print("=" * 80)
        
        h200_prices = {}
        
        # Try multiple methods
        methods = [
            ("Shadeform Website Scraping", self._try_pricing_page),
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
            print("\n❌ Failed to extract H200 pricing from Shadeform")
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
                    # Shadeform H200 pricing is around $2-5/hr
                    if 1.0 < price < 10.0:
                        return True
            except:
                continue
        return False
    
    def _try_pricing_page(self) -> Dict[str, str]:
        """Scrape the Shadeform website for H200 pricing"""
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
        
        # Method 1: Look in nav elements for banner
        nav_elements = soup.find_all('nav')
        for nav in nav_elements:
            nav_text = nav.get_text()
            if 'H200' in nav_text and '$' in nav_text:
                # Look for price pattern
                price_match = re.search(r'\$([0-9.]+)/gpu/hour', nav_text, re.IGNORECASE)
                if price_match:
                    price = float(price_match.group(1))
                    if 1.0 < price < 10.0:
                        print(f"        ✓ Found H200 price in nav banner: ${price:.2f}/hr")
                        prices["H200x8 (Shadeform)"] = f"${price:.2f}/hr"
                        return prices
        
        # Method 2: Look for strong tags with shadeform-coral class
        strong_tags = soup.find_all('strong', class_=lambda x: x and 'coral' in x.lower() if x else False)
        price_value = None
        gpu_found = False
        
        for strong in strong_tags:
            strong_text = strong.get_text()
            if 'H200' in strong_text:
                gpu_found = True
            if '$' in strong_text:
                price_match = re.search(r'\$([0-9.]+)', strong_text)
                if price_match:
                    price_value = float(price_match.group(1))
        
        if gpu_found and price_value and 1.0 < price_value < 10.0:
            print(f"        ✓ Found H200 price from strong tags: ${price_value:.2f}/hr")
            prices["H200x8 (Shadeform)"] = f"${price_value:.2f}/hr"
            return prices
        
        # Method 3: Direct text pattern matching for H200x8
        patterns = [
            r'H200x8[^$]*\$([0-9.]+)/gpu/hour',
            r'H200[^$]*\$([0-9.]+)/gpu/hour',
            r'H200[^$]*\$([0-9.]+)/hour',
            r'H200[^$]*\$([0-9.]+)/hr',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for price_str in matches:
                try:
                    price = float(price_str)
                    if 1.0 < price < 10.0:
                        print(f"        ✓ Found H200 price via pattern: ${price:.2f}/hr")
                        prices["H200x8 (Shadeform)"] = f"${price:.2f}/hr"
                        return prices
                except ValueError:
                    continue
        
        return prices
    
    def _try_selenium_scraper(self) -> Dict[str, str]:
        """Use Selenium to scrape JavaScript-loaded pricing from Shadeform"""
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
                print(f"    Loading Shadeform page...")
                driver.get(self.base_url)
                
                print("    Waiting for dynamic content to load...")
                time.sleep(5)
                
                # Use JavaScript to extract H200 pricing from banner
                script = """
                    // Look in nav for H200 pricing banner
                    const navs = document.querySelectorAll('nav');
                    for (const nav of navs) {
                        const text = nav.textContent;
                        if (text.includes('H200') && text.includes('$')) {
                            const match = text.match(/\\$([0-9.]+)\\/gpu\\/hour/i);
                            if (match) {
                                return {
                                    price: match[1],
                                    context: text.substring(0, 150)
                                };
                            }
                        }
                    }
                    
                    // Look for strong tags with pricing
                    const strongs = document.querySelectorAll('strong');
                    let gpu = null;
                    let price = null;
                    for (const strong of strongs) {
                        const text = strong.textContent;
                        if (text.includes('H200')) {
                            gpu = text;
                        }
                        if (text.includes('$')) {
                            const match = text.match(/\\$([0-9.]+)/);
                            if (match) {
                                price = match[1];
                            }
                        }
                    }
                    if (gpu && price) {
                        return {
                            price: price,
                            context: gpu + ' at $' + price
                        };
                    }
                    
                    // Fallback: search entire page
                    const bodyText = document.body.innerText;
                    const h200Match = bodyText.match(/H200[^$]*\\$([0-9.]+)\\/gpu\\/hour/i);
                    if (h200Match) {
                        return {
                            price: h200Match[1],
                            context: 'Found via text search'
                        };
                    }
                    
                    return null;
                """
                
                result = driver.execute_script(script)
                
                if result and result.get('price'):
                    price = float(result['price'])
                    if 1.0 < price < 10.0:
                        h200_prices["H200x8 (Shadeform)"] = f"${price:.2f}/hr"
                        print(f"    ✓ Found: ${price:.2f}/hr")
                        print(f"    Context: {result.get('context', '')}")
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
    
    def save_to_json(self, prices: Dict[str, str], filename: str = "shadeform_h200_prices.json") -> bool:
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
                    "Shadeform": {
                        "name": "Shadeform",
                        "url": self.base_url,
                        "variants": {
                            "H200x8 (Shadeform)": {
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
                    "instance_type": "H200x8 Bare Metal",
                    "gpu_model": "NVIDIA H200",
                    "gpu_memory": "141GB HBM3e",
                    "gpu_count_per_instance": 8,
                    "pricing_type": "On-Demand",
                    "pricing_unit": "per GPU per hour",
                    "source": "https://www.shadeform.ai/"
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
    """Main function to run the Shadeform H200 scraper"""
    print("🚀 Shadeform H200 GPU Pricing Scraper")
    print("=" * 80)
    print("Note: Shadeform offers H200x8 Bare Metal servers on-demand")
    print("=" * 80)
    
    scraper = ShadeformH200Scraper()
    
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
