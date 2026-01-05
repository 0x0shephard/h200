#!/usr/bin/env python3
"""
AceCloud H200 GPU Price Scraper
Extracts H200 pricing from AceCloud (India)

AceCloud offers H200 GPUs with prices in INR.
This scraper converts INR to USD using live exchange rates.

Reference: https://acecloud.ai/pricing/linux/inr/noida/nvidia-h200-nvl/
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
from typing import Dict, List, Optional, Tuple


class AceCloudH200Scraper:
    """Scraper for AceCloud H200 GPU pricing with INR to USD conversion"""
    
    def __init__(self):
        self.name = "AceCloud"
        self.base_url = "https://acecloud.ai/pricing/linux/inr/noida/nvidia-h200-nvl/"
        # Exchange rate APIs (free, no API key required)
        self.exchange_apis = [
            "https://api.exchangerate-api.com/v4/latest/INR",
            "https://open.er-api.com/v6/latest/INR",
        ]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
    
    def get_inr_to_usd_rate(self) -> Optional[float]:
        """Get live INR to USD exchange rate from multiple APIs"""
        print("    💱 Fetching live INR/USD exchange rate...")
        
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
                            print(f"      ✓ INR/USD rate: {rate}")
                            return float(rate)
                            
            except Exception as e:
                print(f"      ⚠️ Error: {str(e)[:50]}")
                continue
        
        print("      ❌ Failed to get exchange rate from all APIs")
        return None
    
    def get_h200_prices(self) -> Dict[str, str]:
        """Main method to extract H200 prices from AceCloud"""
        print(f"🔍 Fetching {self.name} H200 pricing...")
        print("=" * 80)
        
        # First get the exchange rate
        inr_to_usd = self.get_inr_to_usd_rate()
        if not inr_to_usd:
            print("\n❌ Cannot proceed without exchange rate")
            return {}
        
        all_prices_inr = []
        
        # Try multiple methods
        methods = [
            ("AceCloud Pricing Page Scraping", self._try_pricing_page),
            ("Selenium Scraper", self._try_selenium_scraper),
        ]
        
        for method_name, method_func in methods:
            print(f"\n📋 Method: {method_name}")
            try:
                prices = method_func()
                if prices:
                    all_prices_inr.extend(prices)
                    print(f"   ✅ Found {len(prices)} H200 price entries!")
                    break
                else:
                    print(f"   ❌ No valid prices found")
            except Exception as e:
                print(f"   ⚠️  Error: {str(e)[:100]}")
                continue
        
        if not all_prices_inr:
            print("\n❌ Failed to extract H200 pricing from AceCloud")
            return {}
        
        # Calculate average per-GPU monthly price in INR
        avg_inr_monthly = sum(all_prices_inr) / len(all_prices_inr)
        
        # Convert monthly to hourly (assuming 730 hours per month)
        hours_per_month = 730
        avg_inr_hourly = avg_inr_monthly / hours_per_month
        
        # Convert to USD
        avg_usd_hourly = avg_inr_hourly * inr_to_usd
        
        print(f"\n   📊 Price Statistics:")
        print(f"      Per-GPU Monthly (INR): ₹{avg_inr_monthly:,.0f}")
        print(f"      Per-GPU Hourly (INR): ₹{avg_inr_hourly:.2f}")
        print(f"      Per-GPU Hourly (USD): ${avg_usd_hourly:.2f}")
        print(f"      Exchange Rate: 1 INR = {inr_to_usd:.6f} USD")
        
        result = {
            "H200 (AceCloud)": f"${avg_usd_hourly:.2f}/hr",
            "_inr_monthly": avg_inr_monthly,
            "_exchange_rate": inr_to_usd,
            "_all_prices_inr": all_prices_inr
        }
        
        print(f"\n✅ Final extraction complete")
        return result
    
    def _try_pricing_page(self) -> List[float]:
        """Scrape AceCloud pricing page for H200 prices"""
        all_prices = []
        
        try:
            print(f"    Trying: {self.base_url}")
            response = requests.get(self.base_url, headers=self.headers, timeout=20)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                text_content = soup.get_text()
                
                print(f"      Content length: {len(text_content)}")
                
                # Check if page contains H200 data
                if 'H200' not in text_content and 'N.H200' not in text_content:
                    print(f"      ⚠️  No H200 content found")
                    return all_prices
                
                print(f"      ✓ Found H200 content")
                
                # Extract from table
                prices = self._extract_from_table(soup)
                if prices:
                    all_prices.extend(prices)
                    
            else:
                print(f"      Status {response.status_code}")
                
        except Exception as e:
            print(f"      Error: {str(e)[:50]}...")
        
        return all_prices
    
    def _extract_from_table(self, soup: BeautifulSoup) -> List[float]:
        """Extract H200 per-GPU monthly prices from the pricing table"""
        prices = []
        
        # Find the compute data table
        table = soup.find('table', id='compute_data')
        if not table:
            # Try to find any table with H200 data
            tables = soup.find_all('table')
            for t in tables:
                if 'H200' in t.get_text():
                    table = t
                    break
        
        if not table:
            print("      ⚠️ Pricing table not found")
            return prices
        
        print(f"      📋 Found pricing table")
        
        # Process table rows
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 5:
                row_text = ' '.join([cell.get_text().strip() for cell in cells])
                
                # Look for H200 rows
                if 'N.H200' in row_text or 'H200' in row_text:
                    print(f"        Row: {row_text[:100]}")
                    
                    # Extract GPU count (column 1)
                    gpu_count_text = cells[1].get_text().strip()
                    gpu_count_match = re.search(r'(\d+)x?', gpu_count_text)
                    gpu_count = int(gpu_count_match.group(1)) if gpu_count_match else 1
                    
                    # Extract monthly price (column 4)
                    monthly_price_text = cells[4].get_text().strip()
                    # Remove ₹ and commas
                    price_clean = re.sub(r'[₹,\s]', '', monthly_price_text)
                    
                    try:
                        monthly_price = float(price_clean)
                        # Calculate per-GPU price
                        per_gpu_price = monthly_price / gpu_count
                        prices.append(per_gpu_price)
                        print(f"        ✓ {gpu_count}x GPU, ₹{monthly_price:,.0f}/month → ₹{per_gpu_price:,.0f}/GPU/month")
                    except ValueError:
                        continue
        
        return prices
    
    def _try_selenium_scraper(self) -> List[float]:
        """Use Selenium to scrape JavaScript-loaded pricing from AceCloud"""
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
                print(f"    Loading AceCloud pricing page...")
                driver.get(self.base_url)
                
                print("    Waiting for dynamic content to load...")
                time.sleep(5)
                
                # Use JavaScript to extract H200 pricing from table
                script = """
                    const prices = [];
                    const table = document.querySelector('table#compute_data') || 
                                  Array.from(document.querySelectorAll('table')).find(t => t.innerText.includes('H200'));
                    
                    if (!table) return prices;
                    
                    const rows = table.querySelectorAll('tbody tr');
                    rows.forEach(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 5) {
                            const flavour = cells[0].innerText;
                            if (flavour.includes('H200')) {
                                // GPU count (column 1)
                                const gpuText = cells[1].innerText;
                                const gpuMatch = gpuText.match(/(\\d+)x?/);
                                const gpuCount = gpuMatch ? parseInt(gpuMatch[1]) : 1;
                                
                                // Monthly price (column 4)
                                const priceText = cells[4].innerText.replace(/[₹,\\s]/g, '');
                                const monthlyPrice = parseFloat(priceText);
                                
                                if (!isNaN(monthlyPrice)) {
                                    const perGpuPrice = monthlyPrice / gpuCount;
                                    prices.push({
                                        flavour: flavour,
                                        gpuCount: gpuCount,
                                        monthlyPrice: monthlyPrice,
                                        perGpuPrice: perGpuPrice
                                    });
                                }
                            }
                        }
                    });
                    
                    return prices;
                """
                
                result = driver.execute_script(script)
                
                if result and len(result) > 0:
                    for item in result:
                        all_prices.append(item['perGpuPrice'])
                        print(f"    ✓ {item['flavour']}: {item['gpuCount']}x GPU, ₹{item['monthlyPrice']:,.0f}/month → ₹{item['perGpuPrice']:,.0f}/GPU/month")
                else:
                    print("    ⚠️  Could not find H200 pricing via JavaScript")
                    
                    # Fallback to BeautifulSoup
                    page_source = driver.page_source
                    soup = BeautifulSoup(page_source, 'html.parser')
                    prices = self._extract_from_table(soup)
                    if prices:
                        all_prices.extend(prices)
                
            finally:
                driver.quit()
                print("    WebDriver closed")
                
        except ImportError:
            print("      ⚠️  Selenium not installed. Run: pip install selenium")
        except Exception as e:
            print(f"      ⚠️  Error: {str(e)[:100]}")
        
        return all_prices
    
    def save_to_json(self, prices: Dict[str, str], filename: str = "acecloud_h200_prices.json") -> bool:
        """Save results to a JSON file"""
        try:
            # Extract values
            usd_price = 0.0
            inr_monthly = 0.0
            exchange_rate = 0.0
            all_prices = []
            
            for key, value in prices.items():
                if key == "_inr_monthly":
                    inr_monthly = value
                elif key == "_exchange_rate":
                    exchange_rate = value
                elif key == "_all_prices_inr":
                    all_prices = value
                elif not key.startswith("_"):
                    price_match = re.search(r'\$([0-9.]+)', str(value))
                    if price_match:
                        usd_price = float(price_match.group(1))
            
            output_data = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "provider": self.name,
                "providers": {
                    "AceCloud": {
                        "name": "AceCloud (India)",
                        "url": self.base_url,
                        "variants": {
                            "H200 (AceCloud)": {
                                "gpu_model": "H200",
                                "gpu_memory": "141GB",
                                "price_per_hour": round(usd_price, 2),
                                "currency": "USD",
                                "availability": "on-demand"
                            }
                        }
                    }
                },
                "notes": {
                    "instance_type": "Various (1x, 2x, 4x H200)",
                    "gpu_model": "NVIDIA H200 NVL",
                    "gpu_memory": "141GB HBM3e",
                    "pricing_type": "Monthly (converted to hourly)",
                    "original_currency": "INR",
                    "original_price_inr_monthly": round(inr_monthly, 0),
                    "exchange_rate_inr_to_usd": round(exchange_rate, 6),
                    "location": "Noida, India",
                    "source": "https://acecloud.ai/pricing/linux/inr/noida/nvidia-h200-nvl/"
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
    """Main function to run the AceCloud H200 scraper"""
    print("🚀 AceCloud H200 GPU Pricing Scraper")
    print("=" * 80)
    print("Note: AceCloud prices are in INR, converting to USD hourly rate")
    print("=" * 80)
    
    scraper = AceCloudH200Scraper()
    
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
