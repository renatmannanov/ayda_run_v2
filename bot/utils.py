import re
from typing import Optional
from storage.db import get_user_config, save_user as db_save_user

def save_user(user_id: int, config_data: str = None):
    """
    Saves or updates a user's configuration in the database.
    
    Args:
        user_id: Telegram user ID
        config_data: Configuration data (customize based on your needs)
    """
    db_save_user(user_id, config_data)

def get_user_data(user_id: int) -> Optional[str]:
    """
    Retrieves the configuration data for a given user from the database.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        Configuration data if user exists, None otherwise
    """
    return get_user_config(user_id)

def extract_spreadsheet_id(url_or_id: str) -> Optional[str]:
    """
    Extracts the spreadsheet ID from a Google Sheets URL or returns the ID if it looks like one.
    
    This is an example utility function for Google Sheets integration.
    TODO: Remove if not using Google Sheets.
    
    Args:
        url_or_id: Full URL or spreadsheet ID
        
    Returns:
        Extracted spreadsheet ID or None
        
    Example:
        >>> extract_spreadsheet_id("https://docs.google.com/spreadsheets/d/ABC123/edit")
        'ABC123'
        >>> extract_spreadsheet_id("ABC123")
        'ABC123'
    """
    # Regex for extracting ID from URL
    # Matches strings like /d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url_or_id)
    if match:
        return match.group(1)
    
    # If it's just the ID (alphanumeric + -_), return it
    if re.match(r'^[a-zA-Z0-9-_]+$', url_or_id):
        return url_or_id
        
    return None

# TODO: Add your project-specific utility functions here
# Examples:
# - parse_user_input()
# - validate_data()
# - format_response()
# - extract_tags()
