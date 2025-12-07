# Storage Layer

This directory contains database and data storage modules.

## Files

- `db.py` - SQLAlchemy User model and database setup
- `base.py` - Abstract base class for storage implementations
- `google_sheets.py` - (Optional) Google Sheets integration
- `mongodb.py` - (Optional) MongoDB integration

## Usage

Choose the storage backend that fits your project needs:

1. **SQLite/PostgreSQL** (via db.py) - User authentication and metadata
2. **Google Sheets** - Simple data storage without database setup
3. **MongoDB** - NoSQL document storage for flexible data models

See `ARCHITECTURE.md` for more details on storage patterns.
