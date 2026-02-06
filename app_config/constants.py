"""
Application Constants

This file contains all application-wide constants including:
- Default location settings (country, city)
- Available locations for filtering
- Other configuration constants
"""

# ============= LOCATION DEFAULTS =============

DEFAULT_COUNTRY = "Kazakhstan"
DEFAULT_CITY = "Almaty"

# ============= AVAILABLE LOCATIONS =============

AVAILABLE_COUNTRIES = ["Kazakhstan"]

AVAILABLE_CITIES = {
    "Kazakhstan": ["Almaty", "Astana", "Shymkent"]
}

# ============= VALIDATION =============

def validate_location(country: str, city: str) -> bool:
    """Validate if country and city combination is valid"""
    if country not in AVAILABLE_COUNTRIES:
        return False

    if city not in AVAILABLE_CITIES.get(country, []):
        return False

    return True

def get_cities_for_country(country: str) -> list[str]:
    """Get list of available cities for a given country"""
    return AVAILABLE_CITIES.get(country, [])


# ============= ENTITY CREATION LIMITS =============

MAX_CLUBS_PER_USER = 1
MAX_GROUPS_PER_USER = 3
MAX_UPCOMING_ACTIVITIES_PER_USER = 100


# ============= POST-TRAINING FLOW =============

POST_TRAINING_REMINDER_DELAY_HOURS = 3
POST_TRAINING_SUMMARY_DELAY_HOURS = 5
POST_TRAINING_MAX_REMINDERS = 1

ALLOWED_TRAINING_LINK_DOMAINS = [
    "strava.com", "www.strava.com",
    "connect.garmin.com",
    "training.coros.com",
    "suuntoapp.com", "www.suuntoapp.com",
    "flow.polar.com",
]
