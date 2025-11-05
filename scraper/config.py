"""
Configuration for the scraper system.

Provides URL endpoints and HTTP settings.
"""

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class ScraperConfig:
    """Main configuration for scrapers."""

    PROGRAMS_URL = "https://www.dgae-siae.unam.mx/educacion/carreras.php?plt=0011"
    STUDY_PLANS_URL = (
        "https://www.dgae-siae.unam.mx/educacion/planes.php?acc=pde&plt=0011&crr={}"
    )
    COURSES_URL = (
        "https://www.dgae-siae.unam.mx/educacion/planes.php?acc=est&pde={}&planop=1"
    )
    GROUPS_URL = (
        "https://www.ssa.ingenieria.unam.mx/cj/tmp/programacion_horarios/{}.html"
    )
    LABS_JS_URL = "https://www.ssa.ingenieria.unam.mx/cj/tmp/programacion_horarios/listaAsignatura.js"
    PROFESSORS_URL = (
        "https://www.misprofesores.com/escuelas/Facultad-de-Ingenieria_1511"
    )

    MAX_RETRIES: int = 3
    TIMEOUT: int = 30
    DELAY_RANGE: Tuple[float, float] = (0.5, 1.5)

    USER_AGENTS: List[str] = field(
        default_factory=lambda: [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        ]
    )

    DATA_DIR: str = "data"

    MAX_WORKERS: int = 5


config = ScraperConfig()


def get_config() -> ScraperConfig:
    """Get the global configuration instance."""
    return config
