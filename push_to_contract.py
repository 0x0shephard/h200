#!/usr/bin/env python3
"""Push the aggregate H200 index price to ByteStrike CuOracle on Sepolia."""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv

from cu_oracle_client import (
    DEFAULT_CU_ORACLE_ADDRESS,
    CuOracleClient,
    OracleUpdate,
    price_to_x18,
    x18_to_usd,
)

load_dotenv()

H200_ASSET_ID = os.getenv(
    "H200_ASSET_ID",
    "0x8340d453df40afe28f3d35784237cd4d87407b4bdf574a1f10a1fbabdc417b83",
)
H200_MARKET = "H200-PERP-V2"
H200_ASSET_KEY = "H200"


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


def load_index_price(path: str) -> float:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    price = data.get("final_index_price")
    if price is None:
        raise ValueError(f"{path} does not contain final_index_price")
    return float(price)


def log_update(price_usd: float, result) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "asset": H200_ASSET_KEY,
        "market": H200_MARKET,
        "asset_id": H200_ASSET_ID,
        "price_usd": price_usd,
        "price_x18": price_to_x18(price_usd),
        "commit_tx_hash": result.commit_hash,
        "commitment_hash": result.commitment_hash,
        "tx_hash": result.reveal_hash,
        "commit_timestamp": result.updated_at,
        "contract_address": get_oracle_address(),
        "network": "sepolia",
    }

    log_file = "h200_oracle_update_log.json"
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
        description="Push aggregate H200 index price to ByteStrike CuOracle",
    )
    parser.add_argument(
        "positional_price",
        nargs="?",
        type=float,
        help="H200 hourly price in USD. Kept for existing workflow compatibility.",
    )
    parser.add_argument("--price", type=float, help="H200 hourly price in USD")
    parser.add_argument(
        "--index-file",
        default="h200_weighted_index.json",
        help="Weighted index JSON to read when no price is supplied",
    )
    parser.add_argument("--show-only", action="store_true", help="Only show current oracle state")
    parser.add_argument("--no-verify", action="store_true", help="Skip post-reveal verification")
    parser.add_argument(
        "--reveal-wait-seconds",
        type=int,
        default=int(os.getenv("ORACLE_REVEAL_WAIT_SECONDS", "3")),
        help="Seconds to wait between commit and reveal",
    )
    parser.add_argument(
        "--allow-high",
        action="store_true",
        help="Allow prices above $100/hr without aborting",
    )
    return parser.parse_args()


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

        if not client.is_supported(H200_ASSET_ID):
            raise RuntimeError(f"{H200_ASSET_KEY} asset is not supported: {H200_ASSET_ID}")

        current_price_x18, updated_at = client.get_latest_price(H200_ASSET_ID)
        print("Current H200 index oracle price:")
        print(f"  {H200_ASSET_KEY} ({H200_MARKET}): ${x18_to_usd(current_price_x18):.6f}/hr")
        print(f"  Commit timestamp: {updated_at}")

        if args.show_only:
            return

        price_usd = (
            args.price
            if args.price is not None
            else args.positional_price
            if args.positional_price is not None
            else load_index_price(args.index_file)
        )

        if price_usd <= 0:
            raise ValueError(f"Price must be positive, got {price_usd}")
        if price_usd > 100 and not args.allow_high:
            raise ValueError(f"Refusing unusually high H200 price ${price_usd:.2f}/hr")

        current_usd = x18_to_usd(current_price_x18)
        change_pct = ((price_usd - current_usd) / current_usd * 100) if current_usd else 0
        print("Prepared CuOracle update:")
        print(
            f"  {H200_ASSET_KEY} ({H200_MARKET}): "
            f"${current_usd:.6f} -> ${price_usd:.6f}/hr ({change_pct:+.2f}%)"
        )

        updates = [
            OracleUpdate(
                asset_key=H200_ASSET_KEY,
                market=H200_MARKET,
                asset_id=H200_ASSET_ID,
                price_usd=price_usd,
            )
        ]
        results = client.commit_and_reveal(
            updates,
            reveal_wait_seconds=args.reveal_wait_seconds,
            verify=not args.no_verify,
        )
        log_update(price_usd, results[0])

        print("=" * 70)
        print("SUCCESS! H200 INDEX PRICE UPDATED ON-CHAIN")
        print("=" * 70)
        print(f"  Reveal transaction: {results[0].reveal_hash}")
        print(f"  Etherscan: https://sepolia.etherscan.io/tx/{results[0].reveal_hash}")
    except Exception as exc:
        print("=" * 70)
        print("ERROR: H200 CUORACLE UPDATE FAILED")
        print("=" * 70)
        print(f"  {exc}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
