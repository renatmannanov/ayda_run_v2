"""
Strava OAuth Router

Endpoints:
- GET /api/strava/auth - Redirect to Strava OAuth
- GET /api/strava/callback - Handle OAuth callback (returns HTML page that closes)
- DELETE /api/strava/disconnect - Disconnect Strava account
- GET /api/strava/status - Check if Strava is connected
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from urllib.parse import urlencode
import httpx
import logging

from config import settings
from storage.db import User
from app.core.dependencies import get_db, get_current_user
from app.services.strava_service import StravaService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/strava", tags=["strava"])


# HTML template for OAuth callback (closes window + shows success)
CALLBACK_SUCCESS_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Strava Connected</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #fc4c02 0%, #ff6b35 100%);
        }
        .container {
            text-align: center;
            padding: 40px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            max-width: 320px;
        }
        .icon {
            font-size: 64px;
            margin-bottom: 16px;
        }
        h1 {
            color: #333;
            margin: 0 0 12px 0;
            font-size: 24px;
            font-weight: 600;
        }
        p {
            color: #666;
            margin: 0;
            font-size: 16px;
        }
        .strava-logo {
            width: 120px;
            margin-top: 20px;
            opacity: 0.7;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">&#x2705;</div>
        <h1>Strava &#x43F;&#x43E;&#x434;&#x43A;&#x43B;&#x44E;&#x447;&#x435;&#x43D;&#x430;!</h1>
        <p>&#x41C;&#x43E;&#x436;&#x435;&#x442;&#x435; &#x437;&#x430;&#x43A;&#x440;&#x44B;&#x442;&#x44C; &#x44D;&#x442;&#x43E; &#x43E;&#x43A;&#x43D;&#x43E;</p>
    </div>
    <script>
        // Close window after 3 seconds
        setTimeout(function() {
            window.close();
        }, 3000);
    </script>
</body>
</html>
"""

CALLBACK_ERROR_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>&#x41E;&#x448;&#x438;&#x431;&#x43A;&#x430;</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background: #f5f5f5;
        }}
        .container {{
            text-align: center;
            padding: 40px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            max-width: 320px;
        }}
        .icon {{
            font-size: 64px;
            margin-bottom: 16px;
        }}
        h1 {{
            color: #333;
            margin: 0 0 12px 0;
            font-size: 24px;
            font-weight: 600;
        }}
        p {{
            color: #666;
            margin: 0;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">&#x274C;</div>
        <h1>&#x41E;&#x448;&#x438;&#x431;&#x43A;&#x430; &#x43F;&#x43E;&#x434;&#x43A;&#x43B;&#x44E;&#x447;&#x435;&#x43D;&#x438;&#x44F;</h1>
        <p>{error}</p>
    </div>
</body>
</html>
"""


@router.get("/auth")
async def strava_auth(
    user_id: str = Query(..., description="User ID for OAuth state"),
    db: Session = Depends(get_db)
):
    """
    Redirect to Strava OAuth authorization page.

    Called from bot /connect_strava command via inline button URL.
    user_id is passed as state parameter to callback.
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if already connected
    if user.strava_athlete_id:
        return HTMLResponse(content=CALLBACK_SUCCESS_HTML)

    # Build Strava OAuth URL
    base_url = (settings.base_url or "").rstrip("/")
    if not base_url:
        raise HTTPException(status_code=500, detail="BASE_URL not configured")

    callback_url = f"{base_url}/api/strava/callback"

    params = urlencode({
        "client_id": settings.strava_client_id,
        "redirect_uri": callback_url,
        "response_type": "code",
        "scope": "read,activity:read_all",
        "state": user_id  # Pass user_id as state for callback
    })

    strava_auth_url = f"https://www.strava.com/oauth/authorize?{params}"
    logger.info(f"Redirecting user {user_id} to Strava OAuth")

    return RedirectResponse(url=strava_auth_url, status_code=302)


@router.get("/callback")
async def strava_callback(
    code: str = Query(None),
    state: str = Query(None),
    error: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Handle Strava OAuth callback.

    Returns HTML page that shows success/error and closes window.
    """
    # Handle OAuth error (user denied access)
    if error:
        logger.warning(f"Strava OAuth error: {error}")
        error_msg = "Доступ отклонен" if error == "access_denied" else error
        return HTMLResponse(content=CALLBACK_ERROR_HTML.format(error=error_msg))

    if not code or not state:
        logger.warning("Strava callback missing code or state")
        return HTMLResponse(content=CALLBACK_ERROR_HTML.format(error="Отсутствуют параметры"))

    # Find user by state (user_id)
    user = db.query(User).filter(User.id == state).first()
    if not user:
        logger.warning(f"Strava callback user not found: {state}")
        return HTMLResponse(content=CALLBACK_ERROR_HTML.format(error="Пользователь не найден"))

    # Check if already connected (e.g., user clicked twice)
    if user.strava_athlete_id:
        logger.info(f"User {user.id} already has Strava connected")
        return HTMLResponse(content=CALLBACK_SUCCESS_HTML)

    # Exchange code for tokens
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://www.strava.com/oauth/token",
                data={
                    "client_id": settings.strava_client_id,
                    "client_secret": settings.strava_client_secret,
                    "code": code,
                    "grant_type": "authorization_code"
                },
                timeout=30.0
            )

        if resp.status_code != 200:
            logger.error(f"Strava token exchange failed: {resp.status_code} {resp.text}")
            return HTMLResponse(content=CALLBACK_ERROR_HTML.format(error="Ошибка авторизации"))

        token_data = resp.json()

        # Check if this athlete is already connected to another user
        existing_user = db.query(User).filter(
            User.strava_athlete_id == token_data["athlete"]["id"],
            User.id != user.id
        ).first()

        if existing_user:
            logger.warning(
                f"Strava athlete {token_data['athlete']['id']} already connected to user {existing_user.id}"
            )
            return HTMLResponse(
                content=CALLBACK_ERROR_HTML.format(error="Этот аккаунт Strava уже подключен к другому пользователю")
            )

        # Save tokens (encrypted)
        strava_service = StravaService(db)
        strava_service.save_tokens(user, token_data)

        logger.info(f"Strava connected for user {user.id}, athlete_id={token_data['athlete']['id']}")

        return HTMLResponse(content=CALLBACK_SUCCESS_HTML)

    except httpx.TimeoutException:
        logger.error("Strava token exchange timeout")
        return HTMLResponse(content=CALLBACK_ERROR_HTML.format(error="Таймаут соединения"))
    except Exception as e:
        logger.error(f"Error in Strava callback: {e}", exc_info=True)
        return HTMLResponse(content=CALLBACK_ERROR_HTML.format(error="Внутренняя ошибка"))


@router.delete("/disconnect")
async def disconnect_strava(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disconnect Strava account.

    Requires authentication via Telegram Web App.
    """
    if not current_user.strava_athlete_id:
        raise HTTPException(status_code=400, detail="Strava not connected")

    strava_service = StravaService(db)
    strava_service.clear_tokens(current_user)

    return {"message": "Strava disconnected", "success": True}


@router.get("/status")
async def strava_status(
    current_user: User = Depends(get_current_user)
):
    """
    Check if Strava is connected.

    Requires authentication via Telegram Web App.
    """
    return {
        "connected": current_user.strava_athlete_id is not None,
        "athlete_id": current_user.strava_athlete_id
    }
