from contextlib import asynccontextmanager

import sqlite3
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Response, status

from app.database import get_database, initialize_database
from app.models import CollectionItemCreate, CollectionItemUpdate, PriceSnapshotCreate, WatchlistCreate
from app import repository


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="BrickTracker API", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def serialize(row: sqlite3.Row) -> dict:
    item = dict(row)
    paid = item.get("purchase_price_cents", 0) * item.get("quantity", 0)
    item["gain_loss_cents"] = item.get("current_value_cents", 0) - paid
    item["gain_loss_percent"] = round(item["gain_loss_cents"] * 100 / paid, 2) if paid else None
    return item


@app.post("/collection", status_code=status.HTTP_201_CREATED)
def add_collection_item(payload: CollectionItemCreate, database=Depends(get_database)) -> dict:
    return serialize(repository.create_collection_item(database, payload))


@app.get("/collection")
def collection(database=Depends(get_database)) -> list[dict]:
    return [serialize(item) for item in repository.list_collection_items(database)]


@app.patch("/collection/{item_id}")
def update_collection_item(item_id: int, payload: CollectionItemUpdate, database=Depends(get_database)) -> dict:
    item = repository.update_collection_item(database, item_id, payload)
    if item is None:
        raise HTTPException(404, "Collection item not found")
    return serialize(item)


@app.delete("/collection/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_collection_item(item_id: int, database=Depends(get_database)) -> Response:
    if not repository.delete_collection_item(database, item_id):
        raise HTTPException(404, "Collection item not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/sets/{set_id}/prices", status_code=status.HTTP_201_CREATED)
def store_price(set_id: int, payload: PriceSnapshotCreate, database=Depends(get_database)) -> dict:
    repository.add_price_snapshot(database, set_id, payload)
    return {"status": "stored"}


@app.get("/sets/{set_id}/price-history")
def get_price_history(set_id: int, database=Depends(get_database)) -> list[dict]:
    return [dict(row) for row in repository.price_history(database, set_id)]


@app.get("/dashboard")
def dashboard(database=Depends(get_database)) -> dict:
    items = [serialize(item) for item in repository.list_collection_items(database)]
    return {"collection_value_cents": sum(item["current_value_cents"] for item in items), "profit_loss_cents": sum(item["gain_loss_cents"] for item in items), "best_performing_sets": sorted(items, key=lambda item: item["gain_loss_cents"], reverse=True)[:5]}


@app.get("/retiring-soon")
def retiring_soon(database=Depends(get_database)) -> dict:
    rows = database.execute("SELECT ls.*, rs.status, rs.estimated_retirement_date FROM retirement_statuses rs JOIN lego_sets ls ON ls.id = rs.lego_set_id WHERE rs.status = 'retiring_soon' ORDER BY rs.estimated_retirement_date").fetchall()
    groups: dict[str, list[dict]] = {}
    themes = {"Star Wars", "Icons", "Technic", "Botanicals", "Harry Potter", "Marvel", "Architecture", "Ninjago", "Creator Expert", "City"}
    for row in rows:
        item = dict(row)
        item["months_remaining"] = max(0, round((date.fromisoformat(item["estimated_retirement_date"]) - date.today()).days / 30.44, 1)) if item["estimated_retirement_date"] else None
        groups.setdefault(item["theme"] if item["theme"] in themes else "Other themes", []).append(item)
    return {"groups": groups}


@app.post("/watchlist", status_code=status.HTTP_201_CREATED)
def watch_set(payload: WatchlistCreate, database=Depends(get_database)) -> dict:
    database.execute("INSERT OR REPLACE INTO watchlist_items (lego_set_id, notifications_enabled) VALUES (?, ?)", (payload.set_id, payload.notifications_enabled))
    database.commit()
    return {"status": "watching", "set_id": payload.set_id}