import sqlite3

from app.models import CollectionItemCreate, CollectionItemUpdate, PriceSnapshotCreate


def _collection_query(suffix: str) -> str:
    return """SELECT ci.id, ci.quantity, ci.condition, ci.purchase_price_cents, ci.purchased_at, ci.notes,
        ls.id AS set_id, ls.set_number, ls.name, ls.theme, ls.msrp_cents, ls.currency,
        new_price.average_price_cents AS average_new_price_cents,
        used_price.average_price_cents AS average_used_price_cents,
        COALESCE(CASE ci.condition WHEN 'sealed' THEN new_price.average_price_cents ELSE used_price.average_price_cents END, 0) * ci.quantity AS current_value_cents
        FROM collection_items ci JOIN lego_sets ls ON ls.id = ci.lego_set_id
        LEFT JOIN price_snapshots new_price ON new_price.id = (SELECT id FROM price_snapshots WHERE lego_set_id = ls.id AND condition = 'new' ORDER BY observed_at DESC LIMIT 1)
        LEFT JOIN price_snapshots used_price ON used_price.id = (SELECT id FROM price_snapshots WHERE lego_set_id = ls.id AND condition = 'used' ORDER BY observed_at DESC LIMIT 1) """ + suffix


def create_collection_item(database: sqlite3.Connection, payload: CollectionItemCreate) -> sqlite3.Row:
    lego_set = payload.set
    name = lego_set.name or f"Set {lego_set.set_number}"
    database.execute("""INSERT INTO lego_sets (set_number, name, theme, msrp_cents, currency)
        VALUES (?, ?, ?, ?, ?) ON CONFLICT(set_number) DO UPDATE SET name=excluded.name, theme=excluded.theme,
        msrp_cents=COALESCE(excluded.msrp_cents, lego_sets.msrp_cents), updated_at=CURRENT_TIMESTAMP""",
        (lego_set.set_number, name, lego_set.theme, lego_set.msrp_cents, lego_set.currency.upper()))
    set_id = database.execute("SELECT id FROM lego_sets WHERE set_number = ?", (lego_set.set_number,)).fetchone()[0]
    purchased_at = payload.purchased_at.isoformat() if payload.purchased_at else None
    existing = database.execute("""SELECT id FROM collection_items WHERE lego_set_id = ? AND condition = ?
        AND purchase_price_cents = ? AND COALESCE(purchased_at, '') = COALESCE(?, '') AND COALESCE(notes, '') = COALESCE(?, '')""",
        (set_id, payload.condition.value, payload.purchase_price_cents, purchased_at, payload.notes)).fetchone()
    if existing:
        database.execute("UPDATE collection_items SET quantity = quantity + ?, updated_at=CURRENT_TIMESTAMP WHERE id = ?", (payload.quantity, existing["id"]))
        item_id = existing["id"]
    else:
        cursor = database.execute("""INSERT INTO collection_items (lego_set_id, quantity, condition, purchase_price_cents, purchased_at, notes)
            VALUES (?, ?, ?, ?, ?, ?)""", (set_id, payload.quantity, payload.condition.value, payload.purchase_price_cents,
            purchased_at, payload.notes))
        item_id = cursor.lastrowid
    database.commit()
    return get_collection_item(database, item_id)


def get_collection_item(database: sqlite3.Connection, item_id: int) -> sqlite3.Row | None:
    return database.execute(_collection_query("WHERE ci.id = ?"), (item_id,)).fetchone()


def list_collection_items(database: sqlite3.Connection) -> list[sqlite3.Row]:
    return database.execute(_collection_query("ORDER BY ls.theme, ls.set_number")).fetchall()


def update_collection_item(database: sqlite3.Connection, item_id: int, payload: CollectionItemUpdate) -> sqlite3.Row | None:
    fields = payload.model_dump(exclude_unset=True)
    if not fields:
        return get_collection_item(database, item_id)
    values = [value.value if hasattr(value, "value") else value.isoformat() if hasattr(value, "isoformat") else value for value in fields.values()]
    database.execute(f"UPDATE collection_items SET {', '.join(f'{field} = ?' for field in fields)}, updated_at=CURRENT_TIMESTAMP WHERE id = ?", (*values, item_id))
    database.commit()
    return get_collection_item(database, item_id)


def delete_collection_item(database: sqlite3.Connection, item_id: int) -> bool:
    cursor = database.execute("DELETE FROM collection_items WHERE id = ?", (item_id,))
    database.commit()
    return bool(cursor.rowcount)


def add_price_snapshot(database: sqlite3.Connection, set_id: int, payload: PriceSnapshotCreate) -> None:
    database.execute("""INSERT OR REPLACE INTO price_snapshots
        (lego_set_id, condition, average_price_cents, currency, observed_at, provider) VALUES (?, ?, ?, ?, ?, ?)""",
        (set_id, payload.condition.value, payload.average_price_cents, payload.currency.upper(), payload.observed_at.isoformat(), payload.provider))
    database.commit()


def price_history(database: sqlite3.Connection, set_id: int) -> list[sqlite3.Row]:
    return database.execute("SELECT condition, average_price_cents, currency, observed_at FROM price_snapshots WHERE lego_set_id = ? ORDER BY observed_at", (set_id,)).fetchall()