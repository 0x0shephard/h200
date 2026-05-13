#!/usr/bin/env python3
"""Push provider-specific H200 prices to ByteStrike CuOracle on Sepolia."""

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Optional

from dotenv import load_dotenv

from cu_oracle_client import (
    DEFAULT_CU_ORACLE_ADDRESS,
    CuOracleClient,
    OracleUpdate,
    price_to_x18,
    x18_to_usd,
)

load_dotenv()

H200_PROVIDERS = {
    "ORACLE": {
        "asset_id": "0x5d5f627ba6daf1427a1559c3200cbe7ebf105d0df0ec1610c6b89d54a314bf51",
        "asset_symbol": "ORACLE_H200_HOUR",
        "market": "ORACLE-H200-PERPETUAL",
        "name": "Oracle Cloud H200",
    },
    "AWS": {
        "asset_id": "0xb377854a672b5274c99b24e7fe27d9661c60c8b697ca4f974208162655716b3e",
        "asset_symbol": "AWS_H200_HOUR",
        "market": "AWS-H200-PERPETUAL",
        "name": "AWS H200",
    },
    "COREWEAVE": {
        "asset_id": "0xa05f2ef65a5f11da36153346f35e9cdb554962e858a95c7f79075cd3a4c6ddfd",
        "asset_symbol": "COREWEAVE_H200_HOUR",
        "market": "COREWEAVE-H200-PERPETUAL",
        "name": "CoreWeave H200",
    },
    "GCP": {
        "asset_id": "0x0ba2d87db04ca970c41ab4334516ce12e74356d71ee96e228fb1ba5d519aaaf4",
        "asset_symbol": "GCP_H200_HOUR",
        "market": "GCP-H200-PERPETUAL",
        "name": "Google Cloud H200",
    },
    "AZURE": {
        "asset_id": "0x12b283ae476f0251b7a6eaa8d414a3260644e167d9253ef1e72d49e2c8291e61",
        "asset_symbol": "AZURE_H200_HOUR",
        "market": "AZURE-H200-PERPETUAL",
        "name": "Azure H200",
    },
}

INDEX_PROVIDER_MAP = {
    "AWS": "AWS",
    "Azure": "AZURE",
    "CoreWeave": "COREWEAVE",
    "Google Cloud": "GCP",
    "Oracle": "ORACLE",
}


def get_private_key() -> Optional[str]:
    return (
        os.getenv("ORACLE_UPDATER_PRIVATE_KEY")
        or os.getenv("PRIVATE_KEY")
        or os.getenv("WALLET_PRIVATE_KEY")
    )


def get_oracle_address() -> str:
    return (
        os.getenv("CU_ORACLE_ADDRESS")
        or os.getenv("BYTESTRIKE_CU_ORACLE_ADDRESS")
        or DEFAULT_CU_ORACLE_ADDRESS
    )


def read_prices_from_csv(path: str) -> Dict[str, float]:
    prices: Dict[str, float] = {}
    with open(path, "r", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    for row in rows:
        provider = (row.get("Provider") or row.get("provider") or "").upper().strip()
        price_raw = row.get("Price") or row.get("price")
        if not provider or price_raw is None:
            continue
        if provider not in H200_PROVIDERS:
            print(f"WARNING: Skipping unknown provider {provider}")
            continue
        prices[provider] = float(price_raw)

    if not prices:
        raise ValueError(f"No valid H200 provider prices found in {path}")
    return prices


def read_prices_from_index(path: str) -> Dict[str, float]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    details = data.get("hyperscaler_details", [])
    prices: Dict[str, float] = {}
    for detail in details:
        provider = INDEX_PROVIDER_MAP.get(detail.get("provider", ""))
        price = detail.get("effective_price")
        if provider and price is not None:
            prices[provider] = round(float(price), 4)

    if not prices:
        raise ValueError(f"No hyperscaler H200 provider prices found in {path}")
    return prices


def validate_prices(prices: Dict[str, float], allow_high: bool) -> None:
    for provider, price in prices.items():
        if provider not in H200_PROVIDERS:
            raise ValueError(f"Unknown H200 provider {provider}")
        if price <= 0:
            raise ValueError(f"{provider} price must be positive, got {price}")
        if price > 100 and not allow_high:
            raise ValueError(f"Refusing unusually high {provider} price ${price:.2f}/hr")


def display_current_prices(client: CuOracleClient) -> None:
    print("")
    print("=" * 70)
    print("CURRENT H200 PROVIDER ORACLE PRICES")
    print("=" * 70)
    print(f"{'Provider':<12} {'Market':<28} {'Price ($/hr)':<14} {'Commit Time'}")
    print("-" * 70)
    for provider, info in H200_PROVIDERS.items():
        asset_id = info["asset_id"]
        if not client.is_supported(asset_id):
            print(f"{provider:<12} {info['market']:<28} {'Unsupported':<14} N/A")
            continue
        price_x18, updated_at = client.get_latest_price(asset_id)
        print(
            f"{provider:<12} {info['market']:<28} "
            f"${x18_to_usd(price_x18):<13.4f} {updated_at}"
        )
    print("=" * 70)


def build_updates(prices: Dict[str, float]) -> list[OracleUpdate]:
    updates = []
    for provider, price in prices.items():
        info = H200_PROVIDERS[provider]
        updates.append(
            OracleUpdate(
                asset_key=info["asset_symbol"],
                asset_id=info["asset_id"],
                market=info["market"],
                price_usd=price,
            )
        )
    return updates


def log_update(prices: Dict[str, float], results) -> None:
    reveal_hashes = [result.reveal_hash for result in results]
    commit_hashes = [result.commit_hash for result in results]
    commitment_hashes = [result.commitment_hash for result in results]
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tx_hash": reveal_hashes[-1] if reveal_hashes else None,
        "reveal_tx_hashes": reveal_hashes,
        "commit_tx_hashes": commit_hashes,
        "commitment_hashes": commitment_hashes,
        "contract_address": get_oracle_address(),
        "network": "sepolia",
        "batch_update": len(results) > 1,
        "prices": {
            provider: {
                "price_usd": price,
                "price_scaled": price_to_x18(price),
                "asset_id": H200_PROVIDERS[provider]["asset_id"],
                "asset_symbol": H200_PROVIDERS[provider]["asset_symbol"],
                "market": H200_PROVIDERS[provider]["market"],
            }
            for provider, price in prices.items()
        },
    }

    log_file = "h200_price_update_log.json"
    logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as handle:
                logs = json.load(handle)
            if not isinstance(logs, list):
                logs = []
        except Exception:
            logs = []

    logs.append(entry)
    logs = logs[-100:]
    with open(log_file, "w", encoding="utf-8") as handle:
        json.dump(logs, handle, indent=2)
    print(f"Logged update to {log_file}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Push H200 provider-specific prices to ByteStrike CuOracle",
    )
    parser.add_argument("--show", action="store_true", help="Show current provider prices")
    parser.add_argument("--show-only", action="store_true", help="Alias for --show")
    parser.add_argument("--csv", type=str, help="CSV file with Provider,Price rows")
    parser.add_argument(
        "--from-index",
        type=str,
        nargs="?",
        const="h200_weighted_index.json",
        help="Read effective hyperscaler prices from weighted index JSON",
    )
    parser.add_argument("--provider", action="append", help="Provider to update")
    parser.add_argument("--price", type=float, action="append", help="Price for matching provider")
    parser.add_argument("--all", action="store_true", help="Update providers from individual flags")
    parser.add_argument("--oracle", type=float, help="Oracle Cloud H200 price")
    parser.add_argument("--aws", type=float, help="AWS H200 price")
    parser.add_argument("--coreweave", type=float, help="CoreWeave H200 price")
    parser.add_argument("--gcp", type=float, help="GCP H200 price")
    parser.add_argument("--azure", type=float, help="Azure H200 price")
    parser.add_argument("--no-verify", action="store_true", help="Skip post-reveal verification")
    parser.add_argument(
        "--reveal-wait-seconds",
        type=int,
        default=int(os.getenv("ORACLE_REVEAL_WAIT_SECONDS", "3")),
        help="Seconds to wait between commit and reveal",
    )
    parser.add_argument("--allow-high", action="store_true", help="Allow prices above $100/hr")
    return parser.parse_args()


def prices_from_args(args: argparse.Namespace) -> Dict[str, float]:
    if args.from_index:
        return read_prices_from_index(args.from_index)
    if args.csv:
        return read_prices_from_csv(args.csv)
    if args.all:
        prices: Dict[str, float] = {}
        if args.oracle is not None:
            prices["ORACLE"] = args.oracle
        if args.aws is not None:
            prices["AWS"] = args.aws
        if args.coreweave is not None:
            prices["COREWEAVE"] = args.coreweave
        if args.gcp is not None:
            prices["GCP"] = args.gcp
        if args.azure is not None:
            prices["AZURE"] = args.azure
        if not prices:
            raise ValueError("--all requires at least one provider price flag")
        return prices
    if args.provider and args.price:
        if len(args.provider) != len(args.price):
            raise ValueError("Number of --provider and --price arguments must match")
        return {
            provider.upper(): price
            for provider, price in zip(args.provider, args.price)
        }
    raise ValueError("Specify --show, --from-index, --csv, --provider/--price, or --all")


def main() -> None:
    args = parse_args()
    private_key = get_private_key()
    if not private_key:
        print("ERROR: Set ORACLE_UPDATER_PRIVATE_KEY, PRIVATE_KEY, or WALLET_PRIVATE_KEY")
        sys.exit(1)

    try:
        client = CuOracleClient(
            rpc_url=os.getenv("SEPOLIA_RPC_URL"),
            private_key=private_key,
            oracle_address=get_oracle_address(),
        )
        client.print_connection_summary()
        display_current_prices(client)

        if args.show or args.show_only:
            return

        prices = prices_from_args(args)
        validate_prices(prices, args.allow_high)

        print("")
        print("=" * 70)
        print("PREPARED H200 PROVIDER CUORACLE UPDATES")
        print("=" * 70)
        for provider, price in prices.items():
            info = H200_PROVIDERS[provider]
            current_x18, _ = client.get_latest_price(info["asset_id"])
            current = x18_to_usd(current_x18)
            change_pct = ((price - current) / current * 100) if current else 0
            print(
                f"  {info['asset_symbol']} ({info['market']}): "
                f"${current:.4f} -> ${price:.4f}/hr ({change_pct:+.2f}%)"
            )
        print("=" * 70)

        results = client.commit_and_reveal(
            build_updates(prices),
            reveal_wait_seconds=args.reveal_wait_seconds,
            verify=not args.no_verify,
        )
        log_update(prices, results)

        print("")
        print("=" * 70)
        print("SUCCESS! H200 PROVIDER PRICES UPDATED ON-CHAIN")
        print("=" * 70)
        for result in results:
            print(f"  {result.update.asset_key}: {result.reveal_hash}")
        print("=" * 70)
    except Exception as exc:
        print("")
        print("=" * 70)
        print("ERROR: H200 PROVIDER CUORACLE UPDATE FAILED")
        print("=" * 70)
        print(f"  {exc}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
