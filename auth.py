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
    authorization: str = Header(..., description="Telegram WebApp initData"),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency to get current user from Telegram WebApp initData
    
    Usage:
        @app.get("/api/endpoint")
        def endpoint(current_user: User = Depends(get_current_user)):
            ...
    
    Args:
        authorization: initData from Telegram WebApp (in Authorization header)
        db: Database session
        
    Returns:
        User object
        
    Raises:
        HTTPException: If initData is invalid or user not found
    """
    # Verify initData
    data = verify_telegram_webapp_data(authorization)
    
    # Extract user info
    user_data = data.get('user')
    if not user_data:
        raise HTTPException(status_code=401, detail="User data not found in initData")
    
    telegram_id = user_data.get('id')
    if not telegram_id:
        raise HTTPException(status_code=401, detail="User ID not found in initData")
    
    # Get or create user
    user = get_or_create_user(
        telegram_id=telegram_id,
        username=user_data.get('username'),
        first_name=user_data.get('first_name')
    )
    
    return user


def get_current_user_optional(
    authorization: Optional[str] = Header(None, description="Telegram WebApp initData"),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optional authentication - returns None if not authenticated
    
    Useful for public endpoints that optionally customize for logged-in users
    """
    if not authorization:
        return None
    
    try:
        return get_current_user(authorization=authorization, db=db)
    except HTTPException:
        return None
