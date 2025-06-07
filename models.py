from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class RetreatDates:
    """Date range for a retreat."""

    start: Optional[datetime] = None
    end: Optional[datetime] = None


@dataclass
class RetreatLocation:
    """Detailed retreat location information."""

    practice_center: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None


@dataclass
class RetreatEvent:
    """Unified representation of a retreat event."""

    title: str
    dates: RetreatDates
    teachers: List[str]
    location: RetreatLocation
    description: str
    link: str
    other: Dict[str, str] = field(default_factory=dict)
