"""
AI Daily Pulse - Processing Pipeline
Deduplicates, classifies, scores, and outputs final structured JSON.
"""

import html
import json
import math
import re
import sys
import hashlib
import yaml
from difflib import SequenceMatcher
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def load_config():
    config_path = Path(__file__).parent.parent / "collector" / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def generate_id(title):
    """Generate a short deterministic ID from title."""
    h = hashlib.md5(title.encode("utf-8")).hexdigest()[:8]
    return f"evt_{h}"


def clean_text(text):
    """Convert feed HTML into plain display text."""
    if not text:
        return ""
    text = html.unescape(str(text))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"<[^>]*$", " ", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


SOURCE_SUFFIX_RE = re.compile(
    r"(?:[_-]\s*)?(?:新浪新闻|新浪财经|搜狐网|凤凰网|驱动之家|aastocks\.com|investing\.com|financial news)$",
    re.IGNORECASE,
)

STOPWORDS = {
    "ai", "and", "the", "a", "an", "of", "to", "in", "on", "for", "with", "at", "by",
    "from", "about", "after", "before", "new", "latest", "news", "says", "said",
    "消息", "据报", "媒体", "新闻", "财经", "提供者", "正式", "首个", "具身", "智能",
}

ENTITY_ALIASES = {
    "openai": ["openai", "chatgpt", "gpt"],
    "anthropic": ["anthropic", "claude"],
    "deepseek": ["deepseek", "深度求索"],
    "qwen": ["qwen", "qwen-robot", "通义千问", "千问"],
    "alibaba": ["alibaba", "阿里", "阿里巴巴", "支付宝"],
    "google": ["google", "gemini", "deepmind", "谷歌"],
    "meta": ["meta", "facebook", "llama"],
    "zhipu": ["智谱", "glm"],
    "bytedance": ["字节", "豆包", "doubao"],
    "moonshot": ["moonshot", "kimi", "月之暗面"],
}

TOPIC_BUCKETS = {
    "funding": [
        "funding", "fundraise", "fundraising", "financing", "raises", "raised", "round",
        "valuation", "invest", "investment", "ipo", "融资", "募资", "估值", "首轮", "入股", "出资",
    ],
    "release": [
        "launch", "release", "announce", "announces", "introduced", "introduce", "unveil",
        "roll out", "发布", "上线", "推出", "开源", "发布会", "正式发布",
    ],
    "regulation": ["ban", "order", "regulation", "policy", "监管", "禁令", "合规", "立法", "下线"],
    "incident": ["outage", "downtime", "incident", "degraded", "故障", "降级", "宕机", "泄露", "中断"],
    "partnership": ["partnership", "partner", "collaboration", "合作", "协同", "战略合作"],
}

OFFICIAL_RSS_SOURCES = {
    "OpenAI Blog",
    "Anthropic Blog",
    "Google DeepMind Blog",
    "Meta AI Blog",
    "Mistral Blog",
    "DeepSeek Blog",
}

HIGH_QUALITY_RSS_SOURCES = {
    "TechCrunch AI",
    "The Verge AI",
    "Ars Technica",
    "36Kr",
    "机器之心",
}

REPUTABLE_NEWS_SOURCES = {
    "Reuters",
    "Bloomberg",
    "The Information",
    "Financial Times",
    "Wall Street Journal",
    "CNBC",
    "Forbes",
    "Wired",
    "MIT Technology Review",
    "VentureBeat",
    "ZDNET",
    "The Register",
}

LOW_QUALITY_NEWS_SOURCES = {
    "Startup Fortune",
    "Let's Data Science",
    "ShiaWaves",
}

EVENT_TYPE_WEIGHTS = {
    "incident": 1.0,
    "regulation": 1.0,
    "model": 0.9,
    "business": 0.75,
    "statement": 0.6,
}

AI_RELEVANCE_KEYWORDS = {
    "ai",
    "artificial intelligence",
    "machine learning",
    "llm",
    "model",
    "chatbot",
    "openai",
    "anthropic",
    "chatgpt",
    "gpt",
    "deepseek",
    "gemini",
    "deepmind",
    "meta ai",
    "llama",
    "qwen",
    "kimi",
    "moonshot",
    "doubao",
    "智谱",
    "通义",
    "千问",
    "豆包",
    "文心",
    "模型",
    "人工智能",
    "大模型",
    "智能体",
    "具身智能",
}


def normalize_title(title):
    """Normalize noisy feed titles before event matching."""
    text = clean_text(title).lower()
    text = SOURCE_SUFFIX_RE.sub("", text).strip()
    text = re.sub(r"[#｜|:：,，;；.!！?？()（）\[\]【】\"'“”‘’]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_entities(text):
    entities = set()
    for entity, aliases in ENTITY_ALIASES.items():
        if any(alias.lower() in text for alias in aliases):
            entities.add(entity)
    return entities


def extract_topic_buckets(text):
    buckets = set()
    for bucket, keywords in TOPIC_BUCKETS.items():
        if any(keyword.lower() in text for keyword in keywords):
            buckets.add(bucket)
    return buckets


def extract_money_amounts(text):
    amounts = []
    for raw_number, unit in re.findall(r"(\d+(?:\.\d+)?)\s*(万亿|亿美元|亿美金|美元|美金|亿元|亿人币|亿人民币|亿港元|亿|万)", text):
        value = float(raw_number)
        if unit in {"万亿"}:
            value *= 10000
        elif unit in {"亿美元", "亿美金"}:
            value *= 7
        elif unit in {"美元", "美金"}:
            value /= 100000000 / 7
        elif unit in {"万"}:
            value /= 10000
        amounts.append(value)

    for currency, raw_number, unit in re.findall(r"(rmb|usd|\$|¥|￥)?\s*(\d+(?:\.\d+)?)\s*(billion|bn|b|million|m)\+?", text):
        value = float(raw_number)
        currency = currency.lower()
        unit = unit.lower()
        if unit in {"billion", "bn", "b"}:
            value *= 10
        else:
            value /= 100
        if currency in {"usd", "$"} or (not currency and unit in {"billion", "bn"}):
            value *= 7
        amounts.append(value)
    return amounts


def text_tokens(text):
    tokens = set()
    for token in re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)?", text):
        if len(token) > 1 and token not in STOPWORDS:
            tokens.add(token)

    chinese_chunks = re.findall(r"[\u4e00-\u9fff]{2,}", text)
    for chunk in chinese_chunks:
        if chunk in STOPWORDS:
            continue
        if len(chunk) <= 4:
            tokens.add(chunk)
        for i in range(len(chunk) - 1):
            gram = chunk[i:i + 2]
            if gram not in STOPWORDS:
                tokens.add(gram)

    return tokens


def token_overlap(a, b):
    if not a or not b:
        return 0
    return len(a & b) / min(len(a), len(b))


def amounts_overlap(a, b):
    if not a or not b:
        return False
    for left in a:
        for right in b:
            lower = min(left, right)
            upper = max(left, right)
            if lower > 0 and upper / lower <= 2.5:
                return True
    return False


def article_signature(article):
    text = normalize_title(article.get("title", ""))
    summary = normalize_title(article.get("summary", ""))
    combined = f"{text} {summary}".strip()
    return {
        "title": text,
        "combined": combined,
        "entities": extract_entities(combined),
        "topics": extract_topic_buckets(combined),
        "amounts": extract_money_amounts(combined),
        "tokens": text_tokens(combined),
    }


def similarity(a, b):
    """Compute string similarity ratio between two titles."""
    return SequenceMatcher(None, normalize_title(a), normalize_title(b)).ratio()


def is_same_event(left, right, threshold, left_sig=None, right_sig=None):
    """Return True when two articles likely describe the same news event."""
    left_sig = left_sig or article_signature(left)
    right_sig = right_sig or article_signature(right)
    title_ratio = SequenceMatcher(None, left_sig["title"], right_sig["title"]).ratio()
    overlap = token_overlap(left_sig["tokens"], right_sig["tokens"])

    if title_ratio >= threshold or overlap >= 0.7:
        return True

    common_entities = left_sig["entities"] & right_sig["entities"]
    common_topics = left_sig["topics"] & right_sig["topics"]
    if not common_entities or not common_topics:
        return False

    if "funding" in common_topics:
        return amounts_overlap(left_sig["amounts"], right_sig["amounts"]) and (title_ratio >= 0.25 or overlap >= 0.12)

    if title_ratio >= 0.4 or overlap >= 0.25:
        return True

    return len(common_entities) >= 2 and overlap >= 0.15


def deduplicate(articles, threshold=0.8):
    """
    Group articles by lightweight event similarity.
    Returns list of event groups, each group is a list of similar articles.
    """
    groups = []
    signature_cache = {}

    def signatures_match(left, right):
        for article in (left, right):
            cache_key = id(article)
            if cache_key not in signature_cache:
                signature_cache[cache_key] = article_signature(article)
        return is_same_event(left, right, threshold, signature_cache[id(left)], signature_cache[id(right)])

    for article in articles:
        matched = False

        for group in groups:
            if any(signatures_match(article, existing) for existing in group):
                group.append(article)
                matched = True
                break

        if not matched:
            groups.append([article])

    return groups


def classify(title, summary, config):
    """
    Classify an event into a category based on keyword matching.
    Returns (categoryKey, label).
    """
    text = (title + " " + summary).lower()
    categories = config.get("categories", {})

    best_match = None
    best_count = 0

    for key, cat_cfg in categories.items():
        keywords = cat_cfg.get("keywords", [])
        count = sum(1 for kw in keywords if kw.lower() in text)
        if count > best_count:
            best_count = count
            best_match = key

    if best_match:
        return best_match, categories[best_match]["label"]

    return "business", "商业动态"


def get_source_type(article):
    """Return collector source type with fallback for older raw data."""
    if article.get("source_type"):
        return article["source_type"]
    if article.get("search_keyword"):
        return "google_news"
    return "rss"


def source_weight(article):
    source_name = article.get("source", "")
    source_type = get_source_type(article)

    if source_type == "rss":
        if source_name in OFFICIAL_RSS_SOURCES:
            return 1.0
        if source_name in HIGH_QUALITY_RSS_SOURCES:
            return 0.85
        return 0.7

    if source_name in REPUTABLE_NEWS_SOURCES:
        return 0.7
    if source_name in LOW_QUALITY_NEWS_SOURCES:
        return 0.35
    return 0.55


def quality_score(group):
    weights = sorted((source_weight(article) for article in group), reverse=True)
    top_weights = weights[:3]
    return sum(top_weights) / len(top_weights)


def diversity_score(group):
    source_types = {get_source_type(article) for article in group}
    rss_sources = {article.get("source", "") for article in group if get_source_type(article) == "rss"}
    distinct_sources = {article.get("source", "") for article in group}

    if len(rss_sources) >= 2:
        return 1.0
    if "rss" in source_types and "google_news" in source_types:
        return 0.8
    if len(distinct_sources) > 1:
        return 0.55
    return 0.35


def mention_score(group):
    mention_count = len(group)
    return min(1.0, math.log1p(mention_count) / math.log(8))


def parse_iso_datetime(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def time_decay_score(group, reference_time=None):
    timestamps = []
    for article in group:
        parsed = parse_iso_datetime(article.get("timestamp"))
        if parsed is None:
            continue
        timestamps.append(parsed)

    if not timestamps:
        return 1.0

    reference_time = reference_time or datetime.now(timezone.utc)
    reference_time = reference_time.astimezone(timezone.utc)
    newest = max(timestamps)
    age_hours = max(0, (reference_time - newest.astimezone(timezone.utc)).total_seconds() / 3600)
    return 0.85 + 0.15 * math.exp(-age_hours / 48)


def ai_relevance_score(group):
    text = " ".join(
        f"{article.get('title', '')} {article.get('summary', '')}"
        for article in group
    ).lower()
    short_terms = {"ai", "llm", "gpt"}
    if any(keyword not in short_terms and keyword in text for keyword in AI_RELEVANCE_KEYWORDS):
        return 1.0
    if re.search(r"(?<![a-z0-9])(?:ai|llm|gpt)(?![a-z0-9])", text):
        return 1.0
    return 0.25


def compute_score(group, category_key, reference_time=None):
    """Compute conservative hot score and explainable score components."""
    quality = quality_score(group)
    diversity = diversity_score(group)
    mentions = mention_score(group)
    event_type = EVENT_TYPE_WEIGHTS.get(category_key, 0.45)
    time_decay = time_decay_score(group, reference_time)
    ai_relevance = ai_relevance_score(group)

    raw_score = 100 * (
        0.45 * quality
        + 0.25 * diversity
        + 0.20 * mentions
        + 0.10 * event_type
    ) * time_decay * ai_relevance

    breakdown = {
        "quality": round(quality, 2),
        "diversity": round(diversity, 2),
        "mentions": round(mentions, 2),
        "event_type": round(event_type, 2),
        "time_decay": round(time_decay, 2),
        "ai_relevance": round(ai_relevance, 2),
    }
    return round(raw_score), breakdown


def process(raw_file=None):
    """Main processing pipeline."""
    print("=" * 50)
    print("AI Daily Pulse - Processing Pipeline")
    print("=" * 50)

    # Determine input file
    if raw_file is None:
        beijing_tz = timezone(timedelta(hours=8))
        target_date = (datetime.now(beijing_tz) - timedelta(days=1)).strftime("%Y-%m-%d")
        raw_file = Path("data/raw") / f"{target_date}.json"
    else:
        raw_file = Path(raw_file)

    if not raw_file.exists():
        print(f"Error: Raw data file not found: {raw_file}")
        return None

    # Load raw data
    with open(raw_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    articles = raw_data.get("articles", [])
    date = raw_data.get("date", "")
    reference_time = parse_iso_datetime(raw_data.get("collected_at"))
    print(f"Processing {len(articles)} articles for {date}")

    # Load config for classification
    config = load_config()

    # Deduplicate
    groups = deduplicate(articles)
    print(f"Deduplicated into {len(groups)} unique events")

    # Build events
    events = []
    for group in groups:
        rep = group[0]
        title = clean_text(rep["title"])
        summary = clean_text(rep.get("summary", "")) or title

        category_key, category_label = classify(title, summary, config)

        sources = []
        seen_sources = set()
        for article in group:
            source_name = article.get("source", "Unknown")
            source_url = article.get("url", "")
            source_title = clean_text(article.get("title", "")) or source_name
            source_type = get_source_type(article)
            source_key = (source_name, source_url, source_title)
            if source_key not in seen_sources:
                seen_sources.add(source_key)
                sources.append({"name": source_name, "title": source_title, "url": source_url, "source_type": source_type})

        mention_count = len(group)
        importance_score, score_breakdown = compute_score(group, category_key, reference_time)

        events.append({
            "id": generate_id(title),
            "title": title,
            "summary": summary,
            "category": category_label,
            "categoryKey": category_key,
            "sources": sources,
            "mention_count": mention_count,
            "importance_score": importance_score,
            "score_breakdown": score_breakdown,
            "timestamp": rep.get("timestamp", ""),
        })

    # Sort by importance_score descending
    events.sort(key=lambda x: x["importance_score"], reverse=True)

    # Top 3
    top3 = events[:3]

    # Build final output
    beijing_tz = timezone(timedelta(hours=8))
    output_data = {
        "date": date,
        "generated_at": datetime.now(beijing_tz).isoformat(),
        "top3": top3,
        "all_news": events,
    }

    # Save
    output_dir = Path("data")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{date}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\nProcessed {len(events)} events")
    print(f"Top 3 events:")
    for i, evt in enumerate(top3, 1):
        print(f"  {i}. [{evt['category']}] {evt['title']} (score: {evt['importance_score']})")
    print(f"\nFinal data saved to: {output_file}")

    return str(output_file)


if __name__ == "__main__":
    process(sys.argv[1] if len(sys.argv) > 1 else None)