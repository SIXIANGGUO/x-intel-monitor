#!/usr/bin/env python3
"""
Twitter Fetcher via TikHub SDK v2 — paid API alternative to xgo.ing RSS.

Uses TikHub API (https://tikhub.io) which requires:
  1. Sign up at tikhub.io to get an API key
  2. Set TIKHUB_API_KEY in your environment or .env file

Free alternative: x_rss_fetcher.py uses xgo.ing RSS with zero config.

OPML source: https://github.com/ginobefun/BestBlogs
"""
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── SDK setup ──────────────────────────────────
# TikHub SDK must be installed: pip install tikhub
# If you use a custom Python path, add it here:
# sys.path.insert(0, "/path/to/site-packages")
try:
    from tikhub import async_client
except ImportError:
    print("[!] TikHub SDK not found. Install: pip install tikhub")
    print("[!] Or use x_rss_fetcher.py (free, no API key needed)")
    sys.exit(1)

# ── Config ─────────────────────────────────────
# Replace with your monitored accounts
# See config/monitored_accounts.py for a full list
ACCOUNTS = [
    "AnthropicAI", "OpenAI", "deepseek_ai", "Qwen_AI",
    "midjourney", "mistralai",
    "claudeai", "cursor_ai", "huggingface", "MiniMax_AI",
    "Docker", "GitHub",
    "karpathy", "sama", "demishassabis", "ylecun", "DarioAmodei",
    "geoffreyhinton", "ilyasut", "jeffdean", "drfeifei", "AndrewYNg",
    "jimfan", "swyx", "rauchg", "gdb", "teknium",
]

DEDUP_FILE  = Path("written-ids.json")
OUTPUT_FILE = Path("fetched-tweets.json")
# Time window in hours (TikHub free tier is limited, keep this small)
_WINDOW_HOURS = 4

_semaphore   = asyncio.Semaphore(5)
_window_start: datetime = None


# ── Helpers ─────────────────────────────────────
def load_api_key() -> str:
    """Read TIKHUB_API_KEY from environment or ~/.hermes/.env."""
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("TIKHUB_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"')
    return os.getenv("TIKHUB_API_KEY", "")


def load_sent_ids() -> set:
    if not DEDUP_FILE.exists():
        return set()
    try:
        data = json.loads(DEDUP_FILE.read_text())
        return set(data.get("sent_ids", []))
    except Exception:
        return set()


def tweet_in_window(created_at: str, start: datetime) -> bool:
    if not created_at:
        return False
    try:
        ts = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
        return ts >= start
    except Exception:
        return False


# ── Fetch one account ────────────────────────────
async def fetch_one(screen_name: str, api_key: str) -> list:
    async with _semaphore:
        try:
            async with async_client.AsyncTikHub(api_key=api_key) as client:
                cursor = None
                all_tweets = []
                while True:
                    try:
                        result = await client.twitter_web.fetch_user_post_tweet(
                            screen_name=screen_name, cursor=cursor
                        )
                    except Exception as e:
                        if "400" in str(e) or "429" in str(e):
                            print(f"[!] {screen_name}: {e}")
                            break
                        raise
                    if isinstance(result, dict) and result.get("code") != 200:
                        break
                    timeline = result.get("data", {}).get("timeline", []) if isinstance(result, dict) else []
                    if not timeline:
                        break
                    for t in timeline:
                        all_tweets.append({
                            "id":          t.get("tweet_id", ""),
                            "text":        t.get("text", ""),
                            "author":      screen_name,
                            "author_name": t.get("author", {}).get("name", ""),
                            "created_at":  t.get("created_at", ""),
                            "likes":       t.get("favorites", 0),
                            "retweets":    t.get("retweets", 0),
                            "views":       t.get("views", "0"),
                            "url":         f"https://x.com/{screen_name}/status/{t.get('tweet_id')}",
                        })
                    # Early-stop: if oldest tweet is already outside window, stop paging
                    oldest = timeline[-1].get("created_at", "")
                    if _window_start and tweet_in_window(oldest, _window_start) is False:
                        # oldest is BEFORE window_start = too old
                        pass
                    # Actually check: if oldest < window_start, break
                    if oldest:
                        try:
                            ts_oldest = datetime.strptime(oldest, "%a %b %d %H:%M:%S %z %Y")
                            if ts_oldest < _window_start:
                                break
                        except Exception:
                            pass
                    next_cursor = result.get("data", {}).get("next_cursor") if isinstance(result, dict) else None
                    if not next_cursor or cursor == next_cursor:
                        break
                    cursor = next_cursor
                return all_tweets
        except Exception as e:
            print(f"[!] Error fetching {screen_name}: {e}")
            return []


# ── Main ────────────────────────────────────────
def main():
    api_key = load_api_key()
    if not api_key:
        print("[!] TIKHUB_API_KEY not found.")
        print("    Set it in environment or ~/.hermes/.env")
        print("    Or use x_rss_fetcher.py (free, no API key needed)")
        sys.exit(1)

    now = datetime.now(timezone.utc)
    window_start = now - timedelta(hours=_WINDOW_HOURS)
    window_end   = now

    global _window_start
    _window_start = window_start

    print(f"Fetching {len(ACCOUNTS)} accounts (TikHub SDK v2, window={_WINDOW_HOURS}h) ...")

    all_tweets = asyncio.run(asyncio.gather(*[fetch_one(acc, api_key) for acc in ACCOUNTS]))
    flat = []
    for tweets in all_tweets:
        if isinstance(tweets, list):
            flat.extend(tweets)

    print(f"Fetched {len(flat)} tweets total")

    # Filter by time window
    filtered = [t for t in flat if tweet_in_window(t["created_at"], window_start)]
    print(f"After window filter: {len(filtered)} tweets")

    # Deduplicate
    sent_ids   = load_sent_ids()
    new_tweets = [t for t in filtered if t["id"] not in sent_ids]
    print(f"New: {len(new_tweets)} | Already sent: {len(filtered) - len(new_tweets)}")

    new_tweets.sort(key=lambda t: t["created_at"], reverse=True)

    # Update dedup file with all filtered IDs
    all_filtered_ids = {t["id"] for t in filtered}
    updated_sent = sent_ids | all_filtered_ids
    DEDUP_FILE.write_text(json.dumps({
        "sent_ids":     list(updated_sent),
        "last_updated": datetime.now().isoformat()
    }, ensure_ascii=False, indent=2))

    # Write output
    OUTPUT_FILE.write_text(json.dumps({
        "fetch_time":   datetime.now().isoformat(),
        "window_start": window_start.isoformat(),
        "window_end":   window_end.isoformat(),
        "total":        len(flat),
        "in_window":    len(filtered),
        "new_count":    len(new_tweets),
        "new_tweets":   new_tweets,
    }, ensure_ascii=False, indent=2))

    print(f"Written: {OUTPUT_FILE}")
    if new_tweets:
        print(f"  ({len(new_tweets)} new tweets)")


if __name__ == "__main__":
    main()
