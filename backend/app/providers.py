from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

import httpx

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
    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    async def prices_for_set(self, set_number: str, currency: str) -> list[MarketPrice]:
        results = []
        for bricklink_condition, condition in (("N", PriceCondition.new), ("U", PriceCondition.used)):
            response = await self.client.get(f"https://api.bricklink.com/api/store/v1/items/SET/{set_number}/price", params={"guide_type": "sold", "new_or_used": bricklink_condition, "currency_code": currency})
            response.raise_for_status()
            payload = response.json()["data"]
            results.append(MarketPrice(condition, round(float(payload["avg_price"]) * 100), payload.get("currency_code", currency), datetime.now().astimezone()))
        return results
