import logging
import hashlib
import hmac
import json
from urllib.parse import parse_qsl
from typing import Optional, Dict
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session

from storage.db import get_db, get_or_create_user, User
from config import settings

logger = logging.getLogger(__name__)


def verify_telegram_webapp_data(init_data: str) -> Dict:
    """
    Verify Telegram WebApp initData signature
    
    According to: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    
    Args:
        init_data: The initData string from Telegram WebApp
        
    Returns:
        Parsed data dict if valid
        
    Raises:
        HTTPException: If signature is invalid
    """
    try:
        # Parse the initData string
        parsed_data = dict(parse_qsl(init_data))
        
        # Extract hash
        received_hash = parsed_data.pop('hash', None)
        if not received_hash:
            raise HTTPException(status_code=401, detail="Missing hash in initData")
        
        # Create data-check-string
        data_check_arr = [f"{k}={v}" for k, v in sorted(parsed_data.items())]
        data_check_string = '\n'.join(data_check_arr)
        
        # Create secret key
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=settings.bot_token.encode(),
            digestmod=hashlib.sha256
        ).digest()
        
        # Calculate hash
        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        # Verify hash
        if calculated_hash != received_hash:
            raise HTTPException(status_code=401, detail="Invalid initData signature")
        
        # Parse user data
        if 'user' in parsed_data:
            parsed_data['user'] = json.loads(parsed_data['user'])
        
        return parsed_data
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in initData")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to verify initData: {str(e)}")


def get_dev_user(db: Session) -> User:
    """
    Get or create development user for local testing

    WARNING: Only use in DEBUG mode!
    """
    dev_user = db.query(User).filter(User.telegram_id == 1).first()

    if not dev_user:
        logger.info("Creating dev user (telegram_id=1)")
        dev_user = User(
            telegram_id=1,
            username="admin",
            first_name="Dev",
            has_completed_onboarding=True
        )
        db.add(dev_user)
        db.commit()
        db.refresh(dev_user)

    return dev_user


def get_current_user(
    x_telegram_init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data"),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency to get current user.
    Supports Telegram WebApp initData and local generic user for development.
    """
    # 1. Dev/Local mode bypass
    if not x_telegram_init_data:
        # SECURITY: Only allow dev mode in DEBUG environment
        if not settings.debug:
            logger.error(
                "Missing Telegram auth header in production environment",
                extra={"endpoint": "get_current_user"}
            )
            raise HTTPException(
                status_code=401,
                detail="Authentication required. Please access via Telegram."
            )

        logger.warning(
            "⚠️  Using DEV MODE authentication - not secure for production!",
            extra={"user_id": 1, "username": "admin"}
        )

        # Dev mode: return mock admin user
        return get_dev_user(db)

    # 2. Production/Telegram mode
    data = verify_telegram_webapp_data(x_telegram_init_data)

    user_data = data.get('user')
    if not user_data:
        raise HTTPException(status_code=401, detail="User data not found in initData")

    telegram_id = user_data.get('id')
    if not telegram_id:
        raise HTTPException(status_code=401, detail="User ID not found in initData")

    user = get_or_create_user(
        db=db,
        telegram_id=telegram_id,
        username=user_data.get('username'),
        first_name=user_data.get('first_name')
    )

    # Update last_seen_at for activity tracking
    from datetime import datetime
    user.last_seen_at = datetime.utcnow()
    db.commit()

    return user


def get_current_user_optional(
    x_telegram_init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data"),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user or None (for public endpoints)"""

    if not x_telegram_init_data:
        # In dev mode, return dev user
        if settings.debug:
            logger.debug("Using dev user for optional auth endpoint")
            return get_dev_user(db)
        # In production, return None (unauthenticated)
        return None

    try:
        # Re-use the existing logic if token present
        return get_current_user(x_telegram_init_data=x_telegram_init_data, db=db)
    except HTTPException:
        # If headers are bad but endpoint is optional, return None?
        # Or should we raise because they TRIED to authenticate but failed?
        # The plan says:
        # except Exception as e:
        #    logger.warning(f"Invalid auth data in optional endpoint: {e}")
        #    return None
        # So I will follow that but reuse get_current_user logic if possible or copy paste
        pass
        
    try:
        # Copy-paste logic to avoid double fetching or recursion issues if logic changes
        # But actually let's assume get_current_user raises.
        # Let's trust get_current_user
        return get_current_user(x_telegram_init_data, db)
    except HTTPException as e:
        logger.warning(f"Invalid auth data in optional endpoint: {e.detail}")
        return None
    except Exception as e:
        logger.warning(f"Unexpected error in optional auth: {e}")
        return None
