import logging
import asyncio
import sys
import csv
from pathlib import Path
from typing import Any
import httpx

from config import config
from client import HumbleClient
from models import OrderDetails, OrderKey


def setup_logging() -> logging.Logger:
    """Configures logging to stdout"""
    
    sys.stdout.reconfigure(encoding='utf-8')  # Ensure UTF-8 encoding for console output # type: ignore
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            # TODO: Add file handler (Output to "output" folder with timestamped log files)
        ]
    )
    return logging.getLogger(__name__)


async def async_main() -> int:
    logger: logging.Logger = logging.getLogger(__name__)
    logger.info(f"🚀 Starting Humble Bundle library retrieval process...")

    # Ensure output directory exists
    output_dir: Path = Path("output")
    output_dir.mkdir(exist_ok=True)
    output_file: Path = output_dir / "library.csv"

    humble = HumbleClient()

    # Strictly typing the list of dictionaries that represent our rows
    flat_library: list[dict[str, str]] = []
    
    csv_headers: list[str] = [
        "Index Game Key",
        "Order Game Key",
        "Amount Spent",
        "Currency",
        "Bundle Name",
        "Category",
        "Subproducts Count",
        "Game Name",
        "Downloads Count",
        "Platform",
        "Download Struct Count",
        "Download Name",
        "Download Link",
    ]

    try:
        async with httpx.AsyncClient(headers=humble.headers, timeout=config.request_timeout_seconds) as client:
            keys: list[OrderKey] = await humble.fetch_index(client)
            if not keys:
                logger.error(f"❌ No game keys found in the library. Halting execution.")
                return 1  # Exit with error code
            
            logger.info(f"📥 Beginning extraction of {len(keys)} bundles...")

            semaphore: asyncio.Semaphore = asyncio.Semaphore(5)  # Limit concurrent requests to 5

            async def process_key(index: int, total: int, key_obj: OrderKey) -> tuple[list[dict[str, str]], float, float]:
                async with semaphore:
                    logger.info(f"[{index}/{total}] Fetching details for: {key_obj.gamekey}")
                    details: OrderDetails | None = await humble.fetch_details(client, key_obj.gamekey)

                    local_rows: list[dict[str, str]] = []
                    local_total_usd: float = 0.0
                    local_total_eur: float = 0.0

                    if details:
                        if details.amount_spent is not None and details.currency:
                            amount_spent_value: float = details.amount_spent
                            currency_code: str = details.currency.upper()
                            if currency_code == "USD":
                                local_total_usd += amount_spent_value
                            elif currency_code == "EUR":
                                local_total_eur += amount_spent_value

                        index_game_key: str = key_obj.gamekey
                        order_game_key: str = details.gamekey
                        amount_spent: str = str(details.amount_spent) if details.amount_spent is not None else "N/A"
                        currency: str = details.currency if details.currency else "N/A"
                        bundle_name: str = details.product.bundle_name
                        category: str = details.product.category if details.product.category else "N/A"
                        subproducts_count: str = str(len(details.subproducts))

                        # Preserve order-level properties even when no subproducts exist.
                        if not details.subproducts:
                            local_rows.append({
                                "Index Game Key": index_game_key,
                                "Order Game Key": order_game_key,
                                "Amount Spent": amount_spent,
                                "Currency": currency,
                                "Bundle Name": bundle_name,
                                "Category": category,
                                "Subproducts Count": subproducts_count,
                                "Game Name": "N/A",
                                "Downloads Count": "0",
                                "Platform": "N/A",
                                "Download Struct Count": "0",
                                "Download Name": "N/A",
                                "Download Link": "No downloads available",
                            })
                            await asyncio.sleep(1)
                            return local_rows, local_total_usd, local_total_eur
                        
                        for sub in details.subproducts:
                            game_name: str = sub.name
                            downloads_count: str = str(len(sub.downloads))

                            # Case A: Steam Key Only (No direct downloads)
                            if not sub.downloads:
                                local_rows.append({
                                    "Index Game Key": index_game_key,
                                    "Order Game Key": order_game_key,
                                    "Amount Spent": amount_spent,
                                    "Currency": currency,
                                    "Bundle Name": bundle_name,
                                    "Category": category,
                                    "Subproducts Count": subproducts_count,
                                    "Game Name": game_name,
                                    "Downloads Count": downloads_count,
                                    "Platform": "N/A",
                                    "Download Struct Count": "0",
                                    "Download Name": "N/A",
                                    "Download Link": "No downloads available"
                                })
                                continue

                            # Case B: DRM-Free Downloads available
                            for dl_info in sub.downloads:
                                platform: str = dl_info.platform
                                download_struct_count: str = str(len(dl_info.download_struct))

                                # Preserve download-level properties even if there are no structs.
                                if not dl_info.download_struct:
                                    local_rows.append({
                                        "Index Game Key": index_game_key,
                                        "Order Game Key": order_game_key,
                                        "Amount Spent": amount_spent,
                                        "Currency": currency,
                                        "Bundle Name": bundle_name,
                                        "Category": category,
                                        "Subproducts Count": subproducts_count,
                                        "Game Name": game_name,
                                        "Downloads Count": downloads_count,
                                        "Platform": platform,
                                        "Download Struct Count": download_struct_count,
                                        "Download Name": "N/A",
                                        "Download Link": "No link",
                                    })
                                    continue

                                for struct in dl_info.download_struct:
                                    url: str = struct.url.web if struct.url and struct.url.web else "No link"
                                    download_name: str = struct.name
                                    local_rows.append({
                                        "Index Game Key": index_game_key,
                                        "Order Game Key": order_game_key,
                                        "Amount Spent": amount_spent,
                                        "Currency": currency,
                                        "Bundle Name": bundle_name,
                                        "Category": category,
                                        "Subproducts Count": subproducts_count,
                                        "Game Name": game_name,
                                        "Downloads Count": downloads_count,
                                        "Platform": platform,
                                        "Download Struct Count": download_struct_count,
                                        "Download Name": download_name,
                                        "Download Link": url
                                    })

                    # Rate Limiting: Hold the semaphore slot for 1 second before releasing it
                    await asyncio.sleep(1)
                    return local_rows, local_total_usd, local_total_eur

            # Create a list of concurrent tasks
            tasks = [
                process_key(index, len(keys), key_obj) 
                for index, key_obj in enumerate(keys, start=1)
            ]

            results: tuple[Any, ...] = await asyncio.gather(*tasks, return_exceptions=True) # type: ignore
            total_spent_usd: float = 0.0
            total_spent_eur: float = 0.0

            # Flatten the nested lists into our main flat_library
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"⚠️ A concurrent task failed: {result}")
                elif isinstance(result, tuple):
                    rows, usd_total, eur_total = result
                    flat_library.extend(rows)
                    total_spent_usd += usd_total
                    total_spent_eur += eur_total

        logger.info(f"💾 Saving {len(flat_library)} individual items to CSV...")

        with open(output_file, "w", newline='', encoding="utf-8-sig") as f:
            writer: csv.DictWriter[str] = csv.DictWriter(f, fieldnames=csv_headers)
            writer.writeheader()
            writer.writerows(flat_library)

        logger.info(
            f"💰 Total spent summary | USD: {total_spent_usd:.2f} | EUR: {total_spent_eur:.2f}"
        )
        logger.info(f"🎉 Successfully retrieved library data! Saved to {output_file.absolute()}")
        return 0  # Success exit code
    
    except Exception as e:
        logger.error(f"💥 An orchestration error occurred: {e}", exc_info=True)
        return 1  # Exit with error code


def main() -> int:
    setup_logging()
    return asyncio.run(async_main())

if __name__ == "__main__":
    raise SystemExit(main())
