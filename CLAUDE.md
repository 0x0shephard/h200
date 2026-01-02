# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains web scrapers for collecting NVIDIA H200 GPU pricing data from cloud providers including AWS, Azure, GCP, Oracle Cloud, and specialized GPU cloud providers (HyperStack, CoreWeave, RunPod, Sesterce, Genesis Cloud). Each scraper extracts pricing information and normalizes it to a per-GPU hourly rate format, saving results to JSON files.

## Running the Scrapers

Each cloud provider has its own scraper script:

```bash
# Run individual scrapers - Major cloud providers
python3 aws_h200_scraper.py
python3 azure_h200_scraper.py
python3 gcp_h200_scraper.py
python3 oracle_h200_scraper.py

# Specialized GPU cloud providers
python3 hyperstack_h200_scraper.py
python3 coreweave_h200_scraper.py
python3 runpod_h200_scraper.py
python3 sesterce_h200_scraper.py
python3 genesiscloud_h200_scraper.py
```

Each scraper will:
- Attempt multiple scraping methods (API, web scraping, Selenium)
- Fall back to known pricing data if all methods fail
- Save results to `<provider>_h200_prices.json`

## Dependencies

Core dependencies (required):
```bash
pip install requests beautifulsoup4
```

Optional dependency for JavaScript-heavy pages:
```bash
pip install selenium
```

Note: Selenium requires ChromeDriver to be installed separately.

## Architecture

### Scraper Pattern

All scrapers follow a consistent architecture:

1. **Class-based structure**: Each provider has a dedicated scraper class (e.g., `AWSH200Scraper`)
2. **Multi-method approach**: Scrapers try multiple extraction methods in order of reliability:
   - Provider API (if available)
   - Standard web scraping (BeautifulSoup)
   - Selenium-based scraping (for JavaScript-rendered content)
3. **Fallback to known pricing**: If all methods fail, scrapers use hardcoded known prices
4. **Normalization**: Raw prices are normalized to per-GPU hourly rates and averaged across regions

### Key Methods

Every scraper implements:

- `get_h200_prices()`: Main entry point that orchestrates scraping attempts
- `_validate_prices()`: Validates extracted prices are in reasonable ranges
- `_try_<method>()`: Individual scraping method attempts (API, page scraping, Selenium)
- `_extract_from_tables()`: Extract prices from HTML tables
- `_extract_from_text()`: Extract prices using regex patterns
- `_get_known_pricing()`: Return hardcoded fallback prices
- `_normalize_prices()`: Calculate per-GPU averages across regions
- `save_to_json()`: Save results in standardized JSON format

### Cloud Provider Specifics

**AWS (P5en.48xlarge instances)**
- 8 x H200 GPUs per instance
- ~$7.91/GPU/hr typical pricing
- Uses Vantage.sh as secondary source

**Azure (ND96isr_H200_v5 instances)**
- 8 x H200 GPUs per instance
- ~$12-13/GPU/hr typical pricing
- Has Azure Retail Prices API support

**GCP (A3-Ultra instances)**
- 8 x H200 GPUs per instance (a3-ultragpu-8g)
- ~$10.85/GPU/hr typical pricing
- May require JavaScript rendering

**Oracle Cloud (BM.GPU.H200.8 bare metal)**
- 8 x H200 GPUs per instance
- $10.00/GPU/hr flat pricing across regions
- Simplest pricing structure

**Specialized GPU Cloud Providers**

**HyperStack Cloud**
- ~$3.50/GPU/hr
- Requires Selenium for dynamic content
- More affordable than major cloud providers

**CoreWeave**
- ~$6.50/GPU/hr
- Standard web scraping works
- Mid-range pricing

**RunPod**
- ~$3.59/GPU/hr
- Requires Selenium for dynamic content
- Very competitive pricing

**Sesterce**
- ~$2.25/GPU/hr
- Requires Selenium for dynamic content
- Most affordable H200 pricing found
- Excellent value for cost-conscious workloads

**Genesis Cloud**
- H200 availability: Not confirmed
- Scraper created but no pricing data found

### Output Format

All scrapers produce JSON files with this structure:
```json
{
  "timestamp": "YYYY-MM-DD HH:MM:SS",
  "provider": "ProviderName",
  "providers": {
    "ProviderName": {
      "name": "Full Provider Name",
      "url": "pricing_url",
      "variants": {
        "InstanceType": {
          "gpu_model": "H200",
          "gpu_memory": "141GB",
          "price_per_hour": float,
          "currency": "USD",
          "availability": "on-demand"
        }
      }
    }
  },
  "notes": {
    "instance_type": "instance_name",
    "gpu_model": "NVIDIA H200",
    "gpu_memory": "141GB HBM3e",
    "gpu_count_per_instance": 8,
    "pricing_type": "On-Demand",
    "source": "url"
  }
}
```

## Adding Support for New Cloud Providers

When adding a new provider scraper:

1. Follow the existing class structure pattern
2. Implement all standard methods (`get_h200_prices`, `_validate_prices`, etc.)
3. Define provider-specific URLs and headers in `__init__`
4. Add multiple extraction methods with appropriate fallbacks
5. Set reasonable price validation ranges in `_validate_prices()`
6. Implement `_get_known_pricing()` with documented fallback prices
7. Ensure `save_to_json()` follows the standardized output format
8. Add extraction methods that handle both HTML tables and text patterns

## Modifying Scrapers

When updating scraper logic:

- **Price validation ranges**: Each provider has different typical pricing in `_validate_prices()`
- **Instance naming**: Different providers use different naming schemes (P5en, ND96isr, A3-Ultra, BM.GPU)
- **GPU counts**: All current instances have 8 GPUs, but verify for new instance types
- **Regex patterns**: Price extraction patterns in `_extract_from_text()` are provider-specific
- **Table structures**: HTML table parsing in `_extract_from_tables()` varies by provider
