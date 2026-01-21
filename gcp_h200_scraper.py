#!/usr/bin/env python3
"""
Google Cloud A3 Ultra (H200 GPU) Price Scraper
Extracts H200 pricing from Google Cloud Compute Engine pricing

GCP offers H200 GPUs in A3 Ultra instances (8 x H200 GPUs).

Reference: https://cloud.google.com/compute/gpus-pricing
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
from typing import Dict, Optional


class GCPH200Scraper:
    """Scraper for Google Cloud A3 Ultra (H200) instance pricing"""
    
    def __init__(self):
        self.name = "GCP"
        self.base_url = "https://cloud.google.com/compute/gpus-pricing"
        self.machine_types_url = "https://cloud.google.com/compute/docs/gpus"
        self.pricing_api_url = "https://cloudbilling.googleapis.com/v1/services"
        # Vantage.sh aggregates cloud pricing - A3 Ultra has H200 GPUs
        self.vantage_url = "https://instances.vantage.sh/gcp/a3-ultragpu-8g"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
    
    def get_h200_prices(self) -> Dict[str, str]:
        """Main method to extract H200 prices from Google Cloud"""
        print(f"🔍 Fetching {self.name} A3 Ultra (H200) pricing...")
        print("=" * 80)
        
        h200_prices = {}
        
        # Try multiple methods in order - Vantage first as most reliable
        methods = [
            ("Vantage Instance Pricing", self._try_vantage_pricing),
            ("GCP Pricing Page Scraping", self._try_pricing_page),
            ("GCP Machine Types Page", self._try_machine_types_page),
            ("Selenium Scraper", self._try_selenium_scraper),
        ]
        
        for method_name, method_func in methods:
            print(f"\n📋 Method: {method_name}")
            try:
                prices = method_func()
                if prices and self._validate_prices(prices):
                    h200_prices.update(prices)
                    print(f"   ✅ Found {len(prices)} H200 prices!")
                    break  # Return on first successful method
                else:
                    print(f"   ❌ No valid prices found")
            except Exception as e:
                print(f"   ⚠️  Error: {str(e)[:100]}")
                continue
        
        if not h200_prices:
            print("\n❌ All live methods failed - no fallback data (live data only mode)")
            return {}
        
        # Normalize to per-GPU pricing
        normalized_prices = self._normalize_prices(h200_prices)
        
        print(f"\n✅ Final extraction: {len(normalized_prices)} H200 price variants")
        return normalized_prices
    
    def _validate_prices(self, prices: Dict[str, str]) -> bool:
        """Validate that prices are in a reasonable range for H200 GPUs"""
        if not prices:
            return False
        
        for variant, price_str in prices.items():
            if 'Error' in variant:
                continue
            try:
                price_match = re.search(r'\$?([0-9.]+)', str(price_str))
                if price_match:
                    price = float(price_match.group(1))
                    # H200 pricing should be reasonable (GCP is around $8-15/GPU/hr)
                    if 5 < price < 25:
                        return True
            except:
                continue
        return False
    
    def _try_vantage_pricing(self) -> Dict[str, str]:
        """Try to scrape pricing from Vantage.sh which aggregates GCP pricing"""
        h200_prices = {}
        
        try:
            print(f"    Trying: {self.vantage_url}")
            response = requests.get(self.vantage_url, headers=self.headers, timeout=20)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                text_content = soup.get_text()
                
                print(f"      Content length: {len(text_content)}")
                
                # Look for pricing patterns on Vantage
                # Vantage shows prices like "$86.27" or "86.27 USD" for instance pricing
                price_patterns = [
                    r'\$([0-9]+\.?[0-9]*)\s*(?:per\s+hour|/hr|/hour)',
                    r'On.?Demand[:\s]+\$([0-9]+\.?[0-9]*)',
                    r'hourly[:\s]+\$([0-9]+\.?[0-9]*)',
                    r'\$([0-9]+\.[0-9]+)',  # Generic price pattern
                ]
                
                for pattern in price_patterns:
                    matches = re.findall(pattern, text_content, re.IGNORECASE)
                    for match in matches:
                        try:
                            price = float(match)
                            # Instance price should be in $60-150 range for a3-ultragpu-8g
                            if 50 < price < 200:
                                per_gpu_price = price / 8  # 8 GPUs per instance
                                print(f"      ✓ Found instance price: ${price:.2f}/hr")
                                print(f"        Per-GPU: ${per_gpu_price:.2f}/hr")
                                h200_prices['A3-Ultra (Google Cloud)'] = f"${per_gpu_price:.2f}/hr"
                                return h200_prices
                            # Already per-GPU price
                            elif 5 < price < 20:
                                print(f"      ✓ Found per-GPU price: ${price:.2f}/hr")
                                h200_prices['A3-Ultra (Google Cloud)'] = f"${price:.2f}/hr"
                                return h200_prices
                        except ValueError:
                            continue
                
                print(f"      ⚠️  No H200 pricing found in expected range")
                
            else:
                print(f"      Status {response.status_code}")
                
        except Exception as e:
            print(f"      Error: {str(e)[:50]}...")
        
        return h200_prices
    
    def _try_pricing_page(self) -> Dict[str, str]:
        """Scrape the GCP GPU pricing page for H200 prices"""
        h200_prices = {}
        
        try:
            print(f"    Trying: {self.base_url}")
            response = requests.get(self.base_url, headers=self.headers, timeout=20)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                text_content = soup.get_text()
                html_content = str(soup)
                
                print(f"      Content length: {len(text_content)}")
                
                # Check if page contains H200 or A3 Ultra or nvidia-h200 data
                has_h200 = ('H200' in text_content or 'h200' in text_content.lower() or 
                            'a3-ultra' in text_content.lower() or 'nvidia-h200' in html_content.lower() or
                            'a3ultra' in text_content.lower())
                
                if not has_h200:
                    print(f"      ⚠️  No H200/A3 Ultra content found in text")
                    # Still try extraction - sometimes content is in HTML attributes
                
                print(f"      ✓ Attempting price extraction...")
                
                # Extract from pricing tables
                found_prices = self._extract_from_tables(soup)
                if found_prices:
                    h200_prices.update(found_prices)
                    return h200_prices
                
                # Extract from text patterns
                found_prices = self._extract_from_text(text_content)
                if found_prices:
                    h200_prices.update(found_prices)
                    return h200_prices
                    
            else:
                print(f"      Status {response.status_code}")
                
        except Exception as e:
            print(f"      Error: {str(e)[:50]}...")
        
        return h200_prices
    
    def _try_machine_types_page(self) -> Dict[str, str]:
        """Try the GCP machine types documentation page"""
        h200_prices = {}
        
        try:
            print(f"    Trying: {self.machine_types_url}")
            response = requests.get(self.machine_types_url, headers=self.headers, timeout=20)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                text_content = soup.get_text()
                
                print(f"      Content length: {len(text_content)}")
                
                # Look for A3 Ultra pricing patterns
                if 'a3-ultra' in text_content.lower() or 'H200' in text_content:
                    print(f"      ✓ Found A3 Ultra/H200 content")
                    
                    found_prices = self._extract_from_tables(soup)
                    if found_prices:
                        h200_prices.update(found_prices)
                        return h200_prices
                    
                    found_prices = self._extract_from_text(text_content)
                    if found_prices:
                        h200_prices.update(found_prices)
                else:
                    print(f"      ⚠️  No A3 Ultra/H200 content found")
                    
            else:
                print(f"      Status {response.status_code}")
                
        except Exception as e:
            print(f"      Error: {str(e)[:50]}...")
        
        return h200_prices
    
    def _extract_from_tables(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract H200 prices from HTML tables - handles 8-GPU instance pricing"""
        prices = {}
        
        tables = soup.find_all('table')
        print(f"      Found {len(tables)} tables")
        
        for table in tables:
            table_text = table.get_text()
            table_html = str(table)
            
            # Look for H200 or A3 Ultra mentions (case insensitive)
            has_h200 = ('H200' in table_text or 'h200' in table_text.lower() or 
                        'a3-ultra' in table_text.lower() or 'a3ultra' in table_text.lower() or
                        'nvidia-h200' in table_html.lower())
            
            if not has_h200:
                continue
            
            print(f"      📋 Processing table with H200/A3 Ultra data")
            
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                row_text = ' '.join([cell.get_text().strip() for cell in cells])
                
                # Check for H200/A3/accelerator rows
                has_h200_row = ('H200' in row_text or 'h200' in row_text.lower() or 
                                'a3-ultra' in row_text.lower() or 'a3ultra' in row_text.lower() or
                                'nvidia-h200' in row_text.lower() or 'accelerator' in row_text.lower())
                
                if has_h200_row and '$' in row_text:
                    print(f"         Row: {row_text[:150]}")
                    
                    # Extract all prices from the row
                    price_matches = re.findall(r'\$([0-9.]+)', row_text)
                    
                    for price_str in price_matches:
                        try:
                            instance_price = float(price_str)
                            
                            # GCP A3 Ultra VMs have 8 x H200 GPUs
                            # Instance prices ~$60-150/hr → divide by 8 for per-GPU
                            if 50 < instance_price < 200:
                                per_gpu_price = instance_price / 8
                                variant_name = "A3-Ultra (Google Cloud)"
                                if variant_name not in prices:
                                    prices[variant_name] = f"${per_gpu_price:.2f}/hr"
                                    print(f"        Table ✓ {variant_name} = ${per_gpu_price:.2f}/hr (from ${instance_price:.2f}/instance ÷ 8 GPUs)")
                            # Also accept already per-GPU prices
                            elif 3 < instance_price < 20:
                                variant_name = "A3-Ultra (Google Cloud)"
                                if variant_name not in prices:
                                    prices[variant_name] = f"${instance_price:.2f}/hr"
                                    print(f"        Table ✓ {variant_name} = ${instance_price:.2f}/hr")
                        except ValueError:
                            continue
        
        return prices
    
    def _extract_from_text(self, text_content: str) -> Dict[str, str]:
        """Extract H200 prices from text content - handles 8-GPU instance pricing"""
        prices = {}
        
        # GCP pricing patterns for A3 Ultra VMs with H200
        # Looking for patterns like "$86.27 / 1 hour" near H200/A3 mentions
        
        # Pattern to find price mentions
        price_patterns = [
            r'a3-ultra.*?\$([0-9.]+)',
            r'a3ultra.*?\$([0-9.]+)',
            r'nvidia-h200.*?\$([0-9.]+)',
            r'H200.*?\$([0-9.]+)',
            r'\$([0-9.]+).*?(?:per|/)?\s*(?:1\s+)?hour',
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE | re.DOTALL)
            
            for price_str in matches:
                try:
                    instance_price = float(price_str)
                    
                    # Check if this is an 8-GPU instance price (~$60-150/hr)
                    if 50 < instance_price < 200:
                        per_gpu_price = instance_price / 8
                        variant_name = "A3-Ultra (Google Cloud)"
                        if variant_name not in prices:
                            prices[variant_name] = f"${per_gpu_price:.2f}/hr"
                            print(f"        Pattern ✓ {variant_name} = ${per_gpu_price:.2f}/hr (from ${instance_price:.2f}/instance ÷ 8 GPUs)")
                            return prices  # Found valid price, return immediately
                    # Already per-GPU price
                    elif 3 < instance_price < 20:
                        variant_name = "A3-Ultra (Google Cloud)"
                        if variant_name not in prices:
                            prices[variant_name] = f"${instance_price:.2f}/hr"
                            print(f"        Pattern ✓ {variant_name} = ${instance_price:.2f}/hr")
                            return prices
                except ValueError:
                    continue
        
        return prices
    
    def _try_selenium_scraper(self) -> Dict[str, str]:
        """Use Selenium to scrape JavaScript-loaded pricing from GCP"""
        h200_prices = {}
        
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.common.exceptions import WebDriverException
            
            print("    Setting up Selenium WebDriver...")
            
            # Configure Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Initialize the driver
            driver = webdriver.Chrome(options=chrome_options)
            
            try:
                print(f"    Loading GCP pricing page...")
                driver.get(self.base_url)
                
                # Wait for page to load
                print("    Waiting for dynamic content to load...")
                time.sleep(5)
                
                # Get the page source
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                text_content = soup.get_text()
                
                print(f"    ✓ Page loaded, content length: {len(text_content)}")
                
                # Check for H200 content
                if 'H200' in text_content or 'a3-ultra' in text_content.lower():
                    print(f"      ✓ Found H200/A3 Ultra content")
                    
                    # Try to extract pricing
                    found_prices = self._extract_from_tables(soup)
                    if found_prices:
                        h200_prices.update(found_prices)
                    else:
                        found_prices = self._extract_from_text(text_content)
                        if found_prices:
                            h200_prices.update(found_prices)
                
            finally:
                driver.quit()
                print("    WebDriver closed")
                
        except ImportError:
            print("      ⚠️  Selenium not installed. Run: pip install selenium")
        except Exception as e:
            print(f"      ⚠️  Error: {str(e)[:100]}")
        
        return h200_prices
    
    def _get_known_pricing(self) -> Dict[str, str]:
        """
        Get known GCP A3 Ultra (H200) pricing as fallback.
        Based on publicly available pricing data.
        
        Reference: https://cloud.google.com/compute/gpus-pricing
        
        A3 Ultra (a3-ultragpu-8g): 8 x H200 GPUs
        - H200 Spot price: $3.7247/GPU/hr
        - On-demand estimated: ~$10-11/GPU/hr based on instance pricing
        
        $63,334.74/month ÷ 730 hours ÷ 8 GPUs ≈ $10.85/GPU/hr
        """
        print("    Using known GCP A3 Ultra (H200) pricing data...")
        
        known_prices = {
            'A3-Ultra (us-central1)': '$10.85/hr',
            'A3-Ultra (us-east4)': '$10.85/hr',
            'A3-Ultra (europe-west4)': '$11.50/hr',
        }
        
        print(f"    ✅ Using {len(known_prices)} known pricing entries")
        return known_prices
    
    def _normalize_prices(self, prices: Dict[str, str]) -> Dict[str, str]:
        """
        Normalize prices - Calculate per-GPU pricing if needed.
        Calculate average across all regions for a single representative price.
        """
        if not prices:
            return {}
        
        per_gpu_prices = []
        
        print("\n   📊 Normalizing GCP A3 Ultra (H200) pricing...")
        
        for variant, price_str in prices.items():
            if 'Error' in variant:
                continue
            
            try:
                # Extract price value
                price_match = re.search(r'\$([0-9.]+)', price_str)
                if price_match:
                    price = float(price_match.group(1))
                    per_gpu_prices.append(price)
                    print(f"      {variant}: ${price:.2f}/hr")
                    
            except (ValueError, TypeError) as e:
                print(f"      ⚠️ Error normalizing {variant}: {e}")
                continue
        
        if per_gpu_prices:
            # Calculate average per-GPU price across all regions
            avg_per_gpu = sum(per_gpu_prices) / len(per_gpu_prices)
            print(f"\n   ✅ Averaged {len(per_gpu_prices)} regional prices → ${avg_per_gpu:.2f}/GPU")
            
            # Return single normalized price
            return {
                'A3-Ultra (GCP)': f"${avg_per_gpu:.2f}/hr"
            }
        
        return {}
    
    def save_to_json(self, prices: Dict[str, str], filename: str = "gcp_h200_prices.json") -> bool:
        """Save results to a JSON file in the same format as other scrapers"""
        try:
            # Extract numeric price for the structured format
            price_value = 0.0
            if prices:
                for variant, price_str in prices.items():
                    price_match = re.search(r'\$([0-9.]+)', price_str)
                    if price_match:
                        price_value = float(price_match.group(1))
                        break
            
            output_data = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "provider": self.name,
                "providers": {
                    "GCP": {
                        "name": "Google Cloud",
                        "url": self.base_url,
                        "variants": {
                            "A3-Ultra (GCP)": {
                                "gpu_model": "H200",
                                "gpu_memory": "141GB",
                                "price_per_hour": price_value,
                                "currency": "USD",
                                "availability": "on-demand"
                            }
                        }
                    }
                },
                "notes": {
                    "instance_type": "a3-ultragpu-8g",
                    "gpu_model": "NVIDIA H200",
                    "gpu_memory": "141GB HBM3e",
                    "gpu_count_per_instance": 8,
                    "pricing_type": "On-Demand",
                    "source": "https://cloud.google.com/compute/gpus-pricing"
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
    """Main function to run the GCP A3 Ultra (H200) scraper"""
    print("🚀 Google Cloud A3 Ultra (H200) GPU Pricing Scraper")
    print("=" * 80)
    print("Note: GCP offers H200 GPUs in a3-ultragpu-8g instances (8 x H200)")
    print("=" * 80)
    
    scraper = GCPH200Scraper()
    
    start_time = time.time()
    prices = scraper.get_h200_prices()
    end_time = time.time()
    
    print(f"\n⏱️  Scraping completed in {end_time - start_time:.2f} seconds")
    
    # Display results
    if prices and 'Error' not in str(prices):
        print(f"\n✅ Successfully extracted {len(prices)} H200 price entries:\n")
        
        for variant, price in sorted(prices.items()):
            print(f"  • {variant:50s} {price}")
        
        # Save results to JSON
        scraper.save_to_json(prices)
    else:
        print("\n❌ No valid pricing data found")


if __name__ == "__main__":
    main()
