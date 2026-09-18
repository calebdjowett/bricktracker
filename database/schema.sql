CREATE TABLE IF NOT EXISTS lego_sets (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    set_number TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    theme TEXT NOT NULL DEFAULT 'Other',
    msrp_cents INTEGER,
    currency TEXT NOT NULL DEFAULT 'USD',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS collection_items (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    lego_set_id BIGINT NOT NULL REFERENCES lego_sets(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    condition TEXT NOT NULL CHECK (condition IN ('sealed', 'used')),
    purchase_price_cents INTEGER NOT NULL CHECK (purchase_price_cents >= 0),
    purchased_at DATE,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_collection_items_owner ON collection_items (owner_id);

CREATE TABLE IF NOT EXISTS price_snapshots (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    lego_set_id BIGINT NOT NULL REFERENCES lego_sets(id) ON DELETE CASCADE,
    condition TEXT NOT NULL CHECK (condition IN ('new', 'used')),
    average_price_cents INTEGER NOT NULL CHECK (average_price_cents >= 0),
    currency TEXT NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    provider TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (lego_set_id, condition, observed_at, provider)
);

CREATE INDEX IF NOT EXISTS idx_price_snapshots_set_condition_date
    ON price_snapshots (lego_set_id, condition, observed_at DESC);

CREATE TABLE IF NOT EXISTS retirement_statuses (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    lego_set_id BIGINT NOT NULL UNIQUE REFERENCES lego_sets(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('active', 'retiring_soon', 'retired', 'unknown')),
    estimated_retirement_date DATE,
    source TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS watchlist_items (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    lego_set_id BIGINT NOT NULL REFERENCES lego_sets(id) ON DELETE CASCADE,
    notifications_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (owner_id, lego_set_id)
);

CREATE TABLE IF NOT EXISTS notification_preferences (
    owner_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    thirty_days_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    ninety_days_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    six_months_enabled BOOLEAN NOT NULL DEFAULT TRUE
);