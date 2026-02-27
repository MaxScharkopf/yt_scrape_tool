"""YouTube Search Tool
-------------------
Commands:
  python3 main.py search "your query"       - Search YouTube and save results
  python3 main.py browse                    - Browse your saved database
  python3 main.py export                    - Export database to CSV
  python3 main.py export "query"            - Export a specific topic to CSV
  python3 main.py track "query"             - Add a query to daily tracking
  python3 main.py untrack "query"           - Remove a query from tracking
  python3 main.py tracked                   - List all tracked queries
  python3 main.py run-tracker               - Run the daily tracker once now
  python3 main.py start-scheduler           - Start auto-scraping every N hours
"""

import argparse

from yt_tool.logger import setup_logging
from yt_tool.database import init_db, save_results, add_tracked_query, remove_tracked_query, get_tracked_queries
from yt_tool.scraper import scrape_youtube
from yt_tool.display import display_table, cmd_browse
from yt_tool.exporter import cmd_export
from yt_tool.scheduler import run_tracker, cmd_start_scheduler


# ─── Commands ─────────────────────────────────────────────────────────────────

def cmd_search(query: str) -> None:
    results = scrape_youtube(query)
    if not results:
        return
    display_table(results)
    new = save_results(results, query)
    print(f"\n✅ {len(results)} results shown | {new} new videos saved to database\n")


def cmd_track(query: str) -> None:
    if add_tracked_query(query):
        print(f"\n✅ Now tracking: '{query}'")
        print("   Run 'python3 main.py start-scheduler' to auto-scrape daily.\n")
    else:
        print(f"\n  Already tracking: '{query}'\n")


def cmd_untrack(query: str) -> None:
    if remove_tracked_query(query):
        print(f"\n✅ Removed '{query}' from tracking.\n")
    else:
        print(f"\n  '{query}' was not in your tracked list.\n")


def cmd_tracked() -> None:
    queries = get_tracked_queries()
    if not queries:
        print('\n  No tracked queries yet. Use: python3 main.py track "your query"\n')
    else:
        print("\n📋 Tracked Queries:")
        for i, q in enumerate(queries, 1):
            print(f"  {i}. {q}")
        print()


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    setup_logging()
    init_db()

    parser = argparse.ArgumentParser(description="YouTube Search & Tracking Tool")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("browse",          help="Browse saved database")
    subparsers.add_parser("tracked",         help="List tracked queries")
    subparsers.add_parser("run-tracker",     help="Run tracker now")
    subparsers.add_parser("start-scheduler", help="Auto-scrape every N hours")

    p_search  = subparsers.add_parser("search",  help="Search YouTube")
    p_track   = subparsers.add_parser("track",   help="Add query to daily tracking")
    p_untrack = subparsers.add_parser("untrack", help="Remove query from tracking")
    p_export  = subparsers.add_parser("export",  help="Export database to CSV")

    p_search.add_argument("query",  type=str)
    p_track.add_argument("query",   type=str)
    p_untrack.add_argument("query", type=str)
    p_export.add_argument("query",  type=str, nargs="?", default=None, help="Optional: filter by topic")

    args = parser.parse_args()

    dispatch = {
        "search":          lambda: cmd_search(args.query),
        "browse":          cmd_browse,
        "export":          lambda: cmd_export(args.query),
        "track":           lambda: cmd_track(args.query),
        "untrack":         lambda: cmd_untrack(args.query),
        "tracked":         cmd_tracked,
        "run-tracker":     run_tracker,
        "start-scheduler": cmd_start_scheduler,
    }

    if args.command in dispatch:
        dispatch[args.command]()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
