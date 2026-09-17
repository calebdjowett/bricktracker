# BrickTracker

Mobile LEGO collection tracker with a Flutter client, FastAPI backend, SQLite persistence, BrickLink pricing, retirement watchlists, and portfolio analytics.

## Layout

- `backend/`: FastAPI API, scheduled price refresh, providers, and tests.
- `database/`: SQLite schema and seed data.
- `flutter_app/`: Flutter mobile client.
- `docs/`: architecture and setup documentation.

## Development

The backend uses Python 3.11+ and SQLite. The Flutter client targets Android and iOS. Configure BrickLink OAuth credentials in `backend/.env` before enabling live price refreshes.
