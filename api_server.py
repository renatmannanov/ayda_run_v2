"""
API Server - FastAPI Backend for Ayda Run

Provides REST API for:
- Activities (CRUD)
- Participation (join/leave)
- Static file serving for webapp
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
import logging
import json

from storage.db import init_db, User
from app.core.dependencies import get_db, get_current_user
from config import settings

# Telegram Bot
from telegram import Update
from telegram.ext import Application, CommandHandler
from bot.start_handler import start

# Logger setup (needed before lifespan)
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    # Startup
    init_db()
    logger.info("[SUCCESS] Database initialized")

    # Initialize Telegram bot
    bot_app = Application.builder().token(settings.bot_token).build()

    # Register handlers
    bot_app.add_handler(CommandHandler("start", start))

    # TODO: Add more handlers as we implement onboarding
    # from bot.onboarding_handler import onboarding_conv_handler
    # bot_app.add_handler(onboarding_conv_handler)

    # Initialize bot (but don't start polling - we use webhook)
    await bot_app.initialize()
    await bot_app.start()

    # Set webhook
    webhook_url = f"{settings.app_url}/webhook/{settings.bot_token}"
    await bot_app.bot.set_webhook(url=webhook_url)
    logger.info(f"[SUCCESS] Telegram bot webhook set to: {webhook_url}")

    # Store bot app in FastAPI app state
    app.state.bot_app = bot_app

    yield

    # Shutdown
    await bot_app.stop()
    await bot_app.shutdown()
    logger.info("[SUCCESS] Telegram bot shutdown")

app = FastAPI(
    title="Ayda Run API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "PUT"],
    allow_headers=["Content-Type", "X-Telegram-Init-Data"],
    max_age=600,
)

# Rate Limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.rate_limit_global]
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom rate limit error response"""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Too Many Requests",
            "message": "Вы превысили лимит запросов. Пожалуйста, попробуйте позже.",
            "retry_after": str(exc.limit)
        }, # exc.detail sometimes is not what we expect in some versions, using exc.limit or generic message is safer, but plan suggests exc.detail check if it works.
        headers={
            "Retry-After": "60" # Default fallback
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom handler for validation errors (422)
    Logs detailed information about validation failures for debugging
    """
    # Get body from exception if available
    body_str = "Body not available"
    try:
        if hasattr(exc, 'body'):
            body_str = str(exc.body)
    except:
        pass

    # Log detailed error information with proper formatting
    error_details = {
        "method": request.method,
        "path": str(request.url.path),
        "errors": exc.errors(),
        "body": body_str
    }

    logger.error(
        f"❌ VALIDATION ERROR: {request.method} {request.url.path}\n"
        f"Errors: {json.dumps(exc.errors(), indent=2, default=str)}\n"
        f"Body: {body_str}"
    )

    # Return user-friendly error with details
    # Need to serialize errors to JSON-safe format (ValueError objects can't be serialized)
    errors_json_safe = json.loads(json.dumps(exc.errors(), default=str))

    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "message": "Данные не прошли валидацию",
            "details": errors_json_safe
        }
    )

# ============================================================================
# Schemas (only what's needed in api_server.py)
# ============================================================================
from schemas.user import UserResponse

# Import time and middleware for logging
import time
from starlette.middleware.base import BaseHTTPMiddleware

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests"""

    async def dispatch(self, request, call_next):
        # Start timer
        start_time = time.time()

        # Log request
        logger.info(
            f"Request started",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None
            }
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            process_time = time.time() - start_time

            # Log response
            logger.info(
                f"Request completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(process_time * 1000, 2)
                }
            )

            return response

        except Exception as e:
            # Log error
            logger.error(
                f"Request failed: {str(e)}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e)
                },
                exc_info=True
            )
            raise

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# ============================================================================
# Include Routers
# ============================================================================
from app.routers import activities, clubs, groups

app.include_router(activities.router)
app.include_router(clubs.router)
app.include_router(groups.router)

# ============================================================================
# Static File Serving
# ============================================================================

@app.get("/")
async def root():
    """Serve the main webapp page"""
    return FileResponse("webapp/dist/index.html")

# Serve all static files from dist folder
from fastapi.staticfiles import StaticFiles
import os

# Mount static files directory
if os.path.exists("webapp/dist"):
    app.mount("/assets", StaticFiles(directory="webapp/dist/assets"), name="assets")

# ============================================================================
# Health Check
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "Ayda Run API"}

# ============================================================================
# Telegram Bot Webhook
# ============================================================================

@app.post("/webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    """
    Telegram webhook endpoint.

    Receives updates from Telegram and processes them through the bot.
    """
    # Verify token
    if token != settings.bot_token:
        logger.warning(f"Invalid webhook token attempt: {token[:10]}...")
        return {"status": "error", "message": "Invalid token"}

    # Get bot application from app state
    bot_app: Application = request.app.state.bot_app

    # Parse update
    try:
        update_data = await request.json()
        update = Update.de_json(update_data, bot_app.bot)

        # Process update
        await bot_app.process_update(update)

        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error processing webhook update: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

# ============================================================================
# Users API
# ============================================================================

# UserResponse imported from schemas
from schemas.user import UserStatsResponse
from storage.db import Participation, Activity
from sqlalchemy import func

@app.get("/api/users/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user


@app.get("/api/users/me/stats", response_model=UserStatsResponse)
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user statistics"""
    # Get all participations for current user
    participations = db.query(Participation).filter(
        Participation.user_id == current_user.id
    ).all()

    total_activities = len(participations)
    completed_activities = sum(1 for p in participations if p.attended)

    # Calculate attendance rate
    attendance_rate = 0
    if total_activities > 0:
        attendance_rate = int((completed_activities / total_activities) * 100)

    # Calculate total distance from activities where user participated
    total_distance = 0.0
    sport_counts = {}

    for participation in participations:
        activity = db.query(Activity).filter(Activity.id == participation.activity_id).first()
        if activity:
            # Add distance
            if activity.distance:
                total_distance += activity.distance

            # Count sport types
            if activity.sport_type:
                sport_counts[activity.sport_type] = sport_counts.get(activity.sport_type, 0) + 1

    # Find most frequent sport
    most_frequent_sport = None
    if sport_counts:
        most_frequent_sport = max(sport_counts, key=sport_counts.get)

    return UserStatsResponse(
        total_activities=total_activities,
        completed_activities=completed_activities,
        total_distance=round(total_distance, 1),
        most_frequent_sport=most_frequent_sport,
        attendance_rate=attendance_rate
    )


class OnboardingData(BaseModel):
    """Request model for completing onboarding"""
    preferred_sports: Optional[list[str]] = None  # e.g., ["running", "trail"]


@app.patch("/api/users/me/onboarding", response_model=UserResponse)
async def complete_onboarding(
    onboarding_data: OnboardingData,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete user onboarding and save preferences"""
    import json

    # Update onboarding status
    current_user.has_completed_onboarding = True

    # Save preferred sports as JSON string
    if onboarding_data.preferred_sports:
        current_user.preferred_sports = json.dumps(onboarding_data.preferred_sports)

    db.commit()
    db.refresh(current_user)

    return current_user

# Activities API moved to app/routers/activities.py

# Groups & Clubs API moved to app/routers/clubs.py and app/routers/groups.py

# ============================================================================
# Server Startup
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting Ayda Run API on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
