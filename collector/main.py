"""
AI Daily Pulse - Data Collector Main Entry
Orchestrates RSS and Google News collection, outputs raw JSON.
"""

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from collector.sources.rss_feeds import fetch_rss_feeds
from collector.sources.google_news import fetch_google_news


def get_today_date():
    """Get today's date in Beijing time (UTC+8)."""
    beijing_tz = timezone(timedelta(hours=8))
    return datetime.now(beijing_tz).strftime("%Y-%m-%d")


def main():
    print("=" * 50)
    print("AI Daily Pulse - Data Collection")
    print("=" * 50)

    # Collect from all sources
    rss_articles = fetch_rss_feeds()
    google_articles = fetch_google_news()

    # Merge all articles
    all_articles = rss_articles + google_articles
    print(f"\nTotal articles collected: {len(all_articles)}")

    # Prepare output
    today = get_today_date()
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{today}.json"
    output_data = {
        "date": today,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "source_counts": {
            "rss": len(rss_articles),
            "google_news": len(google_articles),
        },
        "articles": all_articles,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\nRaw data saved to: {output_file}")
    return str(output_file)


if __name__ == "__main__":
    main()