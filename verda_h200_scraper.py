#!/usr/bin/env python3
"""
Verda H200 GPU Price Scraper
Extracts H200 pricing from Verda cloud

Verda offers H200 SXM5 GPUs with on-demand and spot pricing.

Reference: https://verda.com/h200-sxm5
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
from typing import Dict, Optional


class VerdaH200Scraper:
    """Scraper for Verda H200 GPU pricing"""
    
    def __init__(self):
        self.name = "Verda"
        self.base_url = "https://verda.com/h200-sxm5"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
    
    def get_h200_prices(self) -> Dict[str, str]:
        """Main method to extract H200 prices from Verda"""
        print(f"🔍 Fetching {self.name} H200 pricing...")
        print("=" * 80)
        
        h200_prices = {}
        
        # Try multiple methods
        methods = [
            ("Verda Pricing Page Scraping", self._try_pricing_page),
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
            print("\n❌ Failed to extract H200 pricing from Verda")
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
                    # Verda H200 pricing is around $2-4/hr
                    if 1.0 < price < 10.0:
                        return True
            except:
                continue
        return False
    
    def _try_pricing_page(self) -> Dict[str, str]:
        """Scrape the Verda H200 pricing page"""
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
                
                # Extract prices from the page
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
        
        # Look for price patterns: $X.XX/h
        price_patterns = [
            (r'\$([0-9.]+)/h', 'hourly'),
            (r'\$([0-9.]+)\s*/\s*h', 'hourly'),
            (r'\$([0-9.]+)\s*per\s*hour', 'hourly'),
        ]
        
        # First, try to find on-demand price
        on_demand_price = None
        spot_price = None
        
        # Look for on-demand price near "on-demand" or "fixed" text
        on_demand_section = re.search(
            r'(?:on-demand|fixed)[^\$]*\$([0-9.]+)/h',
            text_content, re.IGNORECASE
        )
        if on_demand_section:
            on_demand_price = float(on_demand_section.group(1))
            print(f"        ✓ Found on-demand price: ${on_demand_price:.2f}/hr")
        
        # Look for spot price near "spot" text
        spot_section = re.search(
            r'spot[^\$]*\$([0-9.]+)/h',
            text_content, re.IGNORECASE
        )
        if spot_section:
            spot_price = float(spot_section.group(1))
            print(f"        ✓ Found spot price: ${spot_price:.2f}/hr")
        
        # If we didn't find labeled prices, look for any price pattern
        if not on_demand_price:
            all_prices = re.findall(r'\$([0-9.]+)/h', text_content)
            if all_prices:
                # Usually the higher price is on-demand
                price_values = [float(p) for p in all_prices if 1.0 < float(p) < 10.0]
                if price_values:
                    on_demand_price = max(price_values)
                    print(f"        ✓ Found price: ${on_demand_price:.2f}/hr")
                    if len(price_values) > 1:
                        spot_price = min(price_values)
                        print(f"        ✓ Found spot price: ${spot_price:.2f}/hr")
        
        # Build result dictionary
        if on_demand_price:
            prices["H200 SXM5 On-Demand (Verda)"] = f"${on_demand_price:.2f}/hr"
        if spot_price:
            prices["H200 SXM5 Spot (Verda)"] = f"${spot_price:.2f}/hr"
        
        return prices
    
    def _try_selenium_scraper(self) -> Dict[str, str]:
        """Use Selenium to scrape JavaScript-loaded pricing from Verda"""
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
                print(f"    Loading Verda page...")
                driver.get(self.base_url)
                
                print("    Waiting for dynamic content to load...")
                time.sleep(5)
                
                # Use JavaScript to extract pricing
                script = """
                    const text = document.body.innerText;
                    const prices = {};
                    
                    // Look for on-demand price
                    const onDemandMatch = text.match(/on-demand[^\\$]*\\$([0-9.]+)\\/h/i);
                    if (onDemandMatch) {
                        prices.onDemand = onDemandMatch[1];
                    }
                    
                    // Look for spot price
                    const spotMatch = text.match(/spot[^\\$]*\\$([0-9.]+)\\/h/i);
                    if (spotMatch) {
                        prices.spot = spotMatch[1];
                    }
                    
                    // Fallback: find all prices
                    if (!prices.onDemand) {
                        const allPrices = text.match(/\\$([0-9.]+)\\/h/g);
                        if (allPrices && allPrices.length > 0) {
                            prices.all = allPrices;
                        }
                    }
                    
                    return prices;
                """
                
                result = driver.execute_script(script)
                
                if result:
                    if result.get('onDemand'):
                        price = float(result['onDemand'])
                        h200_prices["H200 SXM5 On-Demand (Verda)"] = f"${price:.2f}/hr"
                        print(f"    ✓ On-demand: ${price:.2f}/hr")
                    
                    if result.get('spot'):
                        price = float(result['spot'])
                        h200_prices["H200 SXM5 Spot (Verda)"] = f"${price:.2f}/hr"
                        print(f"    ✓ Spot: ${price:.2f}/hr")
                    
                    if result.get('all') and not h200_prices:
                        # Parse all prices found
                        for p in result['all']:
                            price_match = re.search(r'\$([0-9.]+)', p)
                            if price_match:
                                price = float(price_match.group(1))
                                if 2.0 < price < 5.0:
                                    h200_prices["H200 SXM5 (Verda)"] = f"${price:.2f}/hr"
                                    print(f"    ✓ Found: ${price:.2f}/hr")
                                    break
                else:
                    print("    ⚠️  Could not find pricing via JavaScript")
                    
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
    
    def save_to_json(self, prices: Dict[str, str], filename: str = "verda_h200_prices.json") -> bool:
        """Save results to a JSON file"""
        try:
            # Extract prices
            on_demand_price = 0.0
            spot_price = 0.0
            
            for variant, price_str in prices.items():
                price_match = re.search(r'\$([0-9.]+)', price_str)
                if price_match:
                    price = float(price_match.group(1))
                    if 'Spot' in variant:
                        spot_price = price
                    else:
                        on_demand_price = price
            
            # Use on-demand as the primary price
            primary_price = on_demand_price if on_demand_price > 0 else spot_price
            
            output_data = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "provider": self.name,
                "providers": {
                    "Verda": {
                        "name": "Verda",
                        "url": self.base_url,
                        "variants": {
                            "H200 SXM5 (Verda)": {
                                "gpu_model": "H200",
                                "gpu_memory": "141GB",
                                "price_per_hour": round(primary_price, 2),
                                "currency": "USD",
                                "availability": "on-demand"
                            }
                        }
                    }
                },
                "notes": {
                    "instance_type": "H200 SXM5",
                    "gpu_model": "NVIDIA H200 SXM5",
                    "gpu_memory": "141GB HBM3e",
                    "gpu_count_per_instance": 1,
                    "pricing_type": "On-Demand",
                    "on_demand_price": round(on_demand_price, 2) if on_demand_price > 0 else None,
                    "spot_price": round(spot_price, 2) if spot_price > 0 else None,
                    "location": "Europe",
                    "source": "https://verda.com/h200-sxm5"
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
    """Main function to run the Verda H200 scraper"""
    print("🚀 Verda H200 GPU Pricing Scraper")
    print("=" * 80)
    print("Note: Verda offers H200 SXM5 GPUs from European locations")
    print("=" * 80)
    
    scraper = VerdaH200Scraper()
    
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
