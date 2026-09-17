import asyncio

import httpx

from app.database import connection, initialize_database
from app.models import PriceSnapshotCreate
from app.providers import BrickLinkPriceProvider
from app.repository import add_price_snapshot


async def refresh_prices() -> None:
    """Run daily through cron: `python -m app.jobs`."""
    initialize_database()
    with connection() as database, httpx.AsyncClient(timeout=30) as client:
        provider = BrickLinkPriceProvider(client)
        for lego_set in database.execute("SELECT id, set_number, currency FROM lego_sets").fetchall():
            for price in await provider.prices_for_set(lego_set["set_number"], lego_set["currency"]):
                add_price_snapshot(database, lego_set["id"], PriceSnapshotCreate(condition=price.condition, average_price_cents=price.average_price_cents, currency=price.currency, observed_at=price.observed_at, provider="bricklink"))


if __name__ == "__main__":
    asyncio.run(refresh_prices())
