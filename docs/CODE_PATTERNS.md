# Code Patterns

Essential code patterns for Telegram Mini Apps. Use `search_in_file` to find specific patterns.

---

## Bot Handlers

### Basic Command

```python
from telegram import Update
from telegram.ext import ContextTypes

async def my_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text("Hello!")

# Register in main.py
application.add_handler(CommandHandler("mycommand", my_command))
```

### Text Handler

```python
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    # Process text
    await update.message.reply_text("Processed!")

# Register
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
```

---

## API Endpoints

### GET with Query

```python
from fastapi import Query, HTTPException

@app.get("/api/items")
async def get_items(user_id: int = Query(...), limit: int = Query(10)):
    try:
        # Your logic
        return {"items": [], "count": 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### POST with Body

```python
from pydantic import BaseModel

class CreateRequest(BaseModel):
    user_id: int
    title: str
    content: str

@app.post("/api/items")
async def create_item(request: CreateRequest):
    # Save to database
    return {"id": "123", "title": request.title}
```

---

## Storage

### Save/Get User

```python
from storage.db import save_user, get_user_config

# Save
save_user(user_id=12345, config_data="config")

# Get
config = get_user_config(user_id=12345)
```

### SQLAlchemy Query

```python
from storage.db import SessionLocal, User

session = SessionLocal()
try:
    user = session.query(User).filter(User.user_id == 12345).first()
finally:
    session.close()
```

---

## Frontend Components

### Using Components

```javascript
import { Card } from './components/card.js';
import { Button } from './components/button.js';
import { EmptyState } from './components/empty_state.js';

// Render card
container.innerHTML = Card({
    title: 'My Title',
    content: 'My content'
});

// Render empty state
container.innerHTML = EmptyState({
    icon: '📋',
    title: 'No items',
    subtitle: 'Create your first item'
});

// Render button
const btn = Button({
    text: 'Click Me',
    variant: 'primary',
    id: 'myBtn'
});
```

### Fetching Data

```javascript
import { api } from './api.js';

async function loadData() {
    try {
        const userId = api.getUserId();
        const data = await api.fetch(`/api/items?user_id=${userId}`);
        state.items = data.items;
        render();
    } catch (error) {
        api.showAlert('Failed to load');
    }
}
```

### Event Delegation

```javascript
function setupEventListeners() {
    document.addEventListener('click', (e) => {
        const action = e.target.dataset.action;
        if (action) {
            handleAction(action);
        }
    });
}
```

---

## Error Handling

### Bot Errors

```python
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Error: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("An error occurred")

application.add_error_handler(error_handler)
```

### API Errors

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": str(exc)})
```

---

## Common Utilities

### Extract Tags

```python
import re

def extract_tags(text: str) -> list[str]:
    return re.findall(r'#\w+', text)
```

### Format Date

```python
from datetime import datetime

def format_date(dt: datetime) -> str:
    return dt.strftime("%d %b %Y")
```

---

## Quick Reference

```python
# Bot: Send message
await update.message.reply_text("Hello")
await context.bot.send_message(chat_id=123, text="Hello")

# API: Return/Error
return {"key": "value"}
raise HTTPException(status_code=404, detail="Not found")
```

```javascript
// Frontend: API calls
api.showAlert('Message');
api.haptic('medium');
api.fetch('/api/endpoint');
```

---

**📚 For detailed patterns**, use `search_in_file` to find specific sections by keyword.
