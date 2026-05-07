# Monitored Accounts Configuration
#
# Two versions of this list exist:
#   1. TikHub SDK version (this file) — for twitter_fetch_tikhub.py
#   2. OPML from BestBlogs — auto-parsed by x_rss_fetcher.py
#
# To use TikHub version:
#   1. Get API key from https://tikhub.io
#   2. Set TIKHUB_API_KEY env var
#   3. Copy accounts from this list into twitter_fetch_tikhub.py ACCOUNTS
#
# To use free RSS version (recommended):
#   x_rss_fetcher.py auto-downloads BestBlogs OPML with 160 accounts

# ── Tier 1: Model / Platform (6) ──────────────
# Core AI labs and model providers
AnthropicAI
OpenAI
deepseek_ai
Qwen_AI
midjourney
mistralai

# ── Tier 2: Product / Application (4) ─────────
claudeai
cursor_ai
huggingface
MiniMax_AI

# ── Tier 3: Infra / Tooling (2) ───────────────
Docker
GitHub

# ── Tier 4: Core People (15) ──────────────────
# Researchers, builders, and influencers
karpathy
sama
demishassabis
ylecun
DarioAmodei
geoffreyhinton
ilyasut
jeffdean
drfeifei
AndrewYNg
jimfan
swyx
rauchg
gdb
teknium

# ── Account management principles ──────────────
# 1. Deduplicate: same entity multiple accounts → keep the best one
#    GoogleDeepMind / DeepMind / GoogleAI → DeepMind
#    MetaAI / AIatMeta              → AIatMeta
#    NVIDIA / NVIDIAAI              → nvidia
#
# 2. Remove accounts that always return 400 (don't exist / private)
#    demaboris, Goodfellow_Marc, LangChainAI → removed
#
# 3. Size control: ~27 accounts is the sweet spot for TikHub free tier
#    More than 35 → 429 rate limit kicks in
