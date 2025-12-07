"""
Authentication utilities for Telegram Mini App

This module handles:
- Verification of Telegram WebApp initData signature
- Extraction of user information from initData
- FastAPI dependency for getting current user
"""

import hashlib
import hmac
import json
from urllib.parse import parse_qsl
from typing import Optional, Dict
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session

from storage.db import get_db, get_or_create_user, User
from config import settings


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


def get_current_user(
    x_telegram_init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data"),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency to get current user.
    Supports Telegram WebApp initData and local generic user for development.
    """
    # 1. Dev/Local mode bypass
    # If no header is provided and we are likely in dev environment
    if not x_telegram_init_data:
        # Create a mock user for local development
        # In production this should be disabled or protected
        return get_or_create_user(
            db=db,
            telegram_id=1,  # Super Admin ID
            username="admin",
            first_name="Admin User"
        )

    # 2. Production/Telegram mode
    data = verify_telegram_webapp_data(x_telegram_init_data)
    
    user_data = data.get('user')
    if not user_data:
        raise HTTPException(status_code=401, detail="User data not found in initData")
    
    telegram_id = user_data.get('id')
    if not telegram_id:
        raise HTTPException(status_code=401, detail="User ID not found in initData")
    
    return get_or_create_user(
        db=db,
        telegram_id=telegram_id,
        username=user_data.get('username'),
        first_name=user_data.get('first_name')
    )


def get_current_user_optional(
    x_telegram_init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data"),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Optional auth"""
    return get_current_user(x_telegram_init_data=x_telegram_init_data, db=db)
