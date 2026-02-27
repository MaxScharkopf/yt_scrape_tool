"""Flask web UI for browsing the yt_scrape_tool database."""

import csv
import io
import logging
import sqlite3

from flask import Flask, render_template, request, send_file

from .config import DB_FILE, WEB_HOST, WEB_PORT
from .database import get_duplicates, get_trending

logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder="templates")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _db_stats() -> dict:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    total_videos  = c.execute("SELECT COUNT(*) FROM videos").fetchone()[0]
    total_queries = c.execute("SELECT COUNT(DISTINCT query) FROM videos").fetchone()[0]
    tracked       = c.execute("SELECT COUNT(*) FROM tracked_queries").fetchone()[0]
    snapshots     = c.execute("SELECT COUNT(*) FROM view_snapshots").fetchone()[0]
    conn.close()
    return {
        "total_videos":  total_videos,
        "total_queries": total_queries,
        "tracked":       tracked,
        "snapshots":     snapshots,
    }


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    stats = _db_stats()
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(
        "SELECT title, channel, views, query, scraped_at, url "
        "FROM videos ORDER BY scraped_at DESC LIMIT 10"
    )
    recent = [dict(row) for row in c.fetchall()]
    conn.close()
    return render_template("index.html", stats=stats, recent=recent)


@app.route("/browse")
def browse():
    keyword      = request.args.get("q", "").strip()
    query_filter = request.args.get("query", "").strip()

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT DISTINCT query FROM videos ORDER BY query")
    all_queries = [row[0] for row in c.fetchall()]

    sql    = "SELECT title, channel, duration, views, views_int, url, query, scraped_at FROM videos WHERE 1=1"
    params: list = []
    if keyword:
        sql += " AND title LIKE ?"
        params.append(f"%{keyword}%")
    if query_filter:
        sql += " AND query = ?"
        params.append(query_filter)
    sql += " ORDER BY scraped_at DESC LIMIT 500"

    c.execute(sql, params)
    videos = [dict(row) for row in c.fetchall()]
    conn.close()

    return render_template(
        "browse.html",
        videos=videos,
        keyword=keyword,
        query_filter=query_filter,
        all_queries=all_queries,
    )


@app.route("/trending")
def trending():
    limit = int(request.args.get("limit", 20))
    rows  = get_trending(limit=limit)
    return render_template("trending.html", rows=rows, limit=limit)


@app.route("/duplicates")
def duplicates():
    rows = get_duplicates()
    return render_template("duplicates.html", rows=rows)


@app.route("/export")
def export():
    """Stream a CSV download directly from the browser."""
    query_filter = request.args.get("query", None) or None

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if query_filter:
        c.execute(
            "SELECT title, channel, duration, views, views_int, url, query, scraped_at "
            "FROM videos WHERE query = ? ORDER BY scraped_at DESC",
            (query_filter,),
        )
        filename = f"youtube_{query_filter.replace(' ', '_')}.csv"
    else:
        c.execute(
            "SELECT title, channel, duration, views, views_int, url, query, scraped_at "
            "FROM videos ORDER BY scraped_at DESC"
        )
        filename = "youtube_all.csv"

    rows = c.fetchall()
    conn.close()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Title", "Channel", "Duration", "Views", "Views (int)", "URL", "Query", "Scraped At"])
    writer.writerows(rows)
    buf.seek(0)

    return send_file(
        io.BytesIO(buf.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=filename,
    )


# ─── Entry Point ──────────────────────────────────────────────────────────────

def run_web(host: str = WEB_HOST, port: int = WEB_PORT) -> None:
    logger.info("Starting web UI on %s:%d", host, port)
    print(f"\n  Web UI running at http://{host}:{port}")
    print("  Press Ctrl+C to stop.\n")
    app.run(host=host, port=port, debug=False)
