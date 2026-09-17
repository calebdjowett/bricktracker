from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class CollectionCondition(str, Enum):
    sealed = "sealed"
    used = "used"


class PriceCondition(str, Enum):
    new = "new"
    used = "used"


class SetCreate(BaseModel):
    set_number: str = Field(pattern=r"^\d{3,8}-\d$")
    name: str | None = None
    theme: str = "Other"
    msrp_cents: int | None = Field(default=None, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)


class CollectionItemCreate(BaseModel):
    set: SetCreate
    quantity: int = Field(gt=0)
    condition: CollectionCondition
    purchase_price_cents: int = Field(ge=0)
    purchased_at: date | None = None
    notes: str | None = None


class CollectionItemUpdate(BaseModel):
    quantity: int | None = Field(default=None, gt=0)
    condition: CollectionCondition | None = None
    purchase_price_cents: int | None = Field(default=None, ge=0)
    purchased_at: date | None = None
    notes: str | None = None


class PriceSnapshotCreate(BaseModel):
    condition: PriceCondition
    average_price_cents: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    observed_at: datetime
    provider: str


class WatchlistCreate(BaseModel):
    set_id: int
    notifications_enabled: bool = True
