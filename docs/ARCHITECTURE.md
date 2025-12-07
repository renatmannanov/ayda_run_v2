# Architecture

Technical overview of the Telegram Mini App template.

## Overview

Three-tier architecture:
1. **Telegram Bot** - User interactions
2. **API Server** - FastAPI backend
3. **Storage Layer** - Data persistence

```
User → Telegram Platform
         ├── Bot Commands
         ├── WebApp UI → FastAPI Server
         └── Channel Updates
                  ↓
             Storage Layer
```

---

## Components

### Bot Layer (`bot/`)

**Purpose**: Handle Telegram interactions

**Key Files**:
- `start_handler.py` - /start command
- `utils.py` - Helper functions
- `channel_integration.py` - Example handler

**Pattern**:
```python
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # Your logic
    await update.message.reply_text("Response")
```

### API Server (`api_server.py`)

**Purpose**: Serve webapp and HTTP API

**Features**:
- Static file serving (HTML, CSS, JS)
- REST endpoints (JSON)
- Database access (SQLAlchemy)

**Pattern**:
```python
@app.get("/api/endpoint")
async def endpoint():
    return {"data": "..."}
```

### Storage Layer (`storage/`)

**Purpose**: Data pers persistence abstraction

**Files**:
- `base.py` - Abstract interface
- `db.py` - SQLAlchemy (SQLite/PostgreSQL)

**Extensibility**: Implement `BaseStorage` for custom backends (MongoDB, Redis, etc.)

### Frontend (`webapp/`)

**Purpose**: User interface

**Structure**:
```
webapp/
├── index.html
├── styles.css
├── api.js         # Telegram WebApp wrapper
├── app.js         # Main logic
└── components/    # Reusable components
    ├── card.js
    ├── button.js
    ├── empty_state.js
    └── list.js
```

**Architecture**: Vanilla JS + ES6 modules + Components

---

## Data Flow

### Bot Command
```
User → Bot Handler → Storage → Response
```

### WebApp
```
User → app.js → API Server → Storage → JSON → Render
```

---

## Database Schema

### User Model

```python
class User:
    id: Integer           # PK
    user_id: Integer      # Telegram ID (unique)
    config_data: String   # Generic config
    created_at: DateTime
    updated_at: DateTime
```

**Customize**: Add fields for your project (e.g., `subscription_tier`, `settings`)

---

## Configuration

### Settings (Pydantic)

```python
class Settings(BaseSettings):
    bot_token: str
    database_url: str = "sqlite:///./app.db"
    debug: bool = False
    # Add your settings
```

**Benefits**: Type safety, validation, auto-completion

---

## Extension Points

### 1. New Bot Command
```python
# bot/my_handler.py
async def my_command(update, context):
    # Logic
    pass

# main.py
application.add_handler(CommandHandler("cmd", my_command))
```

### 2. New API Endpoint
```python
# api_server.py
@app.get("/api/new")
async def new_endpoint():
    return {"data": "..."}
```

### 3. New Storage Backend
```python
# storage/custom.py
class MyStorage(BaseStorage):
    async def save_data(self, dest_id, data):
        # Implementation
        pass
```

### 4. New UI Component
```javascript
// webapp/components/my_component.js
export function MyComponent({ prop }) {
    return `<div>${prop}</div>`;
}
```

---

## Best Practices

### Code Organization
✅ One handler per file  
✅ Type hints in Python  
✅ Clear function names  
❌ Don't mix business logic with handlers  

### Performance
✅ Use async/await  
✅ Batch database queries  
✅ Cache frequent data  

### Security
✅ Validate user input  
✅ Use environment variables for secrets  
✅ Log errors (not sensitive data)  
❌ Never commit `.env` files  

---

## Deployment

### Railway / Render
Both run `start.sh` which launches bot + API concurrently.

**Railway** (recommended):
- Auto-detects Python
- Built-in PostgreSQL
- Simple CLI deployment

**Render**:
- GitHub integration
- Manual PostgreSQL setup
- Web dashboard

---

## Scalability

**Bot**: Use webhooks (not polling) for production  
**API**: Connection pooling, caching  
**Storage**: PostgreSQL (relational), MongoDB (flexible schemas)

---

## Further Reading

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
