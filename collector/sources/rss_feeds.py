"""
RSS Feed Collector
Parses configured RSS feeds and extracts articles published within the last 24 hours.
"""

import html
import re
import feedparser
import yaml
from datetime import datetime, timezone, timedelta
from dateutil import parser as dateparser
from pathlib import Path


def load_config():
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def strip_html(text):
    """Remove HTML tags and decode common entities."""
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'<[^>]*$', ' ', text)
    text = re.sub(r'https?://\S+', '', text)
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def is_within_24h(published_str):
    """Check if the published time is within the last 24 hours."""
    if not published_str:
        return False
    try:
        pub_time = dateparser.parse(published_str)
        if pub_time.tzinfo is None:
            pub_time = pub_time.replace(tzinfo=timezone.utc)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        return pub_time >= cutoff
    except (ValueError, TypeError):
        return False


def parse_published_time(entry):
    """Extract published time string from feed entry."""
    for field in ["published", "updated", "created"]:
        val = getattr(entry, field, None)
        if val:
            return val
    return None


def fetch_rss_feeds():
    """Fetch all configured RSS feeds and return articles from the last 24 hours."""
    config = load_config()
    articles = []

    for feed_cfg in config.get("rss_feeds", []):
        name = feed_cfg["name"]
        url = feed_cfg["url"]
        print(f"[RSS] Fetching: {name}")

        try:
            feed = feedparser.parse(url)
        except Exception as e:
            print(f"[RSS] Error fetching {name}: {e}")
            continue

        for entry in feed.entries:
            pub_str = parse_published_time(entry)
            if not is_within_24h(pub_str):
                continue

            try:
                pub_time = dateparser.parse(pub_str)
                if pub_time.tzinfo is None:
                    pub_time = pub_time.replace(tzinfo=timezone.utc)
                timestamp = pub_time.isoformat()
            except (ValueError, TypeError):
                timestamp = datetime.now(timezone.utc).isoformat()

            title = entry.get("title", "").strip()
            summary = strip_html(entry.get("summary", entry.get("description", "")))
            if not summary:
                summary = title
            if len(summary) > 300:
                summary = summary[:297] + "..."

            link = entry.get("link", "")

            articles.append({
                "title": title,
                "summary": summary,
                "url": link,
                "source": name,
                "timestamp": timestamp,
            })

    print(f"[RSS] Collected {len(articles)} articles from RSS feeds")
    return articles


if __name__ == "__main__":
    results = fetch_rss_feeds()
    for r in results[:5]:
        print(f"  - {r['source']}: {r['title']}")