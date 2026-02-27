"""Scheduler for periodic scraping of tracked queries."""

import logging
import time
from datetime import datetime

import schedule

from .config import SCHEDULER_INTERVAL_HOURS
from .database import get_tracked_queries, save_results
from .scraper import scrape_youtube

logger = logging.getLogger(__name__)


def run_tracker() -> None:
    queries = get_tracked_queries()
    if not queries:
        print('\n  No tracked queries. Add one with: python3 main.py track "query"\n')
        return

    print(f"\n⏱  Running tracker for {len(queries)} queries at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("Tracker started for %d query/queries.", len(queries))

    for query in queries:
        results = scrape_youtube(query)
        if results:
            new = save_results(results, query)
            print(f"  '{query}' → {len(results)} results, {new} new saved")

    print("  ✅ Tracker run complete.\n")
    logger.info("Tracker run complete.")


def cmd_start_scheduler() -> None:
    print(f"\n🕐 Scheduler started — scraping tracked queries every {SCHEDULER_INTERVAL_HOURS} hours.")
    print("   Press Ctrl+C to stop.\n")
    logger.info("Scheduler starting (interval: %d hours).", SCHEDULER_INTERVAL_HOURS)

    run_tracker()
    schedule.every(SCHEDULER_INTERVAL_HOURS).hours.do(run_tracker)

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n  Scheduler stopped.\n")
        logger.info("Scheduler stopped by user.")
