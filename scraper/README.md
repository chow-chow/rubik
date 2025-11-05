# UNAM FI Scraper

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](../LICENSE)

A robust web scraping system designed to collect academic data from UNAM's Faculty of Engineering, including study programs, courses, laboratories, course groups, and professor ratings.

> [!NOTE]
> This scraper is a core component of the **Rubik** project, leveraging GitHub Actions for automated data collection and using the repository itself as a data storage solution that can be consumed directly by the frontend application.

## Overview

The scraper collects and structures data from multiple UNAM sources and 3rd party sources:

- **Academic Programs**: Engineering programs and their curricula
- **Courses**: Course information, credits, and laboratory associations
- **Groups**: Course sections with schedules and professor assignments
- **Professor Ratings**: Faculty evaluations from external platforms

## Key Features

- **Modular Design**: Independent scrapers for each data type with shared HTTP client
- Automatic retries, rate limiting, atomic file writes, and comprehensive logging
- **CLI Interface**: Simple commands to run individual or all scrapers in sequence
- **GitHub Actions Integration**: Designed to run as scheduled workflows for automated data updates
- **Repository as Database**: Scraped data is committed to the repository, making it instantly available via GitHub's CDN

## Quick Start

### Prerequisites

- Python 3.10
- pip

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd rubik/scraper

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# Run all scrapers in sequence
python -m scraper all

# Run individual scrapers
python -m scraper programs   # Scrape academic programs
python -m scraper courses    # Scrape courses for all programs
python -m scraper labs       # Scrape laboratory associations
python -m scraper groups     # Scrape course groups/sections
python -m scraper professors # Scrape professor ratings
```

> [!TIP]
> Use the `--verbose` flag during development to see detailed HTTP requests and parsing information.

## Data Output

The scraper outputs structured JSON data to the `data/` directory:

```bash
data/
├── metadata.json              # Execution metadata and timestamps
├── programs.json              # Academic programs index
├── professor_ratings.json     # Professor ratings and evaluations
├── courses/                   # Courses by program
│   ├── 1114.json             # Program code
│   └── ...
└── groups/                    # Groups by course
    ├── 1124.json             # Course code
    └── ...
```

### Data Models

<details>
<summary><b>Program</b></summary>

```json
{
  "code": "1114",
  "name": "Ingeniería Civil",
  "release_year": 2016,
  "duration": 9,
  "total_courses": 58
}
```

</details>

<details>
<summary><b>Course</b></summary>

```json
{
  "code": "1124",
  "name": "Álgebra",
  "credits": 10,
  "section": "core",
  "total_groups": 12,
  "has_lab": false,
  "lab": null
}
```

</details>

<details>
<summary><b>Group</b></summary>

```json
{
  "code": "1124",
  "group": "01",
  "professor": "MARTÍNEZ GARCÍA JUAN",
  "professor_id": 12345,
  "schedules": [
    {
      "day": "Lunes",
      "start": "07:00",
      "end": "09:00",
      "location": "Aula 301"
    }
  ]
}
```

</details>

<details>
<summary><b>Professor</b></summary>

```json
{
  "id": 12345,
  "full_name": "Juan Martínez García",
  "first_name": "Juan",
  "last_name": "Martínez García",
  "num_ratings": 156,
  "rating": 4.5
}
```

</details>

## Configuration

Configuration is centralized in `config.py`:

| Parameter     | Default    | Description                                        |
| ------------- | ---------- | -------------------------------------------------- |
| `MAX_RETRIES` | 3          | Number of retry attempts for failed requests       |
| `TIMEOUT`     | 30         | Request timeout in seconds                         |
| `DELAY_RANGE` | (0.5, 1.5) | Random delay between requests (rate limiting)      |
| `MAX_WORKERS` | 5          | Maximum concurrent workers for parallel processing |

> [!WARNING]
> Modifying `DELAY_RANGE` to very low values may result in rate limiting or IP bans. Always be respectful of source servers.

## Development

### Adding a New Scraper

1. **Create Parser**: Add parsing logic in `parsers/new_scraper.py`
2. **Create Scraper**: Implement scraper in `scrapers/new_scraper.py`
3. **Register**: Add to `SCRAPERS` dictionary in `cli.py`
4. **Add Command**: Create CLI command in `cli.py` (optional)

## Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/your-feature`)
3. **Commit** your changes (`git commit -m 'feat: add your feature'`)
4. **Push** to the branch (`git push origin feature/your-feature`)
5. **Open** a Pull Request

### Commit Convention

[Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

> [!NOTE]
> This scraper is designed for educational and research purposes. Please respect the terms of service of the scraped websites and use the data responsibly.
