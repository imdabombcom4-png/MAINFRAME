# Stock News Scanner Bot

An efficient bot that scans NASDAQ and S&P 500 stocks for investor relations news and filters by price change threshold.

## Features

- **Comprehensive Coverage**: Scans all NASDAQ-100 and S&P 500 stocks
- **Price Filtering**: Identifies stocks with price changes below a configurable threshold (default: 5%)
- **News Detection**: Automatically finds and scrapes investor relations pages for recent news
- **Efficient Processing**: Uses async operations and batching for optimal performance
- **Multiple Output Formats**: Saves results as both JSON and CSV
- **Rate Limiting**: Built-in delays to avoid overwhelming servers
- **Progress Tracking**: Real-time progress bars and detailed logging

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/imdabombcom4-png/MAINFRAME
cd MAINFRAME
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Run the bot with default settings (5% price change threshold):

```bash
python main.py
```

### Advanced Options

```bash
# Custom price change threshold (e.g., 3%)
python main.py --threshold 0.03

# Test with limited stocks (useful for testing)
python main.py --max-stocks 10

# Enable verbose logging
python main.py --verbose

# Combine options
python main.py --threshold 0.05 --max-stocks 50 --verbose
```

### Command-line Arguments

- `--threshold`: Price change threshold as decimal (default: 0.05 = 5%)
- `--max-stocks`: Maximum number of stocks to scan (useful for testing)
- `--verbose`: Enable detailed logging output

## Configuration

Edit `config.py` to customize bot behavior:

```python
# Price change threshold (as decimal)
PRICE_CHANGE_THRESHOLD = 0.05  # 5%

# Time period for price comparison (days)
PRICE_CHECK_DAYS = 1

# Maximum concurrent requests
MAX_CONCURRENT_REQUESTS = 10

# Request timeout (seconds)
REQUEST_TIMEOUT = 30

# Delay between batches (seconds)
BATCH_DELAY = 2
```

## Output

The bot generates two output files in the `output/` directory:

### JSON Output
Contains complete data including:
- Scan metadata (date, threshold, total stocks)
- Detailed results for each stock:
  - Ticker symbol and company name
  - Current and previous prices
  - Price change percentage
  - Company website and IR page
  - News items (titles, URLs, dates)

Example: `output/stock_news_scan_20231215_143022.json`

### CSV Output
Flattened data suitable for spreadsheet analysis:
- Basic stock information
- Price data and change percentage
- News summary (count, top news item)

Example: `output/stock_news_scan_20231215_143022.csv`

## How It Works

1. **Fetch Tickers**: Retrieves current NASDAQ-100 and S&P 500 stock lists from Wikipedia
2. **Check Prices**: Uses Yahoo Finance to get current and historical prices
3. **Filter Stocks**: Identifies stocks with price changes below the threshold
4. **Scrape News**: Visits company websites to find investor relations pages and extract news
5. **Save Results**: Outputs data in JSON and CSV formats with a summary

## Architecture

```
MAINFRAME/
├── main.py                 # Main orchestrator
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── src/
│   ├── ticker_fetcher.py  # Fetches stock tickers
│   ├── price_checker.py   # Checks price changes
│   ├── news_scraper.py    # Scrapes IR news
│   └── utils.py           # Helper functions
└── output/                # Results directory
```

## Performance

- **Async Operations**: Concurrent requests for faster processing
- **Batching**: Processes stocks in configurable batches
- **Rate Limiting**: Automatic delays to respect server limits
- **Caching**: Avoids redundant requests

Typical scan times:
- ~500-600 stocks: 10-15 minutes
- Limited scan (50 stocks): 1-2 minutes

## Limitations

- Web scraping is subject to website structure changes
- Some companies may not have easily accessible IR pages
- Rate limiting may slow down large scans
- Yahoo Finance data depends on service availability

## Troubleshooting

### No tickers found
- Check internet connection
- Wikipedia may be temporarily unavailable

### Price data errors
- Yahoo Finance may be experiencing issues
- Some tickers may have been delisted

### News scraping timeouts
- Company websites may be slow or blocking requests
- Increase `REQUEST_TIMEOUT` in config.py

### Too many requests errors
- Increase `BATCH_DELAY` in config.py
- Reduce `MAX_CONCURRENT_REQUESTS`

## Example Output

```
================================================================================
STOCK NEWS SCANNER - SUMMARY
================================================================================
Total stocks scanned: 547
Stocks with news found: 234
Stocks without news: 313
================================================================================

Top 10 stocks with news:
--------------------------------------------------------------------------------

1. AAPL - Apple Inc.
   Price change: 0.43%
   News items found: 8
   Latest: Apple Announces Q4 2023 Financial Results...
   URL: https://investor.apple.com/news/press-release-details/2023/...
```

## License

This project is for educational and research purposes.
