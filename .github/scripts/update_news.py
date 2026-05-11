"""
每日自动抓取人形机器人领域热点新闻，更新 news.json
数据来源：Google News RSS、机器之心 RSS 等
"""
import json
import re
import sys
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    print("requests not installed, using urllib")
    import urllib.request as urllib2
    requests = None

try:
    import feedparser
except ImportError:
    print("feedparser not installed, will use basic parsing")
    feedparser = None

NEWS_FILE = "data/news.json"
OUTPUT_FILE = "data/news.json"

# RSS feeds
FEEDS = [
    # Google News - 人形机器人
    "https://news.google.com/rss/search?q=%E4%BA%BA%E5%BD%A2%E6%9C%BA%E5%99%A8%E4%BA%BA+humanoid+robot&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
    # Google News - humanoid robot (English)
    "https://news.google.com/rss/search?q=humanoid+robot&hl=en-US&gl=US&ceid=US:en",
    # 机器之心
    "https://www.jiqizhixin.com/rss",
]


def fetch_feed(url):
    """Fetch and parse an RSS feed"""
    items = []
    try:
        if feedparser:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                title = entry.get("title", "")
                link = entry.get("link", "")
                published = entry.get("published", "")
                summary = entry.get("summary", "")
                # Clean HTML
                summary = re.sub(r"<[^>]+>", "", summary)[:200]
                if title:
                    items.append(
                        {
                            "title": title.strip(),
                            "url": link,
                            "date_str": published,
                            "summary": summary.strip(),
                            "source": entry.get("source", {}).get("title", ""),
                        }
                    )
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
    return items


def extract_date(date_str):
    """Try to parse various date formats to YYYY-MM-DD"""
    try:
        from email.utils import parsedate_to_datetime

        dt = parsedate_to_datetime(date_str)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        pass
    today = datetime.now().strftime("%Y-%m-%d")
    return today


def score_news(item):
    """Score news relevance"""
    score = 0
    title = item.get("title", "")
    summary = item.get("summary", "")
    text = title + summary

    keywords = {
        "人形机器人": 10,
        "humanoid": 10,
        "宇树": 8,
        "unitree": 8,
        "特斯拉": 7,
        "tesla optimus": 8,
        "figure": 7,
        "智元": 7,
        "agibot": 7,
        "优必选": 6,
        "ubtech": 6,
        "波士顿动力": 7,
        "boston dynamics": 7,
        "灵巧手": 8,
        "dexterous": 7,
        "量产": 6,
        "三星": 5,
        "samsung": 5,
        "meta": 5,
        "融资": 6,
        "funding": 5,
        "具身智能": 7,
        "embodied": 7,
        "摩根士丹利": 4,
        "morgan stanley": 4,
        "1x": 5,
        "apptronik": 5,
        "agility": 5,
        "digit": 4,
        "nvidia": 5,
        "英伟达": 5,
        "大模型": 5,
        "VLA": 6,
        "apptronik": 5,
    }
    for kw, pts in keywords.items():
        if kw.lower() in text.lower():
            score += pts
    return min(score + 40, 99)  # base 40, max 99


def main():
    print(f"=== 人形机器人热点新闻更新 ===")
    print(f"时间: {datetime.now().isoformat()}")

    all_items = []
    for url in FEEDS:
        print(f"Fetching: {url[:80]}...")
        items = fetch_feed(url)
        print(f"  Got {len(items)} items")
        all_items.extend(items)

    # Deduplicate by similar title
    seen = set()
    unique = []
    for item in all_items:
        key = item["title"][:40]
        if key not in seen:
            seen.add(key)
            unique.append(item)

    print(f"Total unique items: {len(unique)}")

    # Score and select top 10
    for item in unique:
        item["heat"] = score_news(item)
    unique.sort(key=lambda x: x["heat"], reverse=True)
    top10 = unique[:10]

    # Format output
    today = datetime.now().strftime("%Y-%m-%d")
    news_data = []
    for item in top10:
        source = item.get("source", "")
        if not source:
            # Extract domain from URL
            url = item.get("url", "")
            m = re.search(r"https?://(?:www\.)?([^/]+)", url)
            if m:
                source = m.group(1).split(".")[-2].title()
            else:
                source = "综合报道"

        news_data.append(
            {
                "title": item["title"][:80],
                "date": today,
                "source": source[:20],
                "summary": item["summary"][:150],
                "url": item.get("url", ""),
                "heat": item["heat"],
            }
        )

    # Ensure we have at least 5 items (keep existing if insufficient)
    if len(news_data) < 5:
        try:
            with open(NEWS_FILE, "r") as f:
                old = json.load(f)
            existing = old[len(news_data) : 5 - len(news_data)]
            news_data.extend(existing)
        except Exception:
            pass

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(news_data, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(news_data)} news items to {OUTPUT_FILE}")
    for i, item in enumerate(news_data):
        print(f"  {i+1}. [{item['heat']}°] {item['title'][:60]}")


if __name__ == "__main__":
    main()
