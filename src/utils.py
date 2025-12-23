"""Utility functions for the stock news scanner bot."""

import json
import csv
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import config

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = config.VERBOSE):
    """Setup logging configuration."""
    level = logging.INFO if verbose else logging.WARNING

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def ensure_directories():
    """Ensure required directories exist."""
    Path(config.OUTPUT_DIR).mkdir(exist_ok=True)
    Path(config.CACHE_DIR).mkdir(exist_ok=True)


def save_results_json(data: Dict, filename: str = None):
    """Save results to JSON file."""
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"stock_news_scan_{timestamp}.json"

    filepath = Path(config.OUTPUT_DIR) / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"Results saved to {filepath}")
    return filepath


def save_results_csv(data: List[Dict], filename: str = None):
    """Save results to CSV file."""
    if not data:
        logger.warning("No data to save to CSV")
        return None

    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"stock_news_scan_{timestamp}.csv"

    filepath = Path(config.OUTPUT_DIR) / filename

    # Flatten the data for CSV
    flattened = []
    for item in data:
        flat_item = {
            'ticker': item.get('ticker', ''),
            'company_name': item.get('company_name', ''),
            'website': item.get('website', ''),
            'current_price': item.get('current_price', ''),
            'previous_price': item.get('previous_price', ''),
            'price_change_pct': item.get('price_change_pct', ''),
            'ir_page': item.get('ir_page', ''),
            'news_found': item.get('news_found', False),
            'news_count': item.get('news_count', 0),
            'top_news_title': item.get('news_items', [{}])[0].get('title', '') if item.get('news_items') else '',
            'top_news_url': item.get('news_items', [{}])[0].get('url', '') if item.get('news_items') else '',
            'top_news_date': item.get('news_items', [{}])[0].get('date', '') if item.get('news_items') else '',
        }
        flattened.append(flat_item)

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        if flattened:
            writer = csv.DictWriter(f, fieldnames=flattened[0].keys())
            writer.writeheader()
            writer.writerows(flattened)

    logger.info(f"Results saved to {filepath}")
    return filepath


def merge_results(price_data: Dict[str, Dict], news_data: Dict[str, Dict]) -> List[Dict]:
    """Merge price and news data."""
    merged = []

    for ticker in price_data.keys():
        item = {
            **price_data[ticker],
            **news_data.get(ticker, {
                'news_found': False,
                'news_items': [],
                'news_count': 0
            })
        }
        merged.append(item)

    return merged


def print_summary(results: List[Dict]):
    """Print a summary of results."""
    total = len(results)
    with_news = sum(1 for r in results if r.get('news_found', False))

    print("\n" + "=" * 80)
    print("STOCK NEWS SCANNER - SUMMARY")
    print("=" * 80)
    print(f"Total stocks scanned: {total}")
    print(f"Stocks with news found: {with_news}")
    print(f"Stocks without news: {total - with_news}")
    print("=" * 80)

    if with_news > 0:
        print("\nTop 10 stocks with news:")
        print("-" * 80)

        news_stocks = [r for r in results if r.get('news_found', False)]
        news_stocks.sort(key=lambda x: x.get('news_count', 0), reverse=True)

        for i, stock in enumerate(news_stocks[:10], 1):
            print(f"\n{i}. {stock.get('ticker', 'N/A')} - {stock.get('company_name', 'N/A')}")
            print(f"   Price change: {stock.get('price_change_pct', 0):.2f}%")
            print(f"   News items found: {stock.get('news_count', 0)}")
            if stock.get('news_items'):
                top_news = stock['news_items'][0]
                print(f"   Latest: {top_news.get('title', 'N/A')[:60]}...")
                print(f"   URL: {top_news.get('url', 'N/A')}")

        print("\n" + "=" * 80)
