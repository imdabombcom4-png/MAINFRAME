"""
News Scraper Module

This module scrapes investor relations news from company websites.
Optimized for high concurrency and handling problematic websites.
"""

import asyncio
import aiohttp
import logging
from typing import List, Dict, Optional
from datetime import datetime
import ssl

logger = logging.getLogger(__name__)


class NewsScraper:
    """Scrapes news from company investor relations pages."""

    def __init__(self, max_concurrent: int = 25, timeout: int = 15):
        """
        Initialize the news scraper.

        Args:
            max_concurrent: Maximum number of concurrent requests (default: 25)
            timeout: Timeout per request in seconds (default: 15)
        """
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(max_concurrent)

        # User-Agent to avoid bot detection
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
        }

    async def _create_session(self) -> aiohttp.ClientSession:
        """
        Create an aiohttp session with optimized settings.

        Returns:
            Configured ClientSession
        """
        # Create SSL context that's more lenient
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        # Create connector with increased limits
        connector = aiohttp.TCPConnector(
            limit=self.max_concurrent * 2,
            limit_per_host=5,
            ttl_dns_cache=300,
            ssl=ssl_context,
            force_close=False,
        )

        # Create timeout settings
        timeout = aiohttp.ClientTimeout(
            total=self.timeout,
            connect=10,
            sock_connect=10,
            sock_read=self.timeout
        )

        # Create session with increased header size limit
        return aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.headers,
            max_field_size=32768,  # 32KB instead of default 8KB
            max_line_size=16384,   # 16KB instead of default 8KB
        )

    async def _scrape_single_company(
        self,
        session: aiohttp.ClientSession,
        ticker: str,
        url: str
    ) -> Dict:
        """
        Scrape news for a single company.

        Args:
            session: aiohttp session
            ticker: Stock ticker symbol
            url: Company investor relations URL

        Returns:
            Dictionary with ticker, url, and scraped data
        """
        async with self.semaphore:  # Limit concurrent requests
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        # Basic news extraction (can be enhanced)
                        news_count = html.lower().count('press release') + html.lower().count('news')

                        logger.debug(f"Successfully scraped {ticker} - found {news_count} potential news items")

                        return {
                            'ticker': ticker,
                            'url': url,
                            'status': 'success',
                            'news_count': news_count,
                            'html_length': len(html),
                            'timestamp': datetime.now().isoformat()
                        }
                    else:
                        logger.warning(f"HTTP {response.status} for {ticker} at {url}")
                        return {
                            'ticker': ticker,
                            'url': url,
                            'status': 'error',
                            'error': f'HTTP {response.status}'
                        }

            except asyncio.TimeoutError:
                logger.warning(f"Timeout scraping news for {ticker}")
                return {
                    'ticker': ticker,
                    'url': url,
                    'status': 'timeout',
                    'error': 'Request timeout'
                }

            except aiohttp.ClientError as e:
                error_msg = str(e)
                # Truncate long error messages
                if len(error_msg) > 200:
                    error_msg = error_msg[:200] + '...'
                logger.error(f"Error scraping news for {ticker}: {error_msg}")
                return {
                    'ticker': ticker,
                    'url': url,
                    'status': 'error',
                    'error': error_msg
                }

            except Exception as e:
                logger.error(f"Unexpected error scraping {ticker}: {type(e).__name__}: {str(e)[:100]}")
                return {
                    'ticker': ticker,
                    'url': url,
                    'status': 'error',
                    'error': f'{type(e).__name__}: {str(e)[:100]}'
                }

    async def scrape_news(
        self,
        ticker_url_pairs: List[tuple]
    ) -> List[Dict]:
        """
        Scrape news for multiple companies concurrently.

        Args:
            ticker_url_pairs: List of (ticker, url) tuples

        Returns:
            List of dictionaries with scraping results
        """
        if not ticker_url_pairs:
            logger.warning("No ticker-URL pairs provided")
            return []

        logger.info(f"Starting scrape for {len(ticker_url_pairs)} companies with max {self.max_concurrent} concurrent requests")

        async with await self._create_session() as session:
            # Create all tasks at once - semaphore will limit concurrency
            tasks = [
                self._scrape_single_company(session, ticker, url)
                for ticker, url in ticker_url_pairs
            ]

            # Run all tasks concurrently with progress tracking
            results = []
            completed = 0
            total = len(tasks)

            # Process tasks as they complete
            for coro in asyncio.as_completed(tasks):
                result = await coro
                results.append(result)
                completed += 1

                # Log progress every 50 completions
                if completed % 50 == 0 or completed == total:
                    success_count = sum(1 for r in results if r.get('status') == 'success')
                    logger.info(
                        f"Progress: {completed}/{total} "
                        f"({completed/total*100:.1f}%) - "
                        f"{success_count} successful"
                    )

        # Summary statistics
        success_count = sum(1 for r in results if r.get('status') == 'success')
        timeout_count = sum(1 for r in results if r.get('status') == 'timeout')
        error_count = sum(1 for r in results if r.get('status') == 'error')

        logger.info(
            f"Scraping complete: {success_count} successful, "
            f"{timeout_count} timeouts, {error_count} errors out of {total} total"
        )

        return results

    async def scrape_news_batch(
        self,
        ticker_url_pairs: List[tuple],
        batch_size: int = 100
    ) -> List[Dict]:
        """
        Scrape news in batches (useful for very large lists).

        Args:
            ticker_url_pairs: List of (ticker, url) tuples
            batch_size: Number of companies per batch (default: 100)

        Returns:
            List of dictionaries with scraping results
        """
        all_results = []
        total_batches = (len(ticker_url_pairs) + batch_size - 1) // batch_size

        for i in range(0, len(ticker_url_pairs), batch_size):
            batch_num = i // batch_size + 1
            batch = ticker_url_pairs[i:i + batch_size]

            logger.info(f"Scraping batch {batch_num}/{total_batches} ({len(batch)} companies)")

            batch_results = await self.scrape_news(batch)
            all_results.extend(batch_results)

            # Small delay between batches to be respectful
            if i + batch_size < len(ticker_url_pairs):
                await asyncio.sleep(1)

        return all_results


async def main():
    """Test the news scraper."""
    # Example usage
    scraper = NewsScraper(max_concurrent=25, timeout=15)

    test_companies = [
        ('AAPL', 'https://investor.apple.com'),
        ('MSFT', 'https://www.microsoft.com/en-us/investor'),
        ('GOOGL', 'https://abc.xyz/investor/'),
    ]

    print("=" * 60)
    print("NEWS SCRAPER TEST")
    print("=" * 60)
    print()

    results = await scraper.scrape_news(test_companies)

    print("\nResults:")
    for result in results:
        status = result.get('status', 'unknown')
        ticker = result.get('ticker', 'N/A')
        print(f"  {ticker}: {status}")

    print("=" * 60)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())
