import asyncio
from datetime import date

from app.database import connection, initialize_database
from app.models import PriceSnapshotCreate
from app.providers import BrickLinkPriceProvider
from app.repository import add_price_snapshot


async def refresh_set_prices(database, set_id: int, set_number: str, currency: str) -> None:
    provider = BrickLinkPriceProvider()
    for price in await provider.prices_for_set(set_number, currency):
        add_price_snapshot(database, set_id, PriceSnapshotCreate(condition=price.condition, average_price_cents=price.average_price_cents, currency=price.currency, observed_at=price.observed_at, provider="bricklink"))


async def refresh_prices() -> None:
    """Run daily through cron: `python -m app.jobs`."""
    initialize_database()
    with connection() as database:
        await refresh_stale_prices(database)


async def refresh_stale_prices(database) -> None:
    """Refresh every owned set once per calendar day when the dashboard is opened."""
    for lego_set in database.execute("""SELECT DISTINCT ls.id, ls.set_number, ls.currency
        FROM lego_sets ls JOIN collection_items ci ON ci.lego_set_id = ls.id
        WHERE NOT EXISTS (
            SELECT 1 FROM price_snapshots ps
            WHERE ps.lego_set_id = ls.id AND DATE(ps.observed_at) = %s
        )""", (date.today().isoformat(),)).fetchall():
        try:
            await refresh_set_prices(database, lego_set["id"], lego_set["set_number"], lego_set["currency"])
        except Exception:
            continue


if __name__ == "__main__":
    asyncio.run(refresh_prices())
