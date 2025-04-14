import feedparser
import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List
from difflib import SequenceMatcher
import pytz
import re
from dateutil import parser

# Configuration
RSS_FEEDS = {
    "The Hacker News": "https://feeds.feedburner.com/TheHackersNews",
    "Dark Reading": "https://www.darkreading.com/rss.xml",
    "BleepingComputer": "https://www.bleepingcomputer.com/feed/",
    "TechCrunch": "https://techcrunch.com/feed/",
    "Wired": "https://www.wired.com/feed/category/security/latest/rss",
    "Threatpost": "https://threatpost.com/feed/",
    "Security Boulevard": "https://securityboulevard.com/feed/",
    "Objective-See(MacOS)": "https://objective-see.org/rss.xml",
    "Krebs on Security": "https://krebsonsecurity.com/feed/",
    "SecurityWeek": "https://www.securityweek.com/feed/",
    "Tripwire": "https://www.tripwire.com/state-of-security/feed/",
    "SANS ISC": "https://isc.sans.edu/rssfeed.xml",
    "Exploit-DB": "https://www.exploit-db.com/rss.xml"
}

API_ENDPOINTS = {
    "CIRCL CVE": {
        "url": "https://vulnerability.circl.lu/api/last/10",
        "headers": {},
    },
}

CATEGORIES = {
    "Security Product/Business News": [
        "product", "business", "enterprise", "solution", "vendor", "acquisition", "funding",
        "partnership", "compliance", "regulation", "market", "industry"
    ],
    "Tools": [
        "tool", "software", "framework", "script", "exploit", "scanner", "pentest",
        "automation", "open-source", "github", "repository"
    ],
    "Vulnerabilities/Threat Intel": [
        "vulnerability", "cve", "exploit", "malware", "ransomware", "phishing", "threat",
        "attack", "breach", "zero-day", "ioc", "intelligence", "patch"
    ],
    "Security Events": [
        "conference", "summit", "hackathon", "webinar", "event", "meetup", "workshop",
        "defcon", "blackhat", "rsac", "training"
    ]
}

CACHE_FILE = "cache.json"
OUTPUT_JSON = "cybersecurity_data.json"
MAX_ITEMS_PER_CATEGORY = 7
MAX_ITEMS_PER_FEED = 3  # Limit per feed for diversity

# Timezone mapping
TZINFOS = {
    "EST": pytz.timezone("US/Eastern"),
    "EDT": pytz.timezone("US/Eastern"),
    "CST": pytz.timezone("US/Central"),
    "CDT": pytz.timezone("US/Central"),
    "MST": pytz.timezone("US/Mountain"),
    "MDT": pytz.timezone("US/Mountain"),
    "PST": pytz.timezone("US/Pacific"),
    "PDT": pytz.timezone("US/Pacific"),
    "GMT": pytz.UTC,
    "UTC": pytz.UTC
}

def load_cache() -> Dict:
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {"items": {}, "last_run": ""}

def save_cache(cache: Dict):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

def normalize_title(title: str) -> str:
    """Normalize title for deduplication."""
    title = title.lower()
    title = re.sub(r'[^\w\s]', '', title)
    title = re.sub(r'\s+', ' ', title).strip()
    return title

def is_duplicate(new_title: str, existing_titles: List[str], threshold: float = 0.9) -> bool:
    """Check if new_title is a duplicate."""
    new_title_normalized = normalize_title(new_title)
    for existing_title in existing_titles:
        existing_normalized = normalize_title(existing_title)
        similarity = SequenceMatcher(None, new_title_normalized, existing_normalized).ratio()
        if similarity >= threshold:
            return True
    return False

def categorize_item(title: str, summary: str) -> List[str]:
    categories = []
    text = (title.lower() + " " + summary.lower()).replace("\n", " ")
    for category, keywords in CATEGORIES.items():
        if any(keyword in text for keyword in keywords):
            categories.append(category)
    return categories or ["Vulnerabilities/Threat Intel"]

def parse_date(date_str: str) -> datetime:
    """Parse date formats, ensuring offset-aware datetime."""
    try:
        parsed = parser.parse(date_str, tzinfos=TZINFOS)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=pytz.UTC)
        return parsed
    except (ValueError, TypeError):
        # Fallback to current time if parsing fails
        return datetime.now(tz=pytz.UTC)

def fetch_rss_feed(feed_name: str, url: str, cache: Dict, seen_titles: List[str]) -> List[Dict]:
    try:
        feedparser.PARSE_MICROFORMATS = False
        feed = feedparser.parse(url)
        if feed.bozo and feed.bozo_exception:
            print(f"Warning parsing {feed_name}: {feed.bozo_exception}")
        
        items = []
        cutoff_date = datetime.now(tz=pytz.UTC) - timedelta(days=7)
        feed_item_count = 0
        
        for entry in feed.entries[:10]:
            if feed_item_count >= MAX_ITEMS_PER_FEED:
                break
                
            item_id = entry.get("id", entry.get("link", ""))
            if not item_id or item_id in cache["items"]:
                continue
            
            published_str = entry.get("published", entry.get("updated", ""))
            published = parse_date(published_str) if published_str else datetime.now(tz=pytz.UTC)
            
            if published < cutoff_date:
                continue
                
            title = entry.get("title", "No title")
            link = entry.get("link", "")
            summary = entry.get("summary", entry.get("description", "")).strip()
            if not summary and "content" in entry:
                summary = entry.content[0].value if entry.content else ""
            
            if is_duplicate(title, seen_titles):
                continue
            seen_titles.append(title)
            
            categories = categorize_item(title, summary)
            cache["items"][item_id] = published.isoformat()
            feed_item_count += 1
            
            for category in categories:
                items.append({
                    "source": feed_name,
                    "title": title,
                    "link": link,
                    "summary": summary[:150] + "..." if len(summary) > 150 else summary,
                    "published": published.isoformat(),
                    "category": category
                })
        return items
    except Exception as e:
        print(f"Failed to fetch {feed_name}: {e}")
        return []

def fetch_api_data(api_name: str, config: Dict, cache: Dict, seen_titles: List[str]) -> List[Dict]:
    try:
        response = requests.get(config["url"], headers=config["headers"], timeout=10)
        response.raise_for_status()
        data = response.json()
        
        items = []
        cutoff_date = datetime.now(tz=pytz.UTC) - timedelta(days=7)
        
        if api_name == "CIRCL CVE":
            api_item_count = 0
            for cve in data:
                if api_item_count >= MAX_ITEMS_PER_FEED:
                    break
                    
                item_id = cve.get("id", "")
                if not item_id or item_id in cache["items"]:
                    continue
                
                published_str = cve.get("Published", datetime.now(tz=pytz.UTC).isoformat())
                published = parse_date(published_str)
                
                if published < cutoff_date:
                    continue
                
                title = item_id
                summary = cve.get("summary", "")
                
                if is_duplicate(title, seen_titles):
                    continue
                seen_titles.append(title)
                
                categories = categorize_item(title, summary)
                cache["items"][item_id] = published.isoformat()
                api_item_count += 1
                
                for category in categories:
                    items.append({
                        "source": api_name,
                        "title": title,
                        "link": f"https://cve.circl.lu/cve/{title}",
                        "summary": summary[:150] + "..." if len(summary) > 150 else summary,
                        "published": published.isoformat(),
                        "category": category
                    })
        
        return items
    except Exception as e:
        print(f"Failed to fetch {api_name}: {e}")
        return []

def update_dashboard():
    print(f"Running update at {datetime.now(tz=pytz.UTC)}")
    cache = load_cache()
    
    output = {
        "Security Product/Business News": [],
        "Tools": [],
        "Vulnerabilities/Threat Intel": [],
        "Security Events": []
    }
    
    all_items = []
    seen_titles = []
    
    for feed_name, url in RSS_FEEDS.items():
        print(f"Fetching {feed_name}...")
        items = fetch_rss_feed(feed_name, url, cache, seen_titles)
        all_items.extend(items)
    
    for api_name, config in API_ENDPOINTS.items():
        print(f"Fetching {api_name}...")
        items = fetch_api_data(api_name, config, cache, seen_titles)
        all_items.extend(items)
    
    for item in all_items:
        category = item["category"]
        output[category].append({
            "source": item["source"],
            "title": item["title"],
            "link": item["link"],
            "summary": item["summary"],
            "published": item["published"]
        })
    
    for category in output:
        output[category].sort(key=lambda x: datetime.fromisoformat(x["published"]), reverse=True)
        output[category] = output[category][:MAX_ITEMS_PER_CATEGORY]
    
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    cache["last_run"] = datetime.now(tz=pytz.UTC).isoformat()
    save_cache(cache)
    
    print(f"Data saved to {OUTPUT_JSON} and cache updated successfully. 😊")

if __name__ == "__main__":
    update_dashboard()