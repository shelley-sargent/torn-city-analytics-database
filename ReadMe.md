<a id="readme-top"></a>

<div align="center">
<h3 align="center">Torn City Statistics Collector</h3>

  <p align="center">
    A Python-based data pipeline that collects Torn City faction data (members and attacks) via the REST API and saves snapshots into a PostgreSQL database for historical analysis.
    <br />
    <a href="https://github.com/shelley-sargent/api-to-postgres-project/"><strong>Explore the docs »</strong></a>
    <br />
  </p>
</div>

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#project-structure">Project Structure</a></li>
    <li><a href="#scripts-and-entry-points">Scripts and Entry Points</a></li>
    <li><a href="#environment-variables">Environment Variables</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>

## About The Project

This project implements a repeatable data pipeline designed to run on a schedule (e.g., Raspberry Pi via cron) to track faction performance in Torn City.

### Key Features
- **API Extraction:** Pulls data from Torn City REST API (v2).
- **Data Normalization:** Cleans IDs, timestamps, and numeric types using `pandas` and `numpy`.
- **Enrichment:** Merges participant-level statistics with event/attack records.
- **Database Storage:** Upserts data into PostgreSQL (Supabase) with `psycopg2`.
- **Snapshotting:** Captures daily snapshots of player stats for time-series analysis.

### Project Goal
Originally designed as the data foundation for a predictive modeling system. Collected data can be used for unsupervised learning (K-means clustering) to identify performance patterns and estimate conflict outcomes.

### Architecture
```text
Torn API (v2) 
      ↓
[api.py] (Wrapper)
      ↓
[attacks.py / players.py] (Transformation & Merge)
      ↓
[six_hours.py / one_hour.py] (DB Upsert)
      ↓
PostgreSQL (Supabase)
```

### Built With
* [Python 3.10+](https://www.python.org/)
* [pandas](https://pandas.pydata.org/)
* [PostgreSQL](https://www.postgresql.org/)
* [psycopg2-binary](https://www.psycopg.org/)
* [requests](https://requests.readthedocs.io/)
* [python-dotenv](https://github.com/theskumar/python-dotenv)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Getting Started

### Prerequisites
- Python 3.10 or higher.
- A PostgreSQL database (e.g., [Supabase](https://supabase.com/)).
- Torn City API key(s).

### Installation
1. Clone the repo:
   ```sh
   git clone https://github.com/shelley-sargent/api-to-postgres-project.git
   ```
2. Create and activate a virtual environment (recommended):
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
4. Set up your `.env` file (see [Environment Variables](#environment-variables)).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Project Structure
```text
.
├── api.py           # Core Torn API wrapper (handles rotation of keys)
├── attacks.py       # Data processing logic for faction attacks
├── players.py       # Data processing logic for member statistics
├── six_hours.py     # Entry point for uploading attacks (intended for cron every 6h)
├── one_hour.py      # Entry point for uploading player stats (intended for cron every 1h)
├── requirements.txt # Python dependencies
├── .env             # Environment configuration (not in source control)
└── ReadMe.md        # This file
```

## Scripts and Entry Points

### `six_hours.py`
The primary entry point for collecting faction attack data. 
- Imports processed attack data from `attacks.py`.
- Connects to the database and performs a bulk upsert into the `attacks` table.
- Uses `COALESCE` to ensure existing data is preserved during partial updates.
- **Run manually:** `python six_hours.py`

### `one_hour.py`
Collects and uploads frequently changing individual player stats.
- **Run manually:** `python one_hour.py`

### `api.py`
A helper module providing a `get()` function to interact with Torn API v2. It includes support for rotating multiple API keys from the `.env` file.

### `attacks.py` & `players.py`
These modules contain the logic for data cleaning, transformation, and merging using `pandas`. They are imported by the entry point scripts.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Environment Variables
Create a `.env` file in the root directory with the following variables:

| Variable | Description |
| :--- | :--- |
| `API_KEYS` | A JSON-formatted string of API keys: `{"KEY": "NAME"}` |
| `DB_HOST` | Database host address |
| `DB_NAME` | Database name |
| `DB_USER` | Database username |
| `DB_PASSWORD` | Database password |
| `DB_PORT` | Database port (default: 5432) |

## Scheduling (Cron)
To run this automatically on a Linux/Raspberry Pi system, you can add entries to your crontab (`crontab -e`):

```cron
# Example (TODO: Adjust paths to your local environment)
0 */6 * * * /path/to/venv/bin/python /path/to/project/six_hours.py >> /path/to/logs/attacks.log 2>&1
0 * * * * /path/to/venv/bin/python /path/to/project/one_hour.py >> /path/to/logs/players.log 2>&1
```

## Tests
Currently, there is no formal test suite. 
- **TODO:** Implement unit tests for API parsing and data transformation logic.
- Basic functional tests are present as commented-out sections in `api.py` and `attacks.py`.

## License
Distributed under the MIT License. (TODO: Verify license or add `LICENSE` file).

## Contact
Project Link: [https://github.com/shelley-sargent/api-to-postgres-project/](https://github.com/shelley-sargent/api-to-postgres-project/)

<p align="right">(<a href="#readme-top">back to top</a>)</p>
