"""YouTube search scraper using StealthyFetcher."""

import json
import logging
import re

from scrapling.fetchers import StealthyFetcher

logger = logging.getLogger(__name__)


def scrape_youtube(search_query: str) -> list[dict]:
    print(f"\n🔍 Searching YouTube for: '{search_query}'...")
    url = f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"
    logger.info("Fetching: %s", url)

    try:
        response = StealthyFetcher.fetch(url)
    except Exception as e:
        logger.error("Error fetching page: %s", e)
        print(f"  Error fetching page: {e}")
        return []

    match = re.search(r"var ytInitialData = ({.*?});", response.html_content)
    if not match:
        logger.warning("Could not find ytInitialData in response.")
        print("  Could not find video data in page.")
        return []

    data = json.loads(match.group(1))

    try:
        contents = (
            data["contents"]
                ["twoColumnSearchResultsRenderer"]
                ["primaryContents"]
                ["sectionListRenderer"]
                ["contents"]
        )
    except KeyError:
        logger.warning("Unexpected JSON structure in YouTube response.")
        print("  Could not navigate JSON structure.")
        return []

    all_videos = []
    for section in contents:
        if "itemSectionRenderer" in section:
            for item in section["itemSectionRenderer"]["contents"]:
                if "videoRenderer" in item:
                    all_videos.append(item)

    results = []
    for video in all_videos:
        v = video["videoRenderer"]
        try:
            results.append({
                "video_id": v["videoId"],
                "title":    v["title"]["runs"][0]["text"],
                "channel":  v["ownerText"]["runs"][0]["text"],
                "duration": v.get("lengthText", {}).get("simpleText", "N/A"),
                "views":    v.get("viewCountText", {}).get("simpleText", "N/A"),
                "url":      f"https://youtube.com/watch?v={v['videoId']}",
            })
        except (KeyError, IndexError):
            continue

    logger.info("Scraped %d video(s) for query '%s'.", len(results), search_query)
    return results
