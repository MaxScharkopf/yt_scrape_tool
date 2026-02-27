"""Database initialization and all DB operations."""

import logging
import sqlite3
from datetime import datetime

from .config import DB_FILE

logger = logging.getLogger(__name__)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _parse_views(views_text: str) -> int | None:
    """Convert a views string like '1.2M views' or '45,123 views' to an integer."""
    if not views_text or views_text.strip() in ("N/A", "No views", ""):
        return None
    s = views_text.lower().replace("views", "").replace(",", "").strip()
    multipliers = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}
    for suffix, mult in multipliers.items():
        if s.endswith(suffix):
            try:
                return int(float(s[:-1]) * mult)
            except ValueError:
                return None
    try:
        return int(float(s))
    except ValueError:
        return None


# ─── Schema ───────────────────────────────────────────────────────────────────

def init_db() -> None:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id    TEXT,
            title       TEXT,
            channel     TEXT,
            duration    TEXT,
            views       TEXT,
            views_int   INTEGER,
            url         TEXT,
            query       TEXT,
            scraped_at  TEXT,
            UNIQUE(video_id, query)
        )
    """)
    # Migration: add views_int to existing databases that pre-date this column
    try:
        c.execute("ALTER TABLE videos ADD COLUMN views_int INTEGER")
        logger.info("DB migration: added views_int column.")
    except sqlite3.OperationalError:
        pass  # Column already exists

    c.execute("""
        CREATE TABLE IF NOT EXISTS tracked_queries (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            query   TEXT UNIQUE
        )
    """)

    # View snapshots table for trending detection
    c.execute("""
        CREATE TABLE IF NOT EXISTS view_snapshots (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id    TEXT NOT NULL,
            views_int   INTEGER,
            recorded_at TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_snapshots_video_recorded
        ON view_snapshots (video_id, recorded_at)
    """)

    conn.commit()
    conn.close()
    logger.debug("Database ready: %s", DB_FILE)


# ─── Videos ───────────────────────────────────────────────────────────────────

def save_results(results: list[dict], query: str) -> int:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_count = 0

    for r in results:
        views_int = _parse_views(r.get("views", ""))
        try:
            # Pre-fetch to detect new vs existing and compare views_int
            c.execute(
                "SELECT views_int FROM videos WHERE video_id = ? AND query = ?",
                (r["video_id"], query),
            )
            existing = c.fetchone()
            old_views_int = existing[0] if existing else None
            is_new = existing is None

            # UPSERT: insert new or update views on re-scrape
            c.execute("""
                INSERT INTO videos
                    (video_id, title, channel, duration, views, views_int, url, query, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(video_id, query) DO UPDATE SET
                    views      = excluded.views,
                    views_int  = excluded.views_int,
                    scraped_at = excluded.scraped_at
            """, (
                r["video_id"], r["title"], r["channel"], r["duration"],
                r["views"], views_int, r["url"], query, now,
            ))

            if is_new:
                new_count += 1

            # Record a snapshot when views_int is available and has changed
            if views_int is not None and (is_new or views_int != old_views_int):
                c.execute(
                    "INSERT INTO view_snapshots (video_id, views_int, recorded_at) VALUES (?, ?, ?)",
                    (r["video_id"], views_int, now),
                )
                logger.debug(
                    "Snapshot recorded for %s: %s → %s",
                    r["video_id"], old_views_int, views_int,
                )

        except Exception as e:
            logger.warning("Could not save '%s': %s", r.get("title"), e)
            print(f"  Warning: Could not save '{r.get('title')}': {e}")

    conn.commit()
    conn.close()
    logger.info("Saved %d new result(s) for query '%s'.", new_count, query)
    return new_count


# ─── Trending ─────────────────────────────────────────────────────────────────

def get_trending(limit: int = 20) -> list[dict]:
    """Return videos with the highest view growth between their two most recent snapshots."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        WITH ranked AS (
            SELECT
                video_id,
                views_int,
                recorded_at,
                ROW_NUMBER() OVER (
                    PARTITION BY video_id
                    ORDER BY recorded_at DESC
                ) AS rn
            FROM view_snapshots
        ),
        latest   AS (SELECT video_id, views_int AS latest_views FROM ranked WHERE rn = 1),
        previous AS (SELECT video_id, views_int AS prev_views   FROM ranked WHERE rn = 2)
        SELECT
            v.title,
            v.channel,
            v.query,
            v.url,
            l.latest_views,
            p.prev_views,
            (l.latest_views - p.prev_views) AS growth,
            ROUND(
                CAST(l.latest_views - p.prev_views AS REAL)
                / NULLIF(p.prev_views, 0) * 100,
                2
            ) AS growth_pct
        FROM latest l
        JOIN previous p USING (video_id)
        JOIN videos v ON v.video_id = l.video_id
        WHERE l.latest_views > p.prev_views
        ORDER BY growth DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    logger.debug("get_trending() returned %d row(s).", len(rows))
    return rows


# ─── Duplicates ───────────────────────────────────────────────────────────────

def get_duplicates() -> list[dict]:
    """Return videos that appear under more than one search query."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT
            video_id,
            MAX(title)                         AS title,
            MAX(channel)                        AS channel,
            MAX(views_int)                      AS views_int,
            MAX(views)                          AS views,
            COUNT(DISTINCT query)               AS query_count,
            GROUP_CONCAT(DISTINCT query)        AS queries,
            MAX(url)                            AS url
        FROM videos
        GROUP BY video_id
        HAVING COUNT(DISTINCT query) > 1
        ORDER BY query_count DESC, views_int DESC
    """)
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    logger.debug("get_duplicates() returned %d row(s).", len(rows))
    return rows


# ─── Tracked Queries ──────────────────────────────────────────────────────────

def add_tracked_query(query: str) -> bool:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO tracked_queries (query) VALUES (?)", (query,))
        conn.commit()
        logger.info("Added tracked query: '%s'", query)
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def remove_tracked_query(query: str) -> bool:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM tracked_queries WHERE query = ?", (query,))
    removed = c.rowcount > 0
    conn.commit()
    conn.close()
    if removed:
        logger.info("Removed tracked query: '%s'", query)
    return removed


def get_tracked_queries() -> list[str]:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT query FROM tracked_queries")
    queries = [row[0] for row in c.fetchall()]
    conn.close()
    return queries
