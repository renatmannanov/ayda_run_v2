# Setup Guide

Complete step-by-step guide for deploying your Telegram Mini App.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Creating a Telegram Bot](#creating-a-telegram-bot)
- [Database Setup](#database-setup)
- [Deployment on Railway](#deployment-on-railway)
- [Deployment on Render](#deployment-on-render)
- [Optional: Google Sheets Integration](#optional-google-sheets-integration)
- [Optional: MongoDB Integration](#optional-mongodb-integration)

---

## Prerequisites

- Python 3.9+
- A Telegram account
- Git (for deployment)
- Railway or Render account (for production)

---

## Local Development

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create Environment File

```bash
cp .env.example .env
```

Edit `.env`:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
DATABASE_URL=sqlite:///./app.db
```

### 3. Run Locally

**Option A: Manual (two terminals)**

Terminal 1 - Bot:
```bash
python main.py
```

Terminal 2 - API Server:
```bash
python api_server.py
```

**Option B: Using start script**

```bash
sh start.sh
```

### 4. Test with ngrok

For testing Telegram Mini App locally:

```bash
# Install ngrok
npm install -g ngrok

# Expose port 8000
ngrok http 8000
```

Copy the ngrok URL (e.g., `https://abc123.ngrok.io`) and use it in BotFather.

---

## Creating a Telegram Bot

### 1. Talk to [@BotFather](https://t.me/BotFather)

```
/newbot
```

Follow the prompts to choose a name and username for your bot.

### 2. Save the Bot Token

BotFather will give you a token like:
```
123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

Add this to your `.env` file:
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 3. Set Mini App URL

Once deployed (or using ngrok for testing):

```
/mybots
[Select your bot]
Bot Settings → Menu Button → Edit Menu Button URL
```

Enter your deployment URL (e.g., `https://your-app.railway.app`)

### 4. Test Your Bot

Send `/start` to your bot in Telegram to verify it's working.

---

## Database Setup

### SQLite (Development)

Already configured by default:
```env
DATABASE_URL=sqlite:///./app.db
```

No additional setup needed!

### PostgreSQL (Production)

#### Railway
Railway provides PostgreSQL automatically:
1. Add PostgreSQL service in your project
2. Railway will set `DATABASE_URL` automatically

#### Render
1. Create a PostgreSQL database in Render
2. Copy the Internal Database URL
3. Add as environment variable:
   ```env
   DATABASE_URL=postgresql://user:pass@host/dbname
   ```

---

## Deployment on Railway

**Railway is recommended** - easier setup and better DX.

### 1. Install Railway CLI

```bash
npm install -g @railway/cli
```

### 2. Login

```bash
railway login
```

### 3. Initialize Project

```bash
# In your project directory
railway init
```

Choose "Empty Project" → Give it a name

### 4. Add PostgreSQL (Optional but recommended)

```bash
railway add
```

Choose "PostgreSQL" → Railway will configure it automatically

### 5. Set Environment Variables

```bash
railway variables
```

Add:
- `TELEGRAM_BOT_TOKEN` - Your bot token from BotFather

Railway automatically sets:
- `DATABASE_URL` (if you added PostgreSQL)
- `PORT`

### 6. Deploy

```bash
railway up
```

### 7. Get Your URL

```bash
railway domain
```

Or add a custom domain:
```bash
railway domain add your-domain.com
```

### 8. Update Bot Settings

Go to BotFather and set your Menu Button URL to your Railway URL.

### 9. Monitor Logs

```bash
railway logs
```

---

## Deployment on Render

### 1. Connect GitHub

1. Push your code to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com/)
3. Click "New +" → "Web Service"
4. Connect your repository

### 2. Configure Service

- **Name**: your-app-name
- **Environment**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `sh start.sh`

### 3. Set Environment Variables

In the "Environment" section, add:
- `TELEGRAM_BOT_TOKEN` - Your bot token

### 4. Add PostgreSQL (Optional)

1. Create new PostgreSQL database
2. Copy "Internal Database URL"
3. Add as environment variable:
   - Key: `DATABASE_URL`
   - Value: The internal URL

### 5. Deploy

Click "Create Web Service" → Render will build and deploy

### 6. Get Your URL

Render assigns a URL like `https://your-app.onrender.com`

### 7. Update Bot Settings

Set this URL in BotFather's Menu Button configuration.

---

## Optional: Google Sheets Integration

### 1. Create Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project
3. Enable Google Sheets API
4. Create Service Account
5. Download JSON credentials

### 2. Share Your Sheet

1. Create a Google Sheet
2. Click "Share"
3. Add service account email (from credentials JSON)
4. Give "Editor" permissions

### 3. Configure Environment

**Option A: File path (local development)**
```env
GOOGLE_SHEETS_CREDENTIALS=path/to/credentials.json
```

**Option B: JSON string (Railway/Render)**

Copy entire JSON content and set as environment variable:
```env
GOOGLE_SHEETS_CREDENTIALS={"type":"service_account",...}
```

### 4. Uncomment Dependencies

In `requirements.txt`:
```python
gspread
google-auth
```

### 5. Update Code

Uncomment Google Sheets code in:
- `config.py`
- `main.py`

---

## Optional: MongoDB Integration

### 1. Create MongoDB Atlas Cluster

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create free cluster
3. Create database user
4. Whitelist IP: `0.0.0.0/0` (allow all)
5. Get connection string

### 2. Configure Environment

```env
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/dbname
```

### 3. Install Dependencies

In `requirements.txt`:
```python
pymongo
motor  # for async operations
```

### 4. Implement Storage

Create `storage/mongodb.py` implementing `BaseStorage` interface.

---

## Troubleshooting

### Bot not responding

1. Check logs: `railway logs` or Render dashboard
2. Verify `TELEGRAM_BOT_TOKEN` is set correctly
3. Ensure bot is running: check Railway/Render status

### Mini App not loading

1. Check Mini App URL in BotFather
2. Verify API server is running on correct port
3. Check browser console for errors

### Database errors

1. Verify `DATABASE_URL` is set
2. Check database is running (Railway/Render dashboard)
3. Ensure migrations ran: `init_db()` in `main.py`

### Deploy failures

**Railway**:
```bash
railway logs --deployment
```

**Render**:
Check "Logs" tab in dashboard

Common issues:
- Missing dependencies in `requirements.txt`
- Incorrect `Procfile` or `start.sh`
- Environment variables not set

---

## Next Steps

- Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system
- Check [CODE_PATTERNS.md](CODE_PATTERNS.md) for examples
- Review [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) for UI guidelines

---

## Support

For issues with:
- **Telegram Bot API**: [Official Docs](https://core.telegram.org/bots/api)
- **Railway**: [Railway Docs](https://docs.railway.app/)
- **Render**: [Render Docs](https://render.com/docs)
