#!/usr/bin/env python3
"""
Stock News Scanner Bot

Scans NASDAQ and S&P 500 stocks for investor relations news
and filters by price change threshold.
"""

import asyncio
import argparse
from datetime import datetime
from tqdm.asyncio import tqdm
import logging

from src.ticker_fetcher import TickerFetcher
from src.price_checker import PriceChecker
from src.news_scraper import NewsScraper
from src.utils import (
    setup_logging,
    ensure_directories,
    save_results_json,
    save_results_csv,
    merge_results,
    print_summary
)
import config

logger = logging.getLogger(__name__)


class StockNewsBot:
    """Main orchestrator for the stock news scanner bot."""

    def __init__(self, price_threshold: float = config.PRICE_CHANGE_THRESHOLD, max_stocks: int = None):
        self.price_threshold = price_threshold
        self.max_stocks = max_stocks
        self.ticker_fetcher = TickerFetcher()
        self.price_checker = PriceChecker()
        self.news_scraper = NewsScraper()

    async def run(self):
        """Run the complete scanning process."""
        logger.info("Starting Stock News Scanner Bot")
        logger.info("=" * 80)

        # Step 1: Fetch all tickers
        logger.info("Step 1: Fetching stock tickers from NASDAQ and S&P 500...")
        ticker_info = await self.ticker_fetcher.fetch_all_tickers()
        all_tickers = self.ticker_fetcher.get_tickers_list()

        if not all_tickers:
            logger.error("No tickers fetched. Exiting.")
            return

        # Limit if specified
        if self.max_stocks:
            all_tickers = all_tickers[:self.max_stocks]
            logger.info(f"Limited to {self.max_stocks} stocks for testing")

        logger.info(f"Found {len(all_tickers)} unique tickers")

        # Step 2: Check prices for all stocks
        logger.info("\nStep 2: Checking stock prices...")
        logger.info(f"Fetching price data for {len(all_tickers)} stocks...")

        # Process in batches with progress bar
        batch_size = config.MAX_CONCURRENT_REQUESTS
        all_price_data = {}

        with tqdm(total=len(all_tickers), desc="Fetching prices") as pbar:
            for i in range(0, len(all_tickers), batch_size):
                batch = all_tickers[i:i + batch_size]
                batch_data = await self.price_checker.check_prices_batch(batch)
                all_price_data.update(batch_data)
                pbar.update(len(batch))

                # Small delay between batches
                if i + batch_size < len(all_tickers):
                    await asyncio.sleep(1)

        logger.info(f"Successfully fetched price data for {len(all_price_data)} stocks")

        # Step 3: Filter by price change threshold
        logger.info(f"\nStep 3: Filtering stocks with price change < {self.price_threshold * 100}%...")
        filtered_stocks = self.price_checker.filter_by_threshold(all_price_data, self.price_threshold)

        if not filtered_stocks:
            logger.warning("No stocks match the price change criteria!")
            return

        logger.info(f"Found {len(filtered_stocks)} stocks matching criteria")

        # Step 4: Scrape news for filtered stocks
        logger.info("\nStep 4: Scraping investor relations news...")
        logger.info(f"Checking {len(filtered_stocks)} company websites for news...")

        news_data = await self.news_scraper.scrape_news_batch(filtered_stocks)

        logger.info(f"Completed news scraping for {len(news_data)} stocks")

        # Step 5: Merge and save results
        logger.info("\nStep 5: Merging results and saving...")
        merged_results = merge_results(filtered_stocks, news_data)

        # Save to JSON
        json_file = save_results_json({
            'scan_date': datetime.now().isoformat(),
            'total_tickers_scanned': len(all_tickers),
            'price_threshold_pct': self.price_threshold * 100,
            'stocks_matching_criteria': len(filtered_stocks),
            'results': merged_results
        })

        # Save to CSV
        csv_file = save_results_csv(merged_results)

        # Print summary
        print_summary(merged_results)

        logger.info(f"\nResults saved to:")
        logger.info(f"  JSON: {json_file}")
        logger.info(f"  CSV:  {csv_file}")

        # Cleanup
        await self.cleanup()

    async def cleanup(self):
        """Cleanup resources."""
        self.price_checker.cleanup()
        await self.news_scraper.cleanup()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Stock News Scanner Bot - Scan NASDAQ and S&P 500 for IR news'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=config.PRICE_CHANGE_THRESHOLD,
        help=f'Price change threshold (default: {config.PRICE_CHANGE_THRESHOLD})'
    )
    parser.add_argument(
        '--max-stocks',
        type=int,
        default=None,
        help='Maximum number of stocks to scan (for testing)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        default=config.VERBOSE,
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Setup
    setup_logging(args.verbose)
    ensure_directories()

    # Run bot
    bot = StockNewsBot(price_threshold=args.threshold, max_stocks=args.max_stocks)
    await bot.run()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nBot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
