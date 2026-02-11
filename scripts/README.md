# Scripts

## send_message.py

Send Telegram messages to production users from local machine.

### Prerequisites

Requires `PROD_DATABASE_URL` and `TELEGRAM_BOT_TOKEN` in `.env`.

### Usage

```bash
# Dry run — show spammed users without sending:
python scripts/send_message.py --spammed-on 2026-02-11 --dry-run

# Send apology to spammed users:
python scripts/send_message.py --spammed-on 2026-02-11

# Send to specific users by telegram_id:
python scripts/send_message.py --users 1082768332 930226366 205836252 1041924294

# Custom message:
python scripts/send_message.py --users 1082768332 --message "Ваш текст"
```
