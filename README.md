# YouTube Scrape Tool

A YouTube search scraping and tracking tool built with [Scrapling](https://github.com/D4Vinci/Scrapling). Search YouTube, save results to a local SQLite database, export to CSV, and automatically track topics on a daily schedule.

## Requirements

- Python 3.12+
- A virtual environment (recommended)

Install dependencies:

```bash
pip install scrapling tabulate schedule
pip install "scrapling[fetchers]"
scrapling install
```

> **Note:** `scrapling install` may prompt for your sudo password on Linux — this is normal.

## Setup

1. Activate your virtual environment:

```bash
cd ~/Desktop
source venv/bin/activate
```

2. Run any command — the database and log file are created automatically on first run.

## Usage

```
python3 main.py <command> [args]
```

| Command | Description |
|---|---|
| `search "query"` | Search YouTube and save results to the database |
| `browse` | Browse the saved database interactively |
| `export` | Export all saved videos to a CSV file |
| `export "query"` | Export only videos matching a specific topic |
| `track "query"` | Add a query to the daily auto-tracking list |
| `untrack "query"` | Remove a query from the tracking list |
| `tracked` | Show all currently tracked queries |
| `run-tracker` | Manually run the tracker for all tracked queries now |
| `start-scheduler` | Start the scheduler — scrapes all tracked queries on interval |

> `yt_tool.py` still works as a backwards-compatible entry point.

## Examples

**Search YouTube:**
```bash
python3 main.py search "machine learning"
```

**Export to CSV:**
```bash
python3 main.py export
python3 main.py export "AI news"
```
Saves a timestamped CSV to the project directory. Open in Excel or Google Sheets.

**Daily trend tracking:**
```bash
python3 main.py track "AI news"
python3 main.py track "computer vision"
python3 main.py start-scheduler
```
The scheduler runs in the foreground and scrapes all tracked queries at the configured interval. Press `Ctrl+C` to stop. For persistence, run inside a `tmux` or `screen` session.

**Browse the database:**
```bash
python3 main.py browse
```
Choose from: all saved videos, keyword search, or filter by topic.

## Configuration

Edit `config.toml` to customize behaviour:

```toml
db_file                  = "youtube_data.db"
log_file                 = "logs/yt_tool.log"
log_level                = "INFO"
scheduler_interval_hours = 24
export_dir               = "."
```

## Project Structure

```
yt_scrape_tool/
├── config.toml        # Runtime configuration
├── main.py            # Entry point
├── yt_tool.py         # Backwards-compatible shim
└── yt_tool/
    ├── config.py      # Loads config.toml, resolves paths
    ├── logger.py      # File + console logging
    ├── database.py    # DB init, migration, queries
    ├── scraper.py     # YouTube scraping logic
    ├── display.py     # Terminal output and browser
    ├── exporter.py    # CSV export
    └── scheduler.py   # Scheduled tracking
```

## Database

All data is stored in `youtube_data.db` (SQLite). Access options:

- Export via `python3 main.py export`
- GUI: `sudo apt install sqlitebrowser`
- Terminal: `sqlite3 youtube_data.db`

**`videos` table columns:**
`id`, `video_id`, `title`, `channel`, `duration`, `views`, `views_int`, `url`, `query`, `scraped_at`

> `views_int` stores the parsed integer value of the views string (e.g. `"1.2M views"` → `1200000`), useful for sorting and filtering.

**`tracked_queries` table columns:**
`id`, `query`

## Notes

- YouTube's internal JSON structure can change — if results stop appearing, the scraper's JSON path may need updating.
- Duplicate videos for the same query are automatically skipped on re-scrape.

---

Built with [Scrapling](https://github.com/D4Vinci/Scrapling) · SQLite · Python 3
