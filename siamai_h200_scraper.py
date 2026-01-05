#!/usr/bin/env python3
"""
Siam.ai H200 GPU Price Scraper
Extracts H200 pricing from Siam.ai

Siam.ai offers H200 and H100 GPUs on-demand.

Reference: https://siam.ai/nvidia-hseries/#
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
from typing import Dict, Optional


class SiamaiH200Scraper:
    """Scraper for Siam.ai H200 GPU pricing"""
    
    def __init__(self):
        self.name = "Siam.ai"
        self.base_url = "https://siam.ai/nvidia-hseries/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
    
    def get_h200_prices(self) -> Dict[str, str]:
        """Main method to extract H200 prices from Siam.ai"""
        print(f"🔍 Fetching {self.name} H200 pricing...")
        print("=" * 80)
        
        h200_prices = {}
        
        # Try multiple methods
        methods = [
            ("Siam.ai Website Scraping", self._try_pricing_page),
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
            print("\n❌ Failed to extract H200 pricing from Siam.ai")
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
                    # Siam.ai H200 pricing is around $2-5/hr
                    if 1.0 < price < 10.0:
                        return True
            except:
                continue
        return False
    
    def _try_pricing_page(self) -> Dict[str, str]:
        """Scrape the Siam.ai website for H200 pricing"""
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
        
        # Method 1: Look for font tags containing prices (Siam.ai uses <font> tags)
        font_tags = soup.find_all('font')
        for font in font_tags:
            font_text = font.get_text()
            if '$' in font_text and '/Hour' in font_text:
                # Check if this is the H200 price by looking at parent context
                parent = font.parent
                if parent:
                    parent_text = parent.get_text()
                    if 'H200' in parent_text:
                        price_match = re.search(r'\$([0-9.]+)/Hour', font_text)
                        if price_match:
                            price = float(price_match.group(1))
                            if 1.0 < price < 10.0:
                                print(f"        ✓ Found H200 price from font tag: ${price:.2f}/hr")
                                prices["H200 (Siam.ai)"] = f"${price:.2f}/hr"
                                return prices
        
        # Method 2: Look in .sub-title class for pricing
        sub_titles = soup.find_all(class_='sub-title')
        for sub_title in sub_titles:
            sub_text = sub_title.get_text()
            if 'H200' in sub_text:
                # Extract H200 price specifically
                h200_match = re.search(r'H200\s+at\s+\$([0-9.]+)/Hour', sub_text, re.IGNORECASE)
                if h200_match:
                    price = float(h200_match.group(1))
                    if 1.0 < price < 10.0:
                        print(f"        ✓ Found H200 price from sub-title: ${price:.2f}/hr")
                        prices["H200 (Siam.ai)"] = f"${price:.2f}/hr"
                        return prices
        
        # Method 3: Direct text pattern matching
        h200_pattern = r'H200\s+at\s+\$([0-9.]+)/Hour'
        matches = re.findall(h200_pattern, text_content, re.IGNORECASE)
        for price_str in matches:
            try:
                price = float(price_str)
                if 1.0 < price < 10.0:
                    print(f"        ✓ Found H200 price via pattern: ${price:.2f}/hr")
                    prices["H200 (Siam.ai)"] = f"${price:.2f}/hr"
                    return prices
            except ValueError:
                continue
        
        # Method 4: General pattern for H200 with price
        h200_pattern2 = r'H200[^$]*\$([0-9.]+)/Hour'
        matches = re.findall(h200_pattern2, text_content, re.IGNORECASE)
        for price_str in matches:
            try:
                price = float(price_str)
                if 1.0 < price < 10.0:
                    print(f"        ✓ Found H200 price via general pattern: ${price:.2f}/hr")
                    prices["H200 (Siam.ai)"] = f"${price:.2f}/hr"
                    return prices
            except ValueError:
                continue
        
        return prices
    
    def _try_selenium_scraper(self) -> Dict[str, str]:
        """Use Selenium to scrape JavaScript-loaded pricing from Siam.ai"""
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
                print(f"    Loading Siam.ai page...")
                driver.get(self.base_url)
                
                print("    Waiting for dynamic content to load...")
                time.sleep(5)
                
                # Use JavaScript to extract H200 pricing
                script = """
                    // Look for font tags with prices
                    const fontElements = Array.from(document.querySelectorAll('font'));
                    for (const font of fontElements) {
                        const text = font.textContent;
                        if (text.includes('$') && text.includes('/Hour')) {
                            const parent = font.parentElement;
                            if (parent && parent.textContent.includes('H200')) {
                                const match = text.match(/\\$([0-9.]+)\\/Hour/);
                                if (match) {
                                    return {
                                        price: match[1],
                                        context: parent.textContent.substring(0, 100)
                                    };
                                }
                            }
                        }
                    }
                    
                    // Look in sub-title class
                    const subTitles = document.querySelectorAll('.sub-title');
                    for (const sub of subTitles) {
                        const text = sub.textContent;
                        if (text.includes('H200')) {
                            const match = text.match(/H200\\s+at\\s+\\$([0-9.]+)\\/Hour/i);
                            if (match) {
                                return {
                                    price: match[1],
                                    context: text.substring(0, 100)
                                };
                            }
                        }
                    }
                    
                    // Fallback: search entire page
                    const bodyText = document.body.innerText;
                    const h200Match = bodyText.match(/H200\\s+at\\s+\\$([0-9.]+)\\/Hour/i);
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
                        h200_prices["H200 (Siam.ai)"] = f"${price:.2f}/hr"
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
    
    def save_to_json(self, prices: Dict[str, str], filename: str = "siamai_h200_prices.json") -> bool:
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
                    "Siam.ai": {
                        "name": "Siam.ai",
                        "url": self.base_url,
                        "variants": {
                            "H200 (Siam.ai)": {
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
                    "instance_type": "On-Demand GPU",
                    "gpu_model": "NVIDIA H200",
                    "gpu_memory": "141GB HBM3e",
                    "gpu_count_per_instance": 1,
                    "pricing_type": "On-Demand",
                    "source": "https://siam.ai/nvidia-hseries/"
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
    """Main function to run the Siam.ai H200 scraper"""
    print("🚀 Siam.ai H200 GPU Pricing Scraper")
    print("=" * 80)
    print("Note: Siam.ai offers H200 GPUs on-demand")
    print("=" * 80)
    
    scraper = SiamaiH200Scraper()
    
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
