"""YouTube Search Tool
-------------------
Commands:
  python3 main.py search "your query"       - Search YouTube and save results
  python3 main.py browse                    - Browse your saved database
  python3 main.py export                    - Export database to CSV
  python3 main.py export "query"            - Export a specific topic to CSV
  python3 main.py export-excel              - Export database to Excel (.xlsx)
  python3 main.py export-excel "query"      - Export a specific topic to Excel
  python3 main.py track "query"             - Add a query to daily tracking
  python3 main.py untrack "query"           - Remove a query from tracking
  python3 main.py tracked                   - List all tracked queries
  python3 main.py run-tracker               - Run the daily tracker once now
  python3 main.py start-scheduler           - Start auto-scraping every N hours
  python3 main.py trending                  - Show fastest-growing videos
  python3 main.py trending --limit 50       - Show top 50 trending videos
  python3 main.py duplicates                - Show videos appearing in multiple queries
  python3 main.py serve                     - Start web UI (default: http://127.0.0.1:5000)
  python3 main.py serve --port 8080         - Start web UI on a custom port
"""

import argparse

from yt_tool.config import WEB_HOST, WEB_PORT
from yt_tool.database import (
    add_tracked_query,
    get_tracked_queries,
    init_db,
    remove_tracked_query,
    save_results,
)
from yt_tool.display import cmd_browse, cmd_duplicates, cmd_trending, display_table
from yt_tool.exporter import cmd_export, cmd_export_excel
from yt_tool.logger import setup_logging
from yt_tool.scheduler import cmd_start_scheduler, run_tracker
from yt_tool.scraper import scrape_youtube
from yt_tool.web import run_web


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
    subparsers.add_parser("duplicates",      help="Show videos in multiple queries")

    p_search       = subparsers.add_parser("search",       help="Search YouTube")
    p_track        = subparsers.add_parser("track",        help="Add query to daily tracking")
    p_untrack      = subparsers.add_parser("untrack",      help="Remove query from tracking")
    p_export       = subparsers.add_parser("export",       help="Export database to CSV")
    p_export_excel = subparsers.add_parser("export-excel", help="Export database to Excel (.xlsx)")
    p_trending     = subparsers.add_parser("trending",     help="Show fastest-growing videos")
    p_serve        = subparsers.add_parser("serve",        help="Start web UI")

    p_search.add_argument("query",  type=str)
    p_track.add_argument("query",   type=str)
    p_untrack.add_argument("query", type=str)
    p_export.add_argument("query",       type=str, nargs="?", default=None, help="Optional: filter by topic")
    p_export_excel.add_argument("query", type=str, nargs="?", default=None, help="Optional: filter by topic")
    p_trending.add_argument("--limit",   type=int, default=20, help="Max results (default: 20)")
    p_serve.add_argument("--host", type=str, default=WEB_HOST, help=f"Host to bind (default: {WEB_HOST})")
    p_serve.add_argument("--port", type=int, default=WEB_PORT, help=f"Port to bind (default: {WEB_PORT})")

    args = parser.parse_args()

    dispatch = {
        "search":          lambda: cmd_search(args.query),
        "browse":          cmd_browse,
        "export":          lambda: cmd_export(args.query),
        "export-excel":    lambda: cmd_export_excel(args.query),
        "track":           lambda: cmd_track(args.query),
        "untrack":         lambda: cmd_untrack(args.query),
        "tracked":         cmd_tracked,
        "run-tracker":     run_tracker,
        "start-scheduler": cmd_start_scheduler,
        "trending":        lambda: cmd_trending(limit=args.limit),
        "duplicates":      cmd_duplicates,
        "serve":           lambda: run_web(host=args.host, port=args.port),
    }

    if args.command in dispatch:
        dispatch[args.command]()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
