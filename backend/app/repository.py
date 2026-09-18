from collections.abc import Mapping

from app.models import CollectionItemCreate, CollectionItemUpdate, PriceSnapshotCreate


def _collection_query(suffix: str) -> str:
    return """SELECT ci.id, ci.quantity, ci.condition, ci.purchase_price_cents, ci.purchased_at, ci.notes,
        ls.id AS set_id, ls.set_number, ls.name, ls.theme, ls.msrp_cents, ls.currency,
        new_price.average_price_cents AS average_new_price_cents,
        used_price.average_price_cents AS average_used_price_cents,
        COALESCE(CASE ci.condition WHEN 'sealed' THEN new_price.average_price_cents ELSE used_price.average_price_cents END, 0) * ci.quantity AS current_value_cents
        FROM collection_items ci JOIN lego_sets ls ON ls.id = ci.lego_set_id
        LEFT JOIN LATERAL (SELECT average_price_cents FROM price_snapshots WHERE lego_set_id = ls.id AND condition = 'new' ORDER BY observed_at DESC LIMIT 1) new_price ON TRUE
        LEFT JOIN LATERAL (SELECT average_price_cents FROM price_snapshots WHERE lego_set_id = ls.id AND condition = 'used' ORDER BY observed_at DESC LIMIT 1) used_price ON TRUE """ + suffix


def create_collection_item(database, owner_id: str, payload: CollectionItemCreate) -> Mapping:
    lego_set = payload.set
    name = lego_set.name or f"Set {lego_set.set_number}"
    set_id = database.execute("""INSERT INTO lego_sets (set_number, name, theme, msrp_cents, currency)
        VALUES (%s, %s, %s, %s, %s) ON CONFLICT(set_number) DO UPDATE SET name=EXCLUDED.name, theme=EXCLUDED.theme,
        msrp_cents=COALESCE(EXCLUDED.msrp_cents, lego_sets.msrp_cents), updated_at=CURRENT_TIMESTAMP RETURNING id""",
        (lego_set.set_number, name, lego_set.theme, lego_set.msrp_cents, lego_set.currency.upper())).fetchone()["id"]
    purchased_at = payload.purchased_at.isoformat() if payload.purchased_at else None
    existing = database.execute("""SELECT id FROM collection_items WHERE owner_id = %s AND lego_set_id = %s AND condition = %s
        AND purchase_price_cents = %s AND purchased_at IS NOT DISTINCT FROM %s AND notes IS NOT DISTINCT FROM %s""",
        (owner_id, set_id, payload.condition.value, payload.purchase_price_cents, purchased_at, payload.notes)).fetchone()
    if existing:
        database.execute("UPDATE collection_items SET quantity = quantity + %s, updated_at=CURRENT_TIMESTAMP WHERE id = %s", (payload.quantity, existing["id"]))
        item_id = existing["id"]
    else:
        item_id = database.execute("""INSERT INTO collection_items (owner_id, lego_set_id, quantity, condition, purchase_price_cents, purchased_at, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""", (owner_id, set_id, payload.quantity, payload.condition.value,
            payload.purchase_price_cents, purchased_at, payload.notes)).fetchone()["id"]
    return get_collection_item(database, owner_id, item_id)


def get_collection_item(database, owner_id: str, item_id: int) -> Mapping | None:
    return database.execute(_collection_query("WHERE ci.owner_id = %s AND ci.id = %s"), (owner_id, item_id)).fetchone()


def list_collection_items(database, owner_id: str) -> list[Mapping]:
    return database.execute(_collection_query("WHERE ci.owner_id = %s ORDER BY ls.theme, ls.set_number"), (owner_id,)).fetchall()


def update_collection_item(database, owner_id: str, item_id: int, payload: CollectionItemUpdate) -> Mapping | None:
    fields = payload.model_dump(exclude_unset=True)
    if not fields:
        return get_collection_item(database, owner_id, item_id)
    values = [value.value if hasattr(value, "value") else value.isoformat() if hasattr(value, "isoformat") else value for value in fields.values()]
    database.execute(f"UPDATE collection_items SET {', '.join(f'{field} = %s' for field in fields)}, updated_at=CURRENT_TIMESTAMP WHERE id = %s AND owner_id = %s", (*values, item_id, owner_id))
    return get_collection_item(database, owner_id, item_id)


def delete_collection_item(database, owner_id: str, item_id: int) -> bool:
    cursor = database.execute("DELETE FROM collection_items WHERE id = %s AND owner_id = %s", (item_id, owner_id))
    return bool(cursor.rowcount)


def user_owns_set(database, owner_id: str, set_id: int) -> bool:
    return database.execute("SELECT 1 FROM collection_items WHERE owner_id = %s AND lego_set_id = %s", (owner_id, set_id)).fetchone() is not None


def add_price_snapshot(database, set_id: int, payload: PriceSnapshotCreate) -> None:
    database.execute("""INSERT INTO price_snapshots
        (lego_set_id, condition, average_price_cents, currency, observed_at, provider) VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (lego_set_id, condition, observed_at, provider) DO UPDATE SET average_price_cents = EXCLUDED.average_price_cents, currency = EXCLUDED.currency""",
        (set_id, payload.condition.value, payload.average_price_cents, payload.currency.upper(), payload.observed_at.isoformat(), payload.provider))


def price_history(database, owner_id: str, set_id: int) -> list[Mapping]:
    return database.execute("""SELECT condition, average_price_cents, currency, observed_at FROM price_snapshots WHERE lego_set_id = %s
        AND EXISTS (SELECT 1 FROM collection_items WHERE lego_set_id = %s AND owner_id = %s) ORDER BY observed_at""", (set_id, set_id, owner_id)).fetchall()