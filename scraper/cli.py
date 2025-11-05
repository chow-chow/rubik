"""
Command-line interface for the scraper system.

Usage:
    python -m scraper.cli programs
    python -m scraper.cli courses
    python -m scraper.cli labs
    python -m scraper.cli groups
    python -m scraper.cli professors
    python -m scraper.cli all

Note: Professor-groups linking runs automatically after groups/professors scraping.
"""

import logging
import sys
import time

import click

from .http_client import HTTPClient
from .linker import link_professors_groups
from .models import ScraperResult, ScraperStatus
from .scrapers import courses, groups, labs, professors, programs
from .storage import DataStorage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


SCRAPERS = {
    "programs": programs.scrape_programs,
    "courses": courses.scrape_courses,
    "labs": labs.scrape_labs,
    "groups": groups.scrape_groups,
    "professors": professors.scrape_professors,
}


@click.group()
def cli():
    """UNAM Engineering Schedule Scraper."""
    pass


@cli.command()
@click.option("--data-dir", default="data", help="Data directory")
@click.option("--verbose", is_flag=True, help="Enable debug logging")
def programs(data_dir, verbose):
    """Scrape academic programs."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    _run_scraper("programs", data_dir)


@cli.command()
@click.option("--data-dir", default="data", help="Data directory")
@click.option("--verbose", is_flag=True, help="Enable debug logging")
def courses(data_dir, verbose):
    """Scrape courses for all programs."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    _run_scraper("courses", data_dir)


@cli.command()
@click.option("--data-dir", default="data", help="Data directory")
@click.option("--verbose", is_flag=True, help="Enable debug logging")
def labs(data_dir, verbose):
    """Scrape laboratory course associations."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    _run_scraper("labs", data_dir)


@cli.command()
@click.option("--data-dir", default="data", help="Data directory")
@click.option("--verbose", is_flag=True, help="Enable debug logging")
def groups(data_dir, verbose):
    """Scrape course groups/sections."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    result = _run_scraper("groups", data_dir, return_result=True)

    logger.info("Linking professors with groups...")
    link_professors_groups(data_dir)

    sys.exit(0 if result.status == "success" else 1)


@cli.command()
@click.option("--data-dir", default="data", help="Data directory")
@click.option("--verbose", is_flag=True, help="Enable debug logging")
def professors(data_dir, verbose):
    """Scrape professor ratings."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    result = _run_scraper("professors", data_dir, return_result=True)

    logger.info("Linking professors with groups...")
    link_professors_groups(data_dir)

    sys.exit(0 if result.status == "success" else 1)


@cli.command()
@click.option("--data-dir", default="data", help="Data directory")
@click.option("--verbose", is_flag=True, help="Enable debug logging")
def all(data_dir, verbose):
    """Run all scrapers in sequence."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    order = ["programs", "courses", "labs", "groups", "professors", "link"]

    logger.info("Running all scrapers in sequence")

    results = {}
    for scraper_name in order:
        logger.info(f"Running {scraper_name}")

        if scraper_name == "link":
            success = link_professors_groups(data_dir)

            result = ScraperResult(
                scraper_name="link",
                status="success" if success else "failed",
                items_processed=0,
                execution_time=0.0,
                timestamp="",
                errors=[] if success else ["Linking failed"],
            )
        else:
            result = _run_scraper(scraper_name, data_dir, return_result=True)

        results[scraper_name] = result

        if result.status == "failed":
            logger.error(f"{scraper_name} failed: {result.errors}")
            logger.warning("Continuing with next step...")

    logger.info("EXECUTION SUMMARY")

    for name, result in results.items():
        status_icon = "✓" if result.status == "success" else "✗"
        logger.info(
            f"{status_icon} {name:12} | "
            f"Items: {result.items_processed:4} | "
            f"Time: {result.execution_time:6.2f}s | "
            f"Status: {result.status}"
        )

    total_items = sum(r.items_processed for r in results.values())
    total_time = sum(r.execution_time for r in results.values())

    logger.info(f"\nTotal: {total_items} items in {total_time:.2f}s")


def _run_scraper(name: str, data_dir: str, return_result: bool = False):
    """Run a single scraper."""
    try:
        http_client = HTTPClient()
        storage = DataStorage(data_dir)

        scraper_func = SCRAPERS.get(name)
        if not scraper_func:
            logger.error(f"Unknown scraper: {name}")
            sys.exit(1)

        result = scraper_func(http_client, storage)

        storage.update_metadata(result)

        if result.status == "success":
            logger.info(
                f"✓ {name} completed successfully: "
                f"{result.items_processed} items in {result.execution_time:.2f}s"
            )
        else:
            logger.error(f"✗ {name} failed: {result.errors}")

        stats = http_client.get_stats()
        logger.info(f"HTTP requests: {stats['total_requests']}")

        if return_result:
            return result

        sys.exit(0 if result.status == "success" else 1)

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
