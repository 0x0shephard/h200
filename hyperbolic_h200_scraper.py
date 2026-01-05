#!/usr/bin/env python3
"""
Hyperbolic H200 GPU Price Scraper
Extracts H200 pricing from Hyperbolic AI Marketplace

Hyperbolic offers H200 GPUs on-demand.

Reference: https://www.hyperbolic.ai/marketplace
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
from typing import Dict, Optional


class HyperbolicH200Scraper:
    """Scraper for Hyperbolic AI H200 GPU pricing"""
    
    def __init__(self):
        self.name = "Hyperbolic"
        self.base_url = "https://www.hyperbolic.ai/marketplace"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
    
    def get_h200_prices(self) -> Dict[str, str]:
        """Main method to extract H200 prices from Hyperbolic"""
        print(f"🔍 Fetching {self.name} H200 pricing...")
        print("=" * 80)
        
        h200_prices = {}
        
        # Try multiple methods - prioritize Selenium since page is JS-heavy
        methods = [
            ("Selenium Scraper", self._try_selenium_scraper),
            ("Hyperbolic Website Scraping", self._try_pricing_page),
        ]
        
        for method_name, method_func in methods:
            print(f"\n📋 Method: {method_name}")
            try:
                prices = method_func()
                if prices and self._validate_prices(prices):
                    h200_prices.update(prices)
                    print(f"   ✅ Found H200 prices!")
                    break
                else:
                    print(f"   ❌ No valid prices found")
            except Exception as e:
                print(f"   ⚠️  Error: {str(e)[:100]}")
                continue
        
        if not h200_prices:
            print("\n❌ Failed to extract H200 pricing from Hyperbolic")
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
                    # Hyperbolic H200 pricing is around $2-5/hr
                    if 1.0 < price < 10.0:
                        return True
            except:
                continue
        return False
    
    def _try_pricing_page(self) -> Dict[str, str]:
        """Scrape Hyperbolic website for H200 pricing using requests"""
        h200_prices = {}
        
        try:
            print(f"    Trying: {self.base_url}")
            response = requests.get(self.base_url, headers=self.headers, timeout=20)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                text_content = soup.get_text()
                
                print(f"      Content length: {len(text_content)}")
                
                # Try to extract from JSON-LD structured data first
                json_ld_price = self._extract_from_json_ld(soup)
                if json_ld_price:
                    h200_prices["H200 (Hyperbolic)"] = f"${json_ld_price:.2f}/hr"
                    return h200_prices
                
                # Extract from page content
                prices = self._extract_prices(soup, text_content)
                if prices:
                    h200_prices.update(prices)
                    
            else:
                print(f"      Status {response.status_code}")
                
        except Exception as e:
            print(f"      Error: {str(e)[:50]}...")
        
        return h200_prices
    
    def _extract_from_json_ld(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract H200 price from JSON-LD structured data"""
        script_tags = soup.find_all('script', type='application/ld+json')
        
        for script in script_tags:
            try:
                data = json.loads(script.string)
                
                # Handle array or single object
                items = data if isinstance(data, list) else [data]
                
                for item in items:
                    if item.get('@type') == 'Product':
                        name = item.get('name', '')
                        if 'H200' in name:
                            offers = item.get('offers', {})
                            price = offers.get('price')
                            if price:
                                print(f"        ✓ Found H200 in JSON-LD: ${float(price):.2f}/hr")
                                return float(price)
                                
            except (json.JSONDecodeError, TypeError, ValueError):
                continue
        
        return None
    
    def _extract_prices(self, soup: BeautifulSoup, text_content: str) -> Dict[str, str]:
        """Extract H200 prices from page content"""
        prices = {}
        
        # Look for H200 followed by price pattern
        patterns = [
            r'Nvidia\s+H200[^$]*\$([0-9.]+)\s*/\s*HR',
            r'H200[^$]*\$([0-9.]+)\s*/\s*HR',
            r'H200[^$]*\$([0-9.]+)\s*/\s*hour',
            r'H200[^$]*\$([0-9.]+)\s*per\s*hour',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for price_str in matches:
                try:
                    price = float(price_str)
                    if 1.0 < price < 10.0:
                        print(f"        ✓ Found H200 price via pattern: ${price:.2f}/hr")
                        prices["H200 (Hyperbolic)"] = f"${price:.2f}/hr"
                        return prices
                except ValueError:
                    continue
        
        return prices
    
    def _try_selenium_scraper(self) -> Dict[str, str]:
        """Use Selenium to scrape JavaScript-loaded pricing from Hyperbolic"""
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
                print(f"    Loading Hyperbolic marketplace page...")
                driver.get(self.base_url)
                
                print("    Waiting for dynamic content to load...")
                time.sleep(5)
                
                # First try to extract from JSON-LD
                script = """
                    // Try JSON-LD first
                    const jsonLdScripts = document.querySelectorAll('script[type="application/ld+json"]');
                    for (const script of jsonLdScripts) {
                        try {
                            const data = JSON.parse(script.textContent);
                            const items = Array.isArray(data) ? data : [data];
                            for (const item of items) {
                                if (item['@type'] === 'Product' && item.name && item.name.includes('H200')) {
                                    if (item.offers && item.offers.price) {
                                        return { price: item.offers.price, source: 'json-ld' };
                                    }
                                }
                            }
                        } catch (e) { continue; }
                    }
                    
                    // Fallback: search page text
                    const bodyText = document.body.innerText;
                    
                    // Look for H200 price patterns
                    const patterns = [
                        /Nvidia\\s+H200[^$]*\\$([0-9.]+)\\s*\\/\\s*HR/i,
                        /H200[^$]*\\$([0-9.]+)\\s*\\/\\s*HR/i,
                        /H200[^$]*\\$([0-9.]+)\\s*\\/\\s*hour/i
                    ];
                    
                    for (const pattern of patterns) {
                        const match = bodyText.match(pattern);
                        if (match) {
                            return { price: parseFloat(match[1]), source: 'text' };
                        }
                    }
                    
                    return null;
                """
                
                result = driver.execute_script(script)
                
                if result and result.get('price'):
                    price = float(result['price'])
                    if 1.0 < price < 10.0:
                        h200_prices["H200 (Hyperbolic)"] = f"${price:.2f}/hr"
                        print(f"    ✓ Found: ${price:.2f}/hr (source: {result.get('source', 'unknown')})")
                else:
                    print("    ⚠️  Could not find H200 pricing via JavaScript")
                    
                    # Fallback to BeautifulSoup
                    page_source = driver.page_source
                    soup = BeautifulSoup(page_source, 'html.parser')
                    
                    # Try JSON-LD first
                    json_ld_price = self._extract_from_json_ld(soup)
                    if json_ld_price:
                        h200_prices["H200 (Hyperbolic)"] = f"${json_ld_price:.2f}/hr"
                    else:
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
    
    def save_to_json(self, prices: Dict[str, str], filename: str = "hyperbolic_h200_prices.json") -> bool:
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
                    "Hyperbolic": {
                        "name": "Hyperbolic AI",
                        "url": self.base_url,
                        "variants": {
                            "H200 (Hyperbolic)": {
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
                    "source": "https://www.hyperbolic.ai/marketplace"
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
    """Main function to run the Hyperbolic H200 scraper"""
    print("🚀 Hyperbolic AI H200 GPU Pricing Scraper")
    print("=" * 80)
    print("Note: Hyperbolic offers H200 GPUs on-demand")
    print("=" * 80)
    
    scraper = HyperbolicH200Scraper()
    
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
