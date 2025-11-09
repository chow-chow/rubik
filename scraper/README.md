# UNAM FI Scraper

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](../LICENSE)

A robust web scraping system designed to collect academic data from UNAM's Faculty of Engineering, including study programs, courses, laboratories, course groups, and professor ratings.

> [!NOTE]
> This scraper is a core component of the **Rubik** project, leveraging GitHub Actions for automated data collection and using the repository itself as a data storage solution that can be consumed directly by the frontend application.

## Overview

The scraper collects and structures data from multiple UNAM sources and 3rd party sources:

- **Academic Programs**: Engineering programs with references to their study plans
- **Study Plans**: Detailed curriculum information with course organization by section
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
python -m scraper.cli all

# Run individual scrapers
python -m scraper.cli programs     # Scrape academic programs
python -m scraper.cli study_plans  # Scrape study plans with course organization
python -m scraper.cli courses      # Scrape courses for all programs
python -m scraper.cli labs         # Scrape laboratory associations
python -m scraper.cli groups       # Scrape course groups/sections
python -m scraper.cli professors   # Scrape professor ratings
```

> [!TIP]
> Use the `--verbose` flag during development to see detailed HTTP requests and parsing information.

## Data Output

The scraper outputs structured JSON data to the `data/` directory:

```bash
data/
├── metadata.json              # Execution metadata and timestamps
├── programs.json              # Academic programs index
├── study_plans.json           # Study plans with course organization
├── professor_ratings.json     # Professor ratings and evaluations
├── courses/                   # Courses by program
│   ├── 107.json              # Program code
│   └── ...
└── groups/                    # Groups by course
    ├── 1120.json             # Course code
    └── ...
```

### Data Architecture

The data is normalized across multiple files with clear relationships:

```
programs.json
    ↓ (study_plan_codes)
study_plans.json
    ↓ (courses: {required, elective, elective_humanities})
courses/*.json
    ↓ (code)
groups/*.json
```

**Execution Order**: `programs` → `study_plans` → `courses` → `labs` → `groups` → `professors`

1. **Programs** scraper extracts program metadata and study plan references
2. **Study Plans** scraper fetches detailed curriculum with course organization
3. **Courses** scraper collects unique courses from all study plans
4. **Labs** scraper associates laboratory courses
5. **Groups** scraper fetches schedules for each course
6. **Professors** scraper retrieves faculty ratings

### Data Models

<details>
<summary><b>Program</b></summary>

```json
{
  "code": "107",
  "name": "INGENIERIA CIVIL",
  "duration": 10,
  "study_plan_codes": ["2232", "4318", "4319"],
  "total_courses": 108
}
```

</details>

<details>
<summary><b>Study Plan</b></summary>

```json
{
  "code": "2232",
  "name": "ING CIVIL",
  "release_year": 2023,
  "required_credits": 413,
  "elective_credits": 36,
  "credit_limit_per_period": 60,
  "courses": {
    "required": ["1120", "1121", "1803"],
    "elective": ["0274", "2061"],
    "elective_humanities": ["1055", "1789"]
  }
}
```

</details>

<details>
<summary><b>Course</b></summary>

```json
{
  "code": "1120",
  "name": "ALGEBRA",
  "credits": 8,
  "total_groups": 57,
  "has_lab": false,
  "lab": null
}
```

> **Note**: The `section` field has been removed from courses. Section information (required, elective, elective_humanities) is now managed at the study plan level.

</details>

<details>
<summary><b>Group</b></summary>

```json
{
  "code": "1120",
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
  "full_name": "JUAN MARTINES GARCIA",
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
