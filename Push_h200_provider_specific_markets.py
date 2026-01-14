#!/usr/bin/env python3
"""H200 GPU Provider Price Updater for MultiAssetOracle.

This script updates index prices for H200 GPU rental rates across multiple
cloud providers (Oracle, AWS, CoreWeave, GCP, Azure) on the MultiAssetOracle contract.
"""

import csv
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Sequence, Tuple

from dotenv import load_dotenv
from eth_account import Account
from web3 import Web3

load_dotenv()

# --- Configuration ---
SEPOLIA_RPC_URL = os.getenv("SEPOLIA_RPC_URL", "https://rpc.sepolia.org")
PRIVATE_KEY = os.getenv("ORACLE_UPDATER_PRIVATE_KEY") or os.getenv("PRIVATE_KEY")
MULTI_ASSET_ORACLE_ADDRESS = os.getenv(
    "MULTI_ASSET_ORACLE_ADDRESS",
    "0xB44d652354d12Ac56b83112c6ece1fa2ccEfc683",
)
PRICE_DECIMALS = 18

# --- H200 Provider Asset IDs ---
# These are keccak256 hashes of the provider identifiers
H200_PROVIDERS = {
    "ORACLE": {
        "asset_id": "0x5d5f627ba6daf1427a1559c3200cbe7ebf105d0df0ec1610c6b89d54a314bf51",
        "name": "Oracle Cloud H200",
        "default_price": 2.92,
    },
    "AWS": {
        "asset_id": "0xb377854a672b5274c99b24e7fe27d9661c60c8b697ca4f974208162655716b3e",
        "name": "AWS H200",
        "default_price": 2.65,
    },
    "COREWEAVE": {
        "asset_id": "0xa05f2ef65a5f11da36153346f35e9cdb554962e858a95c7f79075cd3a4c6ddfd",
        "name": "CoreWeave H200",
        "default_price": 2.57,
    },
    "GCP": {
        "asset_id": "0x0ba2d87db04ca970c41ab4334516ce12e74356d71ee96e228fb1ba5d519aaaf4",
        "name": "Google Cloud H200",
        "default_price": 4.55,
    },
    "AZURE": {
        "asset_id": "0x12b283ae476f0251b7a6eaa8d414a3260644e167d9253ef1e72d49e2c8291e61",
        "name": "Azure H200",
        "default_price": 5.05,
    },
}

# --- MultiAssetOracle ABI ---
MULTI_ASSET_ORACLE_ABI: Sequence[dict] = [
    {
        "type": "function",
        "name": "updatePrice",
        "inputs": [
            {"name": "assetId", "type": "bytes32", "internalType": "bytes32"},
            {"name": "newPrice", "type": "uint256", "internalType": "uint256"},
        ],
        "outputs": [],
        "stateMutability": "nonpayable",
    },
    {
        "type": "function",
        "name": "batchUpdatePrices",
        "inputs": [
            {"name": "assetIds", "type": "bytes32[]", "internalType": "bytes32[]"},
            {"name": "newPrices", "type": "uint256[]", "internalType": "uint256[]"},
        ],
        "outputs": [],
        "stateMutability": "nonpayable",
    },
    {
        "type": "function",
        "name": "getPrice",
        "inputs": [
            {"name": "assetId", "type": "bytes32", "internalType": "bytes32"},
        ],
        "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}],
        "stateMutability": "view",
    },
    {
        "type": "function",
        "name": "getPriceData",
        "inputs": [
            {"name": "assetId", "type": "bytes32", "internalType": "bytes32"},
        ],
        "outputs": [
            {"name": "price", "type": "uint256", "internalType": "uint256"},
            {"name": "updatedAt", "type": "uint256", "internalType": "uint256"},
        ],
        "stateMutability": "view",
    },
    {
        "type": "function",
        "name": "isAssetRegistered",
        "inputs": [
            {"name": "assetId", "type": "bytes32", "internalType": "bytes32"},
        ],
        "outputs": [{"name": "", "type": "bool", "internalType": "bool"}],
        "stateMutability": "view",
    },
    {
        "type": "function",
        "name": "owner",
        "inputs": [],
        "outputs": [{"name": "", "type": "address", "internalType": "address"}],
        "stateMutability": "view",
    },
    {
        "type": "event",
        "name": "PriceUpdated",
        "inputs": [
            {"name": "assetId", "type": "bytes32", "indexed": True, "internalType": "bytes32"},
            {"name": "newPrice", "type": "uint256", "indexed": True, "internalType": "uint256"},
            {"name": "timestamp", "type": "uint256", "indexed": False, "internalType": "uint256"},
        ],
        "anonymous": False,
    },
]


@dataclass
class PriceData:
    """Represents price data for an asset."""
    provider: str
    asset_id: str
    price_raw: int
    updated_at: int

    @property
    def price_usd(self) -> float:
        return self.price_raw / 10**PRICE_DECIMALS

    @property
    def updated_at_str(self) -> str:
        if self.updated_at == 0:
            return "Never"
        return datetime.fromtimestamp(self.updated_at, tz=timezone.utc).isoformat()


class H200PriceUpdater:
    """Update H200 GPU rental prices on the MultiAssetOracle contract."""

    def __init__(self, rpc_url: str, private_key: str, contract_address: str):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to RPC: {rpc_url}")

        self.account = Account.from_key(private_key)
        self.address = self.account.address
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=MULTI_ASSET_ORACLE_ABI,
        )
        self.contract_address = contract_address

        # Display connection info
        balance_eth = self.w3.from_wei(self.w3.eth.get_balance(self.address), "ether")
        print("=" * 70)
        print("H200 PROVIDER PRICE UPDATER")
        print("=" * 70)
        print(f"  Network:          Sepolia (Chain ID: {self.w3.eth.chain_id})")
        print(f"  Latest Block:     {self.w3.eth.block_number}")
        print(f"  Updater Address:  {self.address}")
        print(f"  Balance:          {balance_eth:.4f} ETH")
        print(f"  Oracle Contract:  {contract_address}")
        print("=" * 70)

    def _build_dynamic_fee(self) -> Tuple[int, int]:
        """Build EIP-1559 fee parameters."""
        base_fee = self.w3.eth.gas_price
        max_priority = self.w3.to_wei(1, "gwei")
        max_fee = max(base_fee * 2, max_priority * 2)
        return max_fee, max_priority

    def _send_transaction(self, func, gas_limit: int) -> Tuple[str, dict]:
        """Build, sign, and send a transaction."""
        max_fee, max_priority = self._build_dynamic_fee()
        tx = func.build_transaction({
            "from": self.address,
            "nonce": self.w3.eth.get_transaction_count(self.address),
            "gas": gas_limit,
            "maxFeePerGas": max_fee,
            "maxPriorityFeePerGas": max_priority,
            "chainId": self.w3.eth.chain_id,
        })
        signed = self.account.sign_transaction(tx)

        if hasattr(signed, "raw_transaction"):
            raw_tx = signed.raw_transaction
        elif hasattr(signed, "rawTransaction"):
            raw_tx = signed.rawTransaction
        else:
            raw_tx = signed

        tx_hash = self.w3.eth.send_raw_transaction(raw_tx)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
        return tx_hash.hex(), dict(receipt)

    def get_current_prices(self) -> Dict[str, PriceData]:
        """Get current prices for all H200 providers."""
        prices = {}
        for provider, info in H200_PROVIDERS.items():
            asset_id = info["asset_id"]
            try:
                is_registered = self.contract.functions.isAssetRegistered(asset_id).call()
                if is_registered:
                    price_raw, updated_at = self.contract.functions.getPriceData(asset_id).call()
                else:
                    price_raw, updated_at = 0, 0
            except Exception:
                price_raw, updated_at = 0, 0

            prices[provider] = PriceData(
                provider=provider,
                asset_id=asset_id,
                price_raw=price_raw,
                updated_at=updated_at,
            )
        return prices

    def display_current_prices(self) -> None:
        """Display current oracle prices for all providers."""
        prices = self.get_current_prices()
        print("\n" + "=" * 70)
        print("CURRENT ORACLE PRICES")
        print("=" * 70)
        print(f"{'Provider':<12} {'Price ($/hr)':<14} {'Last Updated':<30}")
        print("-" * 70)
        for provider, data in prices.items():
            if data.price_raw > 0:
                print(f"{provider:<12} ${data.price_usd:<13.4f} {data.updated_at_str}")
            else:
                print(f"{provider:<12} {'Not Set':<14} {'N/A'}")
        print("=" * 70)

    def update_single_price(self, provider: str, price_usd: float) -> str:
        """Update price for a single provider."""
        provider = provider.upper()
        if provider not in H200_PROVIDERS:
            raise ValueError(f"Unknown provider: {provider}. Valid: {list(H200_PROVIDERS.keys())}")

        info = H200_PROVIDERS[provider]
        asset_id = info["asset_id"]
        price_scaled = int(price_usd * 10**PRICE_DECIMALS)

        print(f"\nUpdating {info['name']}...")
        print(f"  Asset ID: {asset_id}")
        print(f"  New Price: ${price_usd:.4f}/hr")

        tx_hash, receipt = self._send_transaction(
            self.contract.functions.updatePrice(asset_id, price_scaled),
            gas_limit=100_000,
        )

        print(f"  TX Hash: {tx_hash}")
        print(f"  Gas Used: {receipt['gasUsed']:,}")
        print(f"  Status: {'Success' if receipt['status'] == 1 else 'Failed'}")

        return tx_hash

    def batch_update_prices(self, prices: Dict[str, float]) -> str:
        """Batch update prices for multiple providers in a single transaction."""
        asset_ids = []
        new_prices = []

        print("\n" + "=" * 70)
        print("BATCH PRICE UPDATE")
        print("=" * 70)

        for provider, price_usd in prices.items():
            provider = provider.upper()
            if provider not in H200_PROVIDERS:
                raise ValueError(f"Unknown provider: {provider}")

            info = H200_PROVIDERS[provider]
            asset_ids.append(info["asset_id"])
            new_prices.append(int(price_usd * 10**PRICE_DECIMALS))
            print(f"  {provider:<12} -> ${price_usd:.4f}/hr")

        print("-" * 70)
        print(f"  Total providers: {len(asset_ids)}")
        print("  Sending transaction...")

        tx_hash, receipt = self._send_transaction(
            self.contract.functions.batchUpdatePrices(asset_ids, new_prices),
            gas_limit=50_000 + (len(asset_ids) * 30_000),
        )

        print(f"  TX Hash: {tx_hash}")
        print(f"  Gas Used: {receipt['gasUsed']:,}")
        print(f"  Status: {'Success' if receipt['status'] == 1 else 'Failed'}")
        print("=" * 70)

        return tx_hash

    def read_prices_from_csv(self, csv_file: str) -> Optional[Dict[str, float]]:
        """Read H200 provider prices from a CSV file.

        Expected CSV format:
        Provider,Price
        ORACLE,2.92
        AWS,2.65
        COREWEAVE,2.57
        GCP,4.55
        AZURE,5.05
        """
        try:
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except FileNotFoundError:
            print(f"ERROR: CSV file not found: {csv_file}")
            return None
        except Exception as exc:
            print(f"ERROR: Failed to read CSV: {exc}")
            return None

        if not rows:
            print("ERROR: CSV file is empty")
            return None

        prices = {}
        for row in rows:
            provider = row.get("Provider", "").upper().strip()
            price_str = row.get("Price", "").strip()

            if not provider or not price_str:
                continue

            if provider not in H200_PROVIDERS:
                print(f"  WARNING: Skipping unknown provider: {provider}")
                continue

            try:
                prices[provider] = float(price_str)
            except ValueError:
                print(f"  WARNING: Invalid price for {provider}: {price_str}")
                continue

        if not prices:
            print("ERROR: No valid prices found in CSV")
            return None

        print("\n" + "=" * 70)
        print(f"PRICES FROM CSV: {csv_file}")
        print("=" * 70)
        for provider, price in prices.items():
            print(f"  {provider:<12} ${price:.4f}/hr")
        print("=" * 70)

        return prices

    def read_prices_from_index(self, index_file: str = "h200_weighted_index.json") -> Optional[Dict[str, float]]:
        """Read H200 provider prices from the weighted index JSON file.

        Extracts effective_price from hyperscaler_details for each provider.
        Maps provider names from index format to our format:
        - "Google Cloud" -> "GCP"
        - "Oracle" -> "ORACLE"
        - etc.
        """
        # Mapping from index provider names to our provider keys
        provider_name_map = {
            "AWS": "AWS",
            "Azure": "AZURE",
            "CoreWeave": "COREWEAVE",
            "Google Cloud": "GCP",
            "Oracle": "ORACLE",
        }

        try:
            with open(index_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"ERROR: Index file not found: {index_file}")
            return None
        except json.JSONDecodeError as exc:
            print(f"ERROR: Invalid JSON in index file: {exc}")
            return None
        except Exception as exc:
            print(f"ERROR: Failed to read index file: {exc}")
            return None

        hyperscaler_details = data.get("hyperscaler_details", [])
        if not hyperscaler_details:
            print("ERROR: No hyperscaler_details found in index file")
            return None

        prices = {}
        for detail in hyperscaler_details:
            index_provider = detail.get("provider", "")
            effective_price = detail.get("effective_price")

            if not index_provider or effective_price is None:
                continue

            # Map to our provider key
            our_provider = provider_name_map.get(index_provider)
            if our_provider and our_provider in H200_PROVIDERS:
                prices[our_provider] = round(effective_price, 4)

        if not prices:
            print("ERROR: No valid prices extracted from index file")
            return None

        print("\n" + "=" * 70)
        print(f"PRICES FROM INDEX: {index_file}")
        print("=" * 70)
        print(f"  Index Timestamp: {data.get('timestamp', 'N/A')}")
        print(f"  Final Index Price: ${data.get('final_index_price', 'N/A')}/hr")
        print("-" * 70)
        for provider, price in sorted(prices.items()):
            print(f"  {provider:<12} ${price:.4f}/hr (effective/blended)")
        print("=" * 70)

        return prices

    def log_update(
        self,
        prices: Dict[str, float],
        tx_hash: str,
        block_number: int,
        batch: bool = False,
    ) -> None:
        """Log the update to a JSON file."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tx_hash": tx_hash,
            "block_number": block_number,
            "contract_address": self.contract_address,
            "network": "sepolia",
            "updater_address": self.address,
            "batch_update": batch,
            "prices": {
                provider: {
                    "price_usd": price,
                    "price_scaled": int(price * 10**PRICE_DECIMALS),
                    "asset_id": H200_PROVIDERS[provider]["asset_id"],
                }
                for provider, price in prices.items()
            },
        }

        log_file = "h200_price_update_log.json"
        logs = []

        if os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    logs = json.load(f)
                if not isinstance(logs, list):
                    logs = []
            except Exception:
                logs = []

        logs.append(log_entry)
        logs = logs[-100:]  # Keep last 100 entries

        try:
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=2)
            print(f"Logged to {log_file}")
        except Exception as exc:
            print(f"WARNING: Failed to write log: {exc}")


def main() -> None:
    """Main entry point for H200 provider price updates."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Update H200 GPU provider prices on MultiAssetOracle",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show current prices
  python Push_h200_provider_specific_markets.py --show

  # Update all 5 providers from weighted index (recommended for pipeline)
  python Push_h200_provider_specific_markets.py --from-index
  python Push_h200_provider_specific_markets.py --from-index h200_weighted_index.json

  # Update single provider
  python Push_h200_provider_specific_markets.py --provider AWS --price 2.75

  # Update multiple providers
  python Push_h200_provider_specific_markets.py --provider AWS --price 2.75 --provider GCP --price 4.60

  # Batch update all providers from CSV
  python Push_h200_provider_specific_markets.py --csv h200_prices.csv

  # Update all providers with manual prices
  python Push_h200_provider_specific_markets.py --all \\
    --oracle 2.92 --aws 2.65 --coreweave 2.57 --gcp 4.55 --azure 5.05

Providers: ORACLE, AWS, COREWEAVE, GCP, AZURE

Environment Variables:
  SEPOLIA_RPC_URL              Ethereum RPC endpoint
  PRIVATE_KEY                  Wallet private key for signing
  MULTI_ASSET_ORACLE_ADDRESS   Oracle contract address
        """,
    )

    parser.add_argument("--show", action="store_true", help="Show current oracle prices")
    parser.add_argument("--csv", type=str, help="CSV file with provider prices")
    parser.add_argument(
        "--from-index",
        type=str,
        nargs="?",
        const="h200_weighted_index.json",
        help="Read prices from weighted index JSON file (default: h200_weighted_index.json)",
    )
    parser.add_argument(
        "--provider",
        type=str,
        action="append",
        help="Provider to update (can be repeated)",
    )
    parser.add_argument(
        "--price",
        type=float,
        action="append",
        help="Price for corresponding provider (can be repeated)",
    )
    parser.add_argument("--all", action="store_true", help="Update all providers")
    parser.add_argument("--oracle", type=float, help="Oracle Cloud H200 price")
    parser.add_argument("--aws", type=float, help="AWS H200 price")
    parser.add_argument("--coreweave", type=float, help="CoreWeave H200 price")
    parser.add_argument("--gcp", type=float, help="GCP H200 price")
    parser.add_argument("--azure", type=float, help="Azure H200 price")

    args = parser.parse_args()

    # Validate private key
    if not PRIVATE_KEY:
        print("ERROR: Private key not configured")
        print("Set PRIVATE_KEY or ORACLE_UPDATER_PRIVATE_KEY environment variable")
        sys.exit(1)

    # Initialize updater
    try:
        updater = H200PriceUpdater(
            rpc_url=SEPOLIA_RPC_URL,
            private_key=PRIVATE_KEY,
            contract_address=MULTI_ASSET_ORACLE_ADDRESS,
        )
    except ConnectionError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    # Show current prices
    if args.show:
        updater.display_current_prices()
        sys.exit(0)

    # Determine prices to update
    prices_to_update: Dict[str, float] = {}

    if args.from_index:
        prices_to_update = updater.read_prices_from_index(args.from_index) or {}
        if not prices_to_update:
            sys.exit(1)

    elif args.csv:
        prices_to_update = updater.read_prices_from_csv(args.csv) or {}
        if not prices_to_update:
            sys.exit(1)

    elif args.all:
        # Collect all provider prices from individual flags
        if args.oracle:
            prices_to_update["ORACLE"] = args.oracle
        if args.aws:
            prices_to_update["AWS"] = args.aws
        if args.coreweave:
            prices_to_update["COREWEAVE"] = args.coreweave
        if args.gcp:
            prices_to_update["GCP"] = args.gcp
        if args.azure:
            prices_to_update["AZURE"] = args.azure

        if not prices_to_update:
            print("ERROR: --all requires at least one provider price")
            print("Use: --oracle, --aws, --coreweave, --gcp, --azure")
            sys.exit(1)

    elif args.provider and args.price:
        if len(args.provider) != len(args.price):
            print("ERROR: Number of --provider and --price arguments must match")
            sys.exit(1)

        for provider, price in zip(args.provider, args.price):
            prices_to_update[provider.upper()] = price

    else:
        print("ERROR: Specify --show, --from-index, --csv, --provider/--price, or --all with prices")
        parser.print_help()
        sys.exit(1)

    # Validate prices
    for provider, price in prices_to_update.items():
        if price <= 0:
            print(f"ERROR: Price must be positive for {provider}: {price}")
            sys.exit(1)
        if price > 100:
            print(f"WARNING: Price for {provider} seems high: ${price:.2f}/hr")

    # Display current prices before update
    updater.display_current_prices()

    # Execute update
    try:
        if len(prices_to_update) == 1:
            provider, price = list(prices_to_update.items())[0]
            tx_hash = updater.update_single_price(provider, price)
        else:
            tx_hash = updater.batch_update_prices(prices_to_update)

        # Log and display result
        updater.log_update(
            prices_to_update,
            tx_hash,
            updater.w3.eth.block_number,
            batch=len(prices_to_update) > 1,
        )

        print("\n" + "=" * 70)
        print("SUCCESS! PRICES UPDATED ON-CHAIN")
        print("=" * 70)
        print(f"  Transaction: {tx_hash}")
        print(f"  Etherscan:   https://sepolia.etherscan.io/tx/{tx_hash}")
        print("=" * 70)

        # Display updated prices
        updater.display_current_prices()

    except Exception as exc:
        print(f"\nERROR: Update failed: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
