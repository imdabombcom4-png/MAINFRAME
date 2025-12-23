"""Module to check stock price changes."""

import yfinance as yf
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor
import config

logger = logging.getLogger(__name__)


class PriceChecker:
    """Checks stock price changes using Yahoo Finance."""

    def __init__(self, days_back: int = config.PRICE_CHECK_DAYS):
        self.days_back = days_back
        self.executor = ThreadPoolExecutor(max_workers=config.MAX_CONCURRENT_REQUESTS)

    def _fetch_price_data(self, ticker: str) -> Optional[Dict]:
        """Fetch price data for a single ticker (synchronous)."""
        try:
            stock = yf.Ticker(ticker)

            # Get historical data for the last N days plus buffer
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.days_back + 5)

            hist = stock.history(start=start_date, end=end_date)

            if hist.empty or len(hist) < 2:
                logger.warning(f"Insufficient data for {ticker}")
                return None

            # Get current (most recent) and previous prices
            current_price = hist['Close'].iloc[-1]
            previous_price = hist['Close'].iloc[-(self.days_back + 1)] if len(hist) > self.days_back else hist['Close'].iloc[0]

            # Calculate percentage change
            price_change = ((current_price - previous_price) / previous_price) * 100

            # Get company info
            info = stock.info
            company_name = info.get('longName', ticker)
            website = info.get('website', '')

            return {
                'ticker': ticker,
                'company_name': company_name,
                'website': website,
                'current_price': float(current_price),
                'previous_price': float(previous_price),
                'price_change_pct': float(price_change),
                'abs_price_change_pct': abs(float(price_change)),
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error fetching price data for {ticker}: {e}")
            return None

    async def check_price(self, ticker: str) -> Optional[Dict]:
        """Asynchronously check price for a ticker."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._fetch_price_data, ticker)

    async def check_prices_batch(self, tickers: list) -> Dict[str, Dict]:
        """Check prices for multiple tickers concurrently."""
        tasks = [self.check_price(ticker) for ticker in tickers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        price_data = {}
        for ticker, result in zip(tickers, results):
            if isinstance(result, dict) and result is not None:
                price_data[ticker] = result
            elif isinstance(result, Exception):
                logger.error(f"Exception for {ticker}: {result}")

        return price_data

    def filter_by_threshold(self, price_data: Dict[str, Dict], threshold: float = config.PRICE_CHANGE_THRESHOLD) -> Dict[str, Dict]:
        """Filter stocks where price change is below threshold."""
        threshold_pct = threshold * 100  # Convert to percentage

        filtered = {
            ticker: data
            for ticker, data in price_data.items()
            if data['abs_price_change_pct'] < threshold_pct
        }

        logger.info(f"Filtered {len(filtered)}/{len(price_data)} stocks with price change < {threshold_pct}%")
        return filtered

    def cleanup(self):
        """Cleanup resources."""
        self.executor.shutdown(wait=True)
