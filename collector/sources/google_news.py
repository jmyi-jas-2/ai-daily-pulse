"""
Google News RSS Collector
Searches Google News RSS for configured keywords and extracts articles on target Beijing date.
"""

import html
import re
import feedparser
import yaml
import time
from datetime import datetime, timezone, timedelta
from dateutil import parser as dateparser
from pathlib import Path
from urllib.parse import quote


def load_config():
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


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

def strip_html(text):
    """Remove all HTML tags, entities, and URLs, return clean text."""
    if not text:
        return ""
    text = html.unescape(text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'<[^>]*$', ' ', text)
    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def build_google_news_url(keyword, language="en"):
    """Build Google News RSS search URL."""
    encoded_kw = quote(keyword)
    if language == "zh":
        return (
            f"https://news.google.com/rss/search?"
            f"q={encoded_kw}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
        )
    else:
        return (
            f"https://news.google.com/rss/search?"
            f"q={encoded_kw}&hl=en&gl=US&ceid=US:en"
        )


def fetch_google_news(target_date_str=None):
    """Fetch Google News for all configured keywords on target Beijing date."""
    config = load_config()
    keywords_config = config.get("google_news_keywords", {})
    articles = []
    seen_urls = set()
    if target_date_str is None:
        beijing_tz = timezone(timedelta(hours=8))
        target_date_str = (datetime.now(beijing_tz) - timedelta(days=1)).strftime("%Y-%m-%d")

    for lang, keywords in keywords_config.items():
        for keyword in keywords:
            url = build_google_news_url(keyword, lang)
            print(f"[Google News] Searching: {keyword} ({lang})")

            try:
                feed = feedparser.parse(url)
            except Exception as e:
                print(f"[Google News] Error for '{keyword}': {e}")
                continue

            for entry in feed.entries:
                link = entry.get("link", "")
                if link in seen_urls:
                    continue
                seen_urls.add(link)

                pub_str = entry.get("published", entry.get("updated", ""))
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
                source_name = "Google News"
                if " - " in title:
                    parts = title.rsplit(" - ", 1)
                    title = parts[0].strip()
                    source_name = parts[1].strip()

                summary = strip_html(entry.get("summary", entry.get("description", "")))
                if not summary:
                    summary = title
                if len(summary) > 300:
                    summary = summary[:297] + "..."

                articles.append({
                    "title": title,
                    "summary": summary,
                    "url": link,
                    "source": source_name,
                    "timestamp": timestamp,
                    "search_keyword": keyword,
                })

            # Polite delay between requests
            time.sleep(1)

    print(f"[Google News] Collected {len(articles)} articles on {target_date_str}")
    return articles


if __name__ == "__main__":
    results = fetch_google_news()
    for r in results[:5]:
        print(f"  - {r['source']}: {r['title']}")