PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS lego_sets (
    id INTEGER PRIMARY KEY,
    set_number TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    theme TEXT NOT NULL DEFAULT 'Other',
    msrp_cents INTEGER,
    currency TEXT NOT NULL DEFAULT 'USD',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS collection_items (
    id INTEGER PRIMARY KEY,
    lego_set_id INTEGER NOT NULL REFERENCES lego_sets(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    condition TEXT NOT NULL CHECK (condition IN ('sealed', 'used')),
    purchase_price_cents INTEGER NOT NULL CHECK (purchase_price_cents >= 0),
    purchased_at TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS price_snapshots (
    id INTEGER PRIMARY KEY,
    lego_set_id INTEGER NOT NULL REFERENCES lego_sets(id) ON DELETE CASCADE,
    condition TEXT NOT NULL CHECK (condition IN ('new', 'used')),
    average_price_cents INTEGER NOT NULL CHECK (average_price_cents >= 0),
    currency TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    provider TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (lego_set_id, condition, observed_at, provider)
);

CREATE INDEX IF NOT EXISTS idx_price_snapshots_set_condition_date
    ON price_snapshots (lego_set_id, condition, observed_at DESC);

CREATE TABLE IF NOT EXISTS retirement_statuses (
    id INTEGER PRIMARY KEY,
    lego_set_id INTEGER NOT NULL UNIQUE REFERENCES lego_sets(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('active', 'retiring_soon', 'retired', 'unknown')),
    estimated_retirement_date TEXT,
    source TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS watchlist_items (
    id INTEGER PRIMARY KEY,
    lego_set_id INTEGER NOT NULL UNIQUE REFERENCES lego_sets(id) ON DELETE CASCADE,
    notifications_enabled INTEGER NOT NULL DEFAULT 1 CHECK (notifications_enabled IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notification_preferences (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    thirty_days_enabled INTEGER NOT NULL DEFAULT 1 CHECK (thirty_days_enabled IN (0, 1)),
    ninety_days_enabled INTEGER NOT NULL DEFAULT 1 CHECK (ninety_days_enabled IN (0, 1)),
    six_months_enabled INTEGER NOT NULL DEFAULT 1 CHECK (six_months_enabled IN (0, 1))
);

INSERT OR IGNORE INTO notification_preferences (id) VALUES (1);