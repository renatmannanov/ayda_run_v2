"""
Pydantic models for race card data.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class MedalType(str, Enum):
    """Medal type based on overall placement."""
    GOLD = "gold"
    SILVER = "silver"
    BRONZE = "bronze"
    NONE = "none"


class Checkpoint(BaseModel):
    """Single checkpoint/split data."""
    name: str                    # "CP1", "CP2", "Finish"
    distance_km: Optional[float] = None  # 5.0
    time: str                    # "00:38:12"
    pace: Optional[str] = None   # "7:38 /km"


class ParticipantResult(BaseModel):
    """Participant race result data from MyRace."""
    # Required fields
    bib: str
    name: str
    time: str                    # "01:58:24"
    place: int                   # Overall position

    # Optional fields
    club: Optional[str] = None
    race: Optional[str] = None   # Distance name "VK 1000"
    category: Optional[str] = None  # "M30-39"
    place_category: Optional[str] = None  # "1/89"
    place_gender: Optional[int] = None  # Absolute M/F position
    gender: Optional[str] = None  # "M" or "F"
    pace: Optional[str] = None   # "8:28 min/km"

    # Track data (optional)
    distance_km: Optional[float] = None
    elevation_gain: Optional[int] = None  # +1000m
    start_elevation: Optional[int] = None  # 2850m
    finish_elevation: Optional[int] = None  # 3850m

    # Checkpoints/splits (optional)
    checkpoints: List[Checkpoint] = Field(default_factory=list)

    @property
    def medal(self) -> MedalType:
        """Determine medal type based on place."""
        if self.place == 1:
            return MedalType.GOLD
        elif self.place == 2:
            return MedalType.SILVER
        elif self.place == 3:
            return MedalType.BRONZE
        return MedalType.NONE

    @property
    def has_elevation_data(self) -> bool:
        """Check if elevation profile should be shown."""
        return bool(self.start_elevation and self.finish_elevation)

    @property
    def has_checkpoints(self) -> bool:
        """Check if splits data is available."""
        return len(self.checkpoints) > 0

    @property
    def gender_label(self) -> str:
        """Get gender label for display."""
        if self.gender == "M":
            return "муж."
        elif self.gender == "F":
            return "жен."
        return ""


class EventInfo(BaseModel):
    """Race event metadata."""
    name: str = "Race Results"   # "Amangeldy Race 2026"
    organizer: str = "Unknown"   # "AthleteX"
    timing_provider: str = "MyRace"
    date: Optional[str] = None
    url: Optional[str] = None


class RaceCardData(BaseModel):
    """Complete data for generating race cards."""
    participant: ParticipantResult
    event: EventInfo


class RaceCardOutput(BaseModel):
    """Output from card generation."""
    single_post: bytes           # PNG bytes for Format A
    carousel_slides: List[bytes] # PNG bytes for Format B (3 slides)

    class Config:
        arbitrary_types_allowed = True
