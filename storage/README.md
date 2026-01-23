# Storage Layer

This directory contains database and data storage modules.

## Files

- `db.py` - SQLAlchemy models and PostgreSQL database setup
- `base.py` - Abstract base class for storage implementations
- `user_storage.py` - User operations
- `club_storage.py` - Club operations
- `group_storage.py` - Group operations
- `membership_storage.py` - Membership operations
- `join_request_storage.py` - Join request operations
- `google_sheets.py` - (Optional) Google Sheets integration
- `mongodb.py` - (Optional) MongoDB integration

## Usage

Primary storage backend:

1. **PostgreSQL** (via db.py) - Main database for all application data

Optional integrations:
2. **Google Sheets** - Simple data storage without database setup
3. **MongoDB** - NoSQL document storage for flexible data models

See `ARCHITECTURE.md` for more details on storage patterns.
