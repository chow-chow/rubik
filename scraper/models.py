"""
Data models for the scraper system.

Contains all dataclass definitions for academic entities and scraper metadata.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SectionType(Enum):
    """Course section types."""

    CORE = "core"
    ELECTIVE = "elective"
    HUMANITIES = "humanities"


class ScraperStatus(Enum):
    """Scraper execution statuses."""

    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class Program:
    """Represents an academic program."""

    code: str
    name: str
    duration: int
    study_plan_codes: List[str] = field(default_factory=list)
    total_courses: int = 0


@dataclass
class Course:
    """Represents a course."""

    code: str
    name: str
    credits: Optional[int] = None
    total_groups: int = 0
    has_lab: bool = False
    lab: Optional[Dict] = None


@dataclass
class Group:
    """Represents a course group (section)."""

    code: str
    group: str
    professor: str
    schedules: List[Dict] = field(default_factory=list)


@dataclass
class Professor:
    """Represents a professor with ratings."""

    id: int
    full_name: str
    first_name: str
    last_name: str
    num_ratings: int
    rating: float


@dataclass
class StudyPlan:
    """Represents a study plan."""

    code: str
    name: str
    release_year: int
    required_credits: int
    elective_credits: int
    credit_limit_per_period: Optional[int] = None
    courses: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class ScraperResult:
    """Result of a scraper execution."""

    scraper_name: str
    status: str
    items_processed: int
    execution_time: float
    timestamp: str
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScraperMetadata:
    """Metadata for tracking scraper executions."""

    timestamp: str
    version: str = "1.0.0"
    execution_time_seconds: float = 0.0
    total_items: int = 0
    scrapers: Dict[str, Dict] = field(default_factory=dict)

    @classmethod
    def create_empty(cls) -> "ScraperMetadata":
        """Create empty metadata."""
        return cls(timestamp=datetime.now().isoformat(), scrapers={})
