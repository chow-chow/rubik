"""
Programs scraper - fetches academic programs data.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from ..config import get_config
from ..models import Program, ScraperResult, ScraperStatus, StudyPlan
from ..parsers import ProgramsParser, StudyPlansParser

logger = logging.getLogger(__name__)


def scrape_programs(http_client, storage) -> ScraperResult:
    """
    Scrape academic programs.

    Args:
        http_client: HTTPClient instance
        storage: DataStorage instance

    Returns:
        ScraperResult with execution details
    """
    start_time = time.time()
    config = get_config()

    try:
        logger.info("Starting programs scraper")

        soup = http_client.get(config.PROGRAMS_URL)
        if not soup:
            return _create_result(
                status=ScraperStatus.FAILED,
                items=0,
                errors=["Failed to fetch programs page"],
                start_time=start_time,
            )

        parser = ProgramsParser()
        programs_data = parser.parse(soup)

        if not programs_data:
            return _create_result(
                status=ScraperStatus.FAILED,
                items=0,
                errors=["No programs found"],
                start_time=start_time,
            )

        logger.info(f"Found {len(programs_data)} programs")

        with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
            results = list(
                executor.map(
                    lambda p: _process_program(p, http_client, config), programs_data
                )
            )

        programs = [r for r in results if r is not None]

        if programs:
            storage.save_programs(programs)

        execution_time = time.time() - start_time
        status = ScraperStatus.SUCCESS if programs else ScraperStatus.FAILED

        logger.info(
            f"Programs scraper completed: {len(programs)} programs in {execution_time:.2f}s"
        )

        return _create_result(
            status=status, items=len(programs), errors=[], execution_time=execution_time
        )

    except Exception as e:
        logger.error(f"Error in programs scraper: {e}", exc_info=True)
        return _create_result(
            status=ScraperStatus.FAILED, items=0, errors=[str(e)], execution_time=time.time() - start_time
        )


def _process_program(program_data: dict, http_client, config) -> Program:
    """Process single program."""
    code = program_data["code"]
    name = program_data["name"]

    try:
        logger.info(f"Processing program {code}: {name}")

        url = config.STUDY_PLANS_URL.format(code)
        soup = http_client.get(url)

        if not soup:
            logger.warning(f"Failed to fetch study plans for {code}")
            return None

        parser = StudyPlansParser()
        plans = parser.parse(soup, code)

        if not plans:
            logger.warning(f"No study plans for {code}")
            return None

        study_plan_codes = [p.code for p in plans]
        duration = plans[0].release_year if hasattr(plans[0], "release_year") else 10

        try:
            table = soup.find("table", class_="TblBlk")
            if table:
                rows = table.find_all("tr")[1:]
                if rows:
                    cells = rows[0].find_all("td")
                    if len(cells) >= 6:
                        duration_text = cells[5].get_text(strip=True)
                        duration = int(duration_text.split()[0])
        except (ValueError, IndexError, AttributeError):
            duration = 10

        return Program(
            code=code,
            name=name,
            duration=duration,
            study_plan_codes=study_plan_codes,
            total_courses=0,
        )

    except Exception as e:
        logger.error(f"Error processing program {code}: {e}")
        return None


def _create_result(
    status: ScraperStatus, items: int, errors: list, execution_time: float
) -> ScraperResult:
    """Create scraper result."""
    return ScraperResult(
        scraper_name="programs",
        status=status.value,
        items_processed=items,
        execution_time=execution_time,
        timestamp=datetime.now().isoformat(),
        errors=errors,
    )
