from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass
from datetime import datetime
import os

from requests_oauthlib import OAuth1Session

from app.models import PriceCondition


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
        client = OAuth1Session(os.environ["BRICKLINK_CONSUMER_KEY"], client_secret=os.environ["BRICKLINK_CONSUMER_SECRET"], resource_owner_key=os.environ["BRICKLINK_TOKEN"], resource_owner_secret=os.environ["BRICKLINK_TOKEN_SECRET"], signature_type="auth_header")
        results = []
        for bricklink_condition, condition in (("N", PriceCondition.new), ("U", PriceCondition.used)):
            response = client.get(f"https://api.bricklink.com/api/store/v1/items/SET/{set_number}/price", params={"guide_type": "sold", "new_or_used": bricklink_condition, "currency_code": currency}, timeout=30)
            response.raise_for_status()
            payload = response.json()["data"]
            results.append(MarketPrice(condition, round(float(payload["avg_price"]) * 100), payload.get("currency_code", currency), datetime.now().astimezone()))
        return results
