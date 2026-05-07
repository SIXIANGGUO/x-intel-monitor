#!/usr/bin/env python3
"""
X RSS Fetcher - uses xgo.ing RSS feeds (free, no API key needed)
Replaces twitter_fetch_concurrent.py which uses TikHub SDK.

OPML source: https://github.com/ginobefun/BestBlogs/blob/main/BestBlogs_RSS_Twitters.opml
- 160 accounts covering AI researchers, labs, builders, VC
- RSS via xgo.ing, each feed returns 50 recent tweets
- Deduplication via <guid> (tweet ID)
"""
import asyncio
import json
import re
import time
from datetime import datetime, timedelta, timezone
from html import unescape
from pathlib import Path
from typing import Optional
from xml.sax.saxutils import escape as xml_escape

import feedparser


def _strip_html(text: str) -> str:
    """Remove HTML tags, engagement footer, and decode entities from summary text."""
    # Replace <br /> with newlines first
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    # Remove all remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities (e.g. &amp; &lt; &#39;)
    text = unescape(text)
    # Remove engagement metrics footer: 💬12 🔄8 ❤️116 👀37383 📊23 patterns
    # Covers single-codepoint emoji + multi-codepoint (emoji + variation selector U+FE0F)
    text = re.sub(
        r'[\U0001F4AC\U0001F504\U00002764\U0001F493\U0001F440\U0001F4CA\u2764\u2605]\uFE0F?\d+',
        '', text
    )
    # Remove "⚡ Powered by xgo.ing" footer
    text = re.sub(r'⚡\s*Powered by xgo\.ing', '', text)
    # Collapse multiple spaces and clean up
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n[ \t]+', '\n', text)
    # Remove trailing empty lines
    text = text.rstrip()
    return text

DEDUP_FILE = Path(__file__).parent / "written-ids.json"
OUTPUT_FILE = Path(__file__).parent / "fetched-tweets.json"
OPML_URL = "https://raw.githubusercontent.com/ginobefun/BestBlogs/main/BestBlogs_RSS_Twitters.opml"

# Time window: tweets newer than this are kept (default 48h)
_WINDOW_HOURS = 48

_sem = asyncio.Semaphore(10)  # concurrent RSS fetches


def _load_written_ids() -> set:
    """Load tweet IDs we already wrote to avoid duplicates."""
    if DEDUP_FILE.exists():
        try:
            return set(json.loads(DEDUP_FILE.read_text()))
        except Exception:
            return set()
    return set()


def _save_written_ids(ids: set):
    """Append new IDs to dedup file."""
    existing = _load_written_ids()
    combined = existing | ids
    DEDUP_FILE.write_text(json.dumps(list(combined), ensure_ascii=False))


def _window_start() -> datetime:
    return datetime.now(timezone.utc) - timedelta(hours=_WINDOW_HOURS)


# Known Chinese account handles (from OPML)
_CHINESE_HANDLES = {
    'lijigang_com', 'dotey', 'imxiaohu', 'op7418', '_catwu', 'vista8',
    'HiTw93', 'Yangyixxxx', 'hidecloud', 'geekbb', 'vikingmute',
    'idoubicc', 'PMbackttfuture', 'shao__meng', 'oran_ge',
}

async def fetch_one_feed(screen_name: str, rss_url: str) -> list:
    """Fetch one RSS feed, return list of tweets within time window."""
    async with _sem:
        await asyncio.sleep(0.3)  # rate limit
        try:
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, rss_url)
        except Exception as e:
            print(f"[!] Feed error {screen_name}: {e}")
            return []

        tweets = []
        ws = _window_start()
        for entry in feed.entries:
            # guid is the tweet ID
            tweet_id = getattr(entry, 'id', None) or getattr(entry, 'guid', None)
            if not tweet_id:
                continue

            # Filter by time window
            pub_parsed = getattr(entry, 'published_parsed', None)
            if pub_parsed:
                pub_dt = datetime(*pub_parsed[:6], tzinfo=timezone.utc)
                if pub_dt < ws:
                    continue

            # Extract author name
            author_name = getattr(entry, 'author', screen_name) or screen_name

            # Use summary (full text) instead of title (truncated at ~103 chars by xgo.ing RSS)
            raw_text = getattr(entry, 'summary', '') or getattr(entry, 'title', '') or ''
            tweet_text = _strip_html(raw_text)

            tweets.append({
                "id": tweet_id,
                "text": tweet_text,
                "author": screen_name,
                "author_name": author_name,
                "created_at": getattr(entry, 'published', '') or '',
                "is_chinese": screen_name.lower() in _CHINESE_HANDLES,
                "url": f"https://x.com/{screen_name}/status/{tweet_id}",
            })

        return tweets


def parse_opml(opml_text: str) -> list:
    """Extract (screen_name, rss_url) pairs from OPML."""
    accounts = []
    for line in opml_text.splitlines():
        m = re.search(r'text="([^"]+)"[^>]*xmlUrl="([^"]+)"', line)
        if m:
            name = m.group(1)
            url = m.group(2)
            # Extract handle from name like "OpenAI(@OpenAI)"
            handle = name.split("(@")[-1].rstrip(")") if "@" in name else name
            accounts.append((handle, url))
    return accounts


async def fetch_all_feeds(accounts: list) -> list:
    """Fetch all feeds concurrently."""
    tasks = [fetch_one_feed(handle, url) for handle, url in accounts]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    all_tweets = []
    for r in results:
        if isinstance(r, Exception):
            continue
        all_tweets.extend(r)
    return all_tweets


def main():
    print(f"[x_rss_fetcher] Fetching OPML from {OPML_URL}")
    import urllib.request
    try:
        with urllib.request.urlopen(OPML_URL, timeout=30) as resp:
            opml_text = resp.read().decode('utf-8')
    except Exception as e:
        print(f"[!] Failed to fetch OPML: {e}")
        return

    accounts = parse_opml(opml_text)
    print(f"[x_rss_fetcher] Found {len(accounts)} accounts in OPML")

    all_tweets = asyncio.run(fetch_all_feeds(accounts))

    # Deduplicate by ID
    written_ids = _load_written_ids()
    new_tweets = [t for t in all_tweets if t['id'] not in written_ids]

    # Sort by created_at desc
    def parse_date(t):
        try:
            return datetime.strptime(t['created_at'], '%a, %d %b %Y %H:%M:%S %z')
        except Exception:
            return datetime.min.replace(tzinfo=timezone.utc)

    new_tweets.sort(key=parse_date, reverse=True)

    print(f"[x_rss_fetcher] Total fetched: {len(all_tweets)}, New (not yet written): {len(new_tweets)}")

    if new_tweets:
        # Save new tweets
        OUTPUT_FILE.write_text(json.dumps(new_tweets, ensure_ascii=False, indent=2))
        # Update dedup file
        new_ids = {t['id'] for t in new_tweets}
        _save_written_ids(new_ids)
        print(f"[x_rss_fetcher] Written {len(new_tweets)} new tweets to {OUTPUT_FILE}")
    else:
        print("[x_rss_fetcher] No new tweets")


if __name__ == "__main__":
    main()
