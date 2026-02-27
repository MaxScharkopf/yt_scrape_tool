"""Export database contents to CSV."""

import csv
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

from .config import DB_FILE, EXPORT_DIR

logger = logging.getLogger(__name__)


def cmd_export(query: str | None = None) -> None:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if query:
        c.execute(
            "SELECT title, channel, duration, views, views_int, url, query, scraped_at "
            "FROM videos WHERE query = ? ORDER BY scraped_at DESC",
            (query,),
        )
        filename = f"youtube_{query.replace(' ', '_')}_{timestamp}.csv"
    else:
        c.execute(
            "SELECT title, channel, duration, views, views_int, url, query, scraped_at "
            "FROM videos ORDER BY scraped_at DESC"
        )
        filename = f"youtube_all_{timestamp}.csv"

    rows = c.fetchall()
    conn.close()

    if not rows:
        print("\n  No data found to export.\n")
        return

    out_path = Path(EXPORT_DIR) / filename
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Title", "Channel", "Duration", "Views", "Views (int)", "URL", "Query", "Scraped At"])
        writer.writerows(rows)

    print(f"\n✅ Exported {len(rows)} videos to: {out_path}")
    print("   Open it in Excel or Google Sheets!\n")
    logger.info("Exported %d row(s) to %s.", len(rows), out_path)
