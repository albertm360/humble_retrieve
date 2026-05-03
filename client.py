import logging
from typing import Any
import httpx
from pydantic import ValidationError

from config import config
from models import OrderKey, OrderDetails

logger = logging.getLogger(__name__)


class HumbleClient:
    def __init__(self):
        self.base_url: str = "https://www.humblebundle.com/api/v1"
        self.headers: dict = {
            "User-Agent": config.user_agent,
            "Accept": "application/json",
            "Cookie": f"_simpleauth_sess={config.humble_session_key.get_secret_value()}"
        }


    async def fetch_index(self, client: httpx.AsyncClient) -> list[OrderKey]:
        """Fetches the master list of all gamekeys"""
        url: str = f"{self.base_url}/user/order"
        logger.info(f"🔍 Requesting master library index from {url}...")

        try:
            response: httpx.Response = await client.get(url)
            response.raise_for_status()

            raw_data: list[dict[str, Any]] = response.json()

            valid_keys: list[OrderKey] = []

            for item in raw_data:
                try:
                    valid_keys.append(OrderKey.model_validate(item))
                except ValidationError:
                    logger.warning(f"⚠️ Failed to parse an index item: {item.get('gamekey', 'Unknown')}")

            logger.info(f"✅ Successfully retrieved {len(valid_keys)} valid gamekeys.")
            return valid_keys
        
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Auth or Network failure (HTTP {e.response.status_code})", exc_info=True)
            return []
        except httpx.RequestError as e:
            logger.error("❌ Connection failed.", exc_info=True)
            return []
        

    async def fetch_details(self, client: httpx.AsyncClient, gamekey: str) -> OrderDetails | None:
        """Fetches the specific subproducts and download links for a gamekey."""
        url: str = f"{self.base_url}/order/{gamekey}"

        try:
            response: httpx.Response = await client.get(url)
            response.raise_for_status()

            return OrderDetails.model_validate(response.json())
        
        except httpx.HTTPError as e:
            logger.error(f"⚠️ Network error while fetching {gamekey}: {e}")
            return None
            
        except ValidationError:
            logger.error(f"🛑 Data contract violation for {gamekey}!", exc_info=True)
            return None