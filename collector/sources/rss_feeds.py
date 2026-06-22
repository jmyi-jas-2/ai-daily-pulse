"""
RSS Feed Collector
Parses configured RSS feeds and extracts articles published on target Beijing date.
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

def is_on_target_beijing_date(published_str, target_date_str):
    """Check if publish time falls on target date in Beijing timezone."""
    if not published_str:
        return False
    try:
        pub_time = dateparser.parse(published_str)
        if pub_time.tzinfo is None:
            pub_time = pub_time.replace(tzinfo=timezone.utc)
        beijing_tz = timezone(timedelta(hours=8))
        beijing_date = pub_time.astimezone(beijing_tz).strftime("%Y-%m-%d")
        return beijing_date == target_date_str
    except (ValueError, TypeError):
        return False


def parse_published_time(entry):
    """Extract published time string from feed entry."""
    for field in ["published", "updated", "created"]:
        val = getattr(entry, field, None)
        if val:
            return val
    return None


def fetch_rss_feeds(target_date_str=None):
    """Fetch all configured RSS feeds and return articles on target Beijing date."""
    config = load_config()
    articles = []
    if target_date_str is None:
        beijing_tz = timezone(timedelta(hours=8))
        target_date_str = (datetime.now(beijing_tz) - timedelta(days=1)).strftime("%Y-%m-%d")

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
            if not is_on_target_beijing_date(pub_str, target_date_str):
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
                "source_type": "rss",
                "timestamp": timestamp,
            })

    print(f"[RSS] Collected {len(articles)} articles from RSS feeds on {target_date_str}")
    return articles


if __name__ == "__main__":
    results = fetch_rss_feeds()
    for r in results[:5]:
        print(f"  - {r['source']}: {r['title']}")