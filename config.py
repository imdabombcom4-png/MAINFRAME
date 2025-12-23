"""Configuration settings for the stock news scanner bot."""

# Price change threshold (as decimal, e.g., 0.05 = 5%)
PRICE_CHANGE_THRESHOLD = 0.05

# Time period for price change calculation (in days)
PRICE_CHECK_DAYS = 1  # Compare to previous day

# Maximum concurrent requests
MAX_CONCURRENT_REQUESTS = 10

# Request timeout in seconds
REQUEST_TIMEOUT = 30

# Rate limiting: delay between batches (seconds)
BATCH_DELAY = 2

# Output directory
OUTPUT_DIR = "output"

# Cache directory
CACHE_DIR = "cache"

# User agent for web requests
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Keywords to identify investor relations news
IR_KEYWORDS = [
    "investor relations",
    "press release",
    "news release",
    "earnings",
    "financial results",
    "quarterly results",
    "annual report",
    "sec filings",
    "investor news"
]

# Minimum news age (days) to consider "new"
MAX_NEWS_AGE_DAYS = 7

# Enable verbose logging
VERBOSE = True
