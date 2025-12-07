# Telegram Mini App Template

A production-ready template for building Telegram Mini Apps with Python backend and vanilla JavaScript frontend.

Based on the proven architecture from [ayda_think](https://github.com/renatmannanov/ayda_think) project.

## Features

- **Minimalist Design** - Clean, professional UI with gray-scale palette
- **Modular Architecture** - Separated concerns: bot, API server, storage, frontend
- **Flexible Storage** - Support for SQLite, PostgreSQL, MongoDB, Google Sheets
- **Telegram Integration** - Ready-to-use WebApp API wrapper
- **Railway/Render Ready** - Deployment configurations included
- **Well-Documented** - Extensive inline comments and documentation

## Quick Start

1. **Clone/Copy this template**
   ```bash
   cd your-project-name
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

4. **Run locally**
   ```bash
   # Terminal 1: Start bot
   python main.py
   
   # Terminal 2: Start API server
   python api_server.py
   ```

5. **Open in Telegram**
   - Create a bot with [@BotFather](https://t.me/BotFather)
   - Set Mini App URL: `https://your-domain.com`
   - Test locally using ngrok or similar

## Project Structure

```
├── bot/                    # Telegram bot handlers
│   ├── start_handler.py   # /start command
│   ├── utils.py           # Helper functions
│   └── channel_integration.py  # Example: channel integration
├── storage/               # Data persistence layer
│   ├── db.py             # SQLAlchemy models
│   └── base.py           # Abstract storage class
├── webapp/               # Frontend application
│   ├── index.html       # Main HTML
│   ├── styles.css       # Minimalist design system
│   ├── api.js           # Telegram WebApp wrapper
│   ├── app.js           # Application logic
│   └── components/      # Reusable UI components
│       ├── card.js
│       ├── button.js
│       ├── empty_state.js
│       └── list.js
├── docs/                 # Documentation
│   ├── SETUP_GUIDE.md   # Deployment guide
│   ├── ARCHITECTURE.md  # Technical decisions
│   ├── DESIGN_SYSTEM.md # UI/UX guidelines
│   └── CODE_PATTERNS.md # Code examples
├── config.py            # Pydantic Settings
├── main.py              # Bot entry point
├── api_server.py        # FastAPI server
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template
└── Procfile            # Deployment config
```

## Customization

All template files are marked with `TODO` comments indicating where you should customize for your project:

- Update bot welcome message in `bot/start_handler.py`
- Add API endpoints in `api_server.py`
- Customize UI in `webapp/`
- Modify database models in `storage/db.py`

## Documentation

- **[Setup Guide](docs/SETUP_GUIDE.md)** - Step-by-step deployment
- **[Architecture](docs/ARCHITECTURE.md)** - Design decisions
- **[Design System](docs/DESIGN_SYSTEM.md)** - UI guidelines
- **[Code Patterns](docs/CODE_PATTERNS.md)** - Common patterns

## Deployment

### Railway (Recommended)

1. Install Railway CLI: `npm install -g @railway/cli`
2. Login: `railway login`
3. Initialize: `railway init`
4. Add env vars: `railway variables`
5. Deploy: `railway up`

See [SETUP_GUIDE.md](docs/SETUP_GUIDE.md) for detailed instructions.

### Render

1. Connect your GitHub repo
2. Create new Web Service
3. Set environment variables
4. Deploy

## License

MIT - feel free to use for your projects

## Credits

Template created from [ayda_think](https://github.com/renatmannanov/ayda_think) project architecture.
