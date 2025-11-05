"""
Entry point for running the scraper as a module.

Usage:
    python -m scraper.cli programs
"""

from .cli import cli

if __name__ == '__main__':
    cli()
