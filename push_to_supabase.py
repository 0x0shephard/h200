#!/usr/bin/env python3
"""
Push H200 Weighted Index to Supabase

This script reads the H200 weighted index from h200_weighted_index.json
and pushes it to the Supabase h200_index_prices table.

Usage:
    python push_to_supabase.py

Environment Variables Required (set in .env file):
    SUPABASE_URL - Your Supabase project URL
    SUPABASE_SERVICE_KEY - Your Supabase service role key (for write access)

Contingency Plan:
    - Price validation: New price must be within ±25% of the average of last 2 prices
    - If validation fails, the push is rejected to prevent bad data
    - Initial pushes (< 2 records) are allowed without validation
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not required if env vars are set directly


def load_index_data(filepath: str = "h200_weighted_index.json") -> Optional[Dict]:
    """Load H200 weighted index data from JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] {filepath} not found!")
        print(f"   Please run calculate_h200_index.py first to generate the index.")
        return None
    except json.JSONDecodeError as e:
        print(f"[ERROR] Error parsing JSON: {e}")
        return None


def validate_price(supabase: 'Client', new_price: float, tolerance: float = 0.25) -> bool:
    """
    Validate that the new price is within acceptable range of historical prices.
    
    CONTINGENCY PLAN:
    - Compare new price against average of last 2 prices
    - Reject if deviation exceeds ±25% (configurable tolerance)
    - Allow initial pushes when < 2 historical records exist
    
    Args:
        supabase: Supabase client
        new_price: New price to validate
        tolerance: Acceptable deviation (default 25% = 0.25)
    
    Returns:
        True if price is valid, False otherwise
    """
    try:
        # Get last 2 prices from Supabase
        response = supabase.table('h200_index_prices')\
            .select('index_price')\
            .order('created_at', desc=True)\
            .limit(2)\
            .execute()
        
        if not response.data or len(response.data) < 2:
            print(f"\n[WARNING] Not enough historical data for validation (found {len(response.data) if response.data else 0} records)")
            print(f"   Allowing push for initial data collection...")
            return True
        
        # Calculate average of last 2 prices
        last_prices = [float(record['index_price']) for record in response.data]
        avg_price = sum(last_prices) / len(last_prices)
        
        # Calculate acceptable range (±25%)
        lower_bound = avg_price * (1 - tolerance)
        upper_bound = avg_price * (1 + tolerance)
        
        # Check if new price is within range
        is_valid = lower_bound <= new_price <= upper_bound
        
        # Display validation info
        print(f"\n[VALIDATION] Price Validation Check:")
        print(f"   Last 2 Prices: ${last_prices[0]:.2f}, ${last_prices[1]:.2f}")
        print(f"   Average: ${avg_price:.2f}")
        print(f"   Acceptable Range: ${lower_bound:.2f} - ${upper_bound:.2f} (+/-{tolerance*100:.0f}%)")
        print(f"   New Price: ${new_price:.2f}")
        
        if is_valid:
            deviation_pct = ((new_price - avg_price) / avg_price) * 100
            print(f"   [OK] VALID - Deviation: {deviation_pct:+.1f}%")
        else:
            deviation_pct = ((new_price - avg_price) / avg_price) * 100
            print(f"   [FAIL] INVALID - Deviation: {deviation_pct:+.1f}% (exceeds +/-{tolerance*100:.0f}%)")
        
        return is_valid
        
    except Exception as e:
        print(f"\n[WARNING] Price validation error: {e}")
        print(f"   Allowing push anyway...")
        return True  # Allow push if validation fails (don't block on errors)


def push_to_supabase(index_data: Dict) -> bool:
    """Push H200 index data and hyperscaler prices to Supabase with price validation"""
    
    # Get Supabase credentials from environment
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_key:
        print("[ERROR] Supabase credentials not found!")
        print("   Please set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables.")
        print("\n   Example:")
        print("   export SUPABASE_URL='https://your-project.supabase.co'")
        print("   export SUPABASE_SERVICE_KEY='your-service-role-key'")
        return False
    
    try:
        from supabase import create_client, Client
    except ImportError:
        print("[ERROR] supabase-py library not installed!")
        print("   Install it with: pip install supabase")
        return False
    
    try:
        # Initialize Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Get new price
        new_price = index_data.get("final_index_price")
        
        # Validate price against historical data
        if not validate_price(supabase, new_price):
            print("\n[ERROR] Price validation failed - not pushing to Supabase")
            print("   The new price is outside the acceptable range.")
            print("   This may indicate a scraping error or market anomaly.")
            return False
        
        # Prepare data for insertion
        insert_data = {
            "timestamp": index_data.get("timestamp"),
            "index_price": new_price,
            "hyperscaler_component": index_data.get("hyperscaler_component"),
            "neocloud_component": index_data.get("neocloud_component"),
            "hyperscaler_count": index_data.get("hyperscaler_count"),
            "neocloud_count": index_data.get("neocloud_count"),
            "metadata": {
                "weights": index_data.get("weights", {}),
                "hyperscaler_details": index_data.get("hyperscaler_details", []),
                "neocloud_details": index_data.get("neocloud_details", []),
                "base_config": index_data.get("base_config", {})
            }
        }
        
        print(f"\n[PUSH] Pushing H200 Index to Supabase...")
        print(f"   Index Price: ${insert_data['index_price']:.2f}/hr")
        print(f"   Hyperscaler Component: ${insert_data['hyperscaler_component']:.4f}")
        print(f"   Neocloud Component: ${insert_data['neocloud_component']:.4f}")
        print(f"   Timestamp: {insert_data['timestamp']}")
        
        # Insert main index into Supabase
        response = supabase.table('h200_index_prices').insert(insert_data).execute()
        
        if response.data:
            index_id = response.data[0]['id']
            print(f"\n[SUCCESS] Successfully pushed index to Supabase!")
            print(f"   Record ID: {index_id}")
            
            # Push individual hyperscaler prices
            push_hyperscaler_prices(supabase, index_data, index_id)
            
            return True
        else:
            print(f"\n[ERROR] No data returned from Supabase")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] Error pushing to Supabase: {e}")
        import traceback
        traceback.print_exc()
        return False


def push_hyperscaler_prices(supabase: 'Client', index_data: Dict, index_id: int) -> bool:
    """Push individual H200 hyperscaler prices to h200_provider_prices table"""
    
    try:
        timestamp = index_data.get("timestamp")
        hyperscaler_details = index_data.get("hyperscaler_details", [])
        
        provider_records = []
        
        print(f"\n[PUSH] Pushing H200 hyperscaler prices...")
        print(f"\n   📊 Hyperscalers:")
        
        for detail in hyperscaler_details:
            provider_name = detail.get("provider")
            
            record = {
                "index_id": index_id,
                "timestamp": timestamp,
                "provider_name": provider_name,
                "provider_type": "hyperscaler",
                "original_price": round(detail.get("original_price", 0), 4),
                "effective_price": round(detail.get("effective_price", 0), 4),
                "discount_rate": round(detail.get("discount_rate", 0), 4),
                "relative_weight": round(detail.get("relative_weight", 0), 4),
                "absolute_weight": round(detail.get("absolute_weight", 0), 4),
                "weighted_contribution": round(detail.get("weighted_contribution", 0), 4),
            }
            provider_records.append(record)
            print(f"      • {provider_name}: ${record['effective_price']:.2f}/hr (discounted from ${record['original_price']:.2f})")
        
        # Insert hyperscaler records
        if provider_records:
            response = supabase.table('h200_provider_prices').insert(provider_records).execute()
            
            if response.data:
                print(f"\n   [OK] Pushed {len(response.data)} hyperscaler prices to Supabase!")
                return True
            else:
                print(f"\n   [WARNING] No data returned for provider prices")
                return False
        else:
            print(f"\n   [WARNING] No provider records to push")
            return False
            
    except Exception as e:
        print(f"\n   [WARNING] Error pushing provider prices: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_push(supabase_url: str, supabase_key: str) -> bool:
    """Verify the most recent entry in Supabase"""
    try:
        from supabase import create_client
        
        supabase = create_client(supabase_url, supabase_key)
        
        # Get the most recent entry
        response = supabase.table('h200_index_prices')\
            .select('*')\
            .order('created_at', desc=True)\
            .limit(1)\
            .execute()
        
        if response.data:
            latest = response.data[0]
            print(f"\n[VERIFY] Latest Entry in Supabase:")
            print(f"   ID: {latest['id']}")
            print(f"   Index Price: ${latest['index_price']}/hr")
            print(f"   Timestamp: {latest['timestamp']}")
            print(f"   Created At: {latest['created_at']}")
            return True
        else:
            print(f"\n[WARNING] No entries found in h200_index_prices table")
            return False
            
    except Exception as e:
        print(f"\n[WARNING] Could not verify: {e}")
        return False


def main():
    """Main function"""
    print("=" * 60)
    print("H200 Index -> Supabase Uploader")
    print("=" * 60)
    
    # Load index data
    print("\n[LOAD] Loading H200 weighted index data...")
    index_data = load_index_data()
    
    if not index_data:
        sys.exit(1)
    
    print(f"   Loaded index: ${index_data['final_index_price']:.2f}/hr")
    print(f"   Hyperscalers: {index_data.get('hyperscaler_count', 'N/A')}")
    print(f"   Neoclouds: {index_data.get('neocloud_count', 'N/A')}")
    
    # Push to Supabase
    success = push_to_supabase(index_data)
    
    if not success:
        sys.exit(1)
    
    # Verify
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if supabase_url and supabase_key:
        verify_push(supabase_url, supabase_key)
    
    print("\n" + "=" * 60)
    print("[DONE] H200 index successfully uploaded to Supabase!")
    print("=" * 60)


if __name__ == "__main__":
    main()
