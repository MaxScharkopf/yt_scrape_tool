"""Terminal display and interactive database browser."""

import logging
import sqlite3

from tabulate import tabulate

from .config import DB_FILE

logger = logging.getLogger(__name__)


def display_table(results: list[dict]) -> None:
    if not results:
        print("  No results to display.")
        return
    rows = [
        [i, (r["title"][:55] + "...") if len(r["title"]) > 55 else r["title"],
         r["channel"], r["duration"], r["views"]]
        for i, r in enumerate(results, 1)
    ]
    print("\n" + tabulate(
        rows,
        headers=["#", "Title", "Channel", "Duration", "Views"],
        tablefmt="rounded_outline",
    ))


def cmd_browse() -> None:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    print("\n📂 Browse Options:")
    print("  1. All saved videos")
    print("  2. Search by keyword")
    print("  3. Filter by query topic")
    choice = input("\nChoose (1/2/3): ").strip()

    if choice == "1":
        c.execute(
            "SELECT title, channel, duration, views, query, scraped_at "
            "FROM videos ORDER BY scraped_at DESC LIMIT 100"
        )
        rows = c.fetchall()
        print(f"\n{tabulate(rows, headers=['Title','Channel','Duration','Views','Query','Scraped At'], tablefmt='rounded_outline', maxcolwidths=[40,20,10,15,20,20])}")
        logger.info("Browsed all videos (%d shown).", len(rows))

    elif choice == "2":
        keyword = input("Enter keyword to search titles: ").strip()
        c.execute(
            "SELECT title, channel, duration, views, url FROM videos "
            "WHERE title LIKE ? ORDER BY scraped_at DESC",
            (f"%{keyword}%",),
        )
        rows = c.fetchall()
        if rows:
            print(f"\n{tabulate(rows, headers=['Title','Channel','Duration','Views','URL'], tablefmt='rounded_outline', maxcolwidths=[40,20,10,15,50])}")
            print(f"\n  Found {len(rows)} matching videos")
        else:
            print(f"  No videos found matching '{keyword}'")
        logger.info("Keyword search '%s': %d result(s).", keyword, len(rows))

    elif choice == "3":
        c.execute("SELECT DISTINCT query FROM videos")
        queries = [row[0] for row in c.fetchall()]
        if not queries:
            print("  No data yet.")
            conn.close()
            return
        print("\nAvailable topics:")
        for i, q in enumerate(queries, 1):
            print(f"  {i}. {q}")
        idx = input("\nChoose topic number: ").strip()
        try:
            chosen = queries[int(idx) - 1]
            c.execute(
                "SELECT title, channel, duration, views, url FROM videos "
                "WHERE query = ? ORDER BY scraped_at DESC",
                (chosen,),
            )
            rows = c.fetchall()
            print(f"\n{tabulate(rows, headers=['Title','Channel','Duration','Views','URL'], tablefmt='rounded_outline', maxcolwidths=[40,20,10,15,50])}")
            logger.info("Browse by topic '%s': %d result(s).", chosen, len(rows))
        except (ValueError, IndexError):
            print("  Invalid selection.")

    conn.close()
