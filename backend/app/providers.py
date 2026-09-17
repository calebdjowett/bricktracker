from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass
from datetime import datetime
import os
from pathlib import Path

from dotenv import load_dotenv
from requests_oauthlib import OAuth1Session

from app.models import PriceCondition

load_dotenv(Path(__file__).parents[1] / ".env")


@dataclass(frozen=True)
class MarketPrice:
    condition: PriceCondition
    average_price_cents: int
    currency: str
    observed_at: datetime


class PriceProvider(ABC):
    @abstractmethod
    async def prices_for_set(self, set_number: str, currency: str) -> list[MarketPrice]:
        """Return sold-price averages for both conditions."""


class RetirementProvider(ABC):
    @abstractmethod
    async def retirement_for_set(self, set_number: str) -> dict | None:
        """Allow BrickEconomy, Rebrickable, LEGO.com, or a scraper to supply retirement data."""


class BrickLinkPriceProvider(PriceProvider):
    async def prices_for_set(self, set_number: str, currency: str) -> list[MarketPrice]:
        return await asyncio.to_thread(self._prices_for_set, set_number, currency)

    def _prices_for_set(self, set_number: str, currency: str) -> list[MarketPrice]:
        required_settings = ("BRICKLINK_CONSUMER_KEY", "BRICKLINK_CONSUMER_SECRET", "BRICKLINK_TOKEN", "BRICKLINK_TOKEN_SECRET")
        if missing_settings := [setting for setting in required_settings if not os.environ.get(setting)]:
            raise RuntimeError(f"BrickLink pricing is not configured. Add {', '.join(missing_settings)} to backend/.env.")
        client = OAuth1Session(os.environ["BRICKLINK_CONSUMER_KEY"], client_secret=os.environ["BRICKLINK_CONSUMER_SECRET"], resource_owner_key=os.environ["BRICKLINK_TOKEN"], resource_owner_secret=os.environ["BRICKLINK_TOKEN_SECRET"], signature_type="auth_header")
        results = []
        for bricklink_condition, condition in (("N", PriceCondition.new), ("U", PriceCondition.used)):
            response = client.get(f"https://api.bricklink.com/api/store/v1/items/SET/{set_number}/price", params={"guide_type": "sold", "new_or_used": bricklink_condition, "currency_code": currency}, timeout=30)
            response.raise_for_status()
            response_payload = response.json()
            if response_payload.get("meta", {}).get("code") != 200:
                message = response_payload.get("meta", {}).get("description", "BrickLink returned no price data")
                raise RuntimeError(f"BrickLink price lookup for {set_number} failed: {message}")
            payload = response_payload["data"]
            results.append(MarketPrice(condition, round(float(payload["avg_price"]) * 100), payload.get("currency_code", currency), datetime.now().astimezone()))
        return results
