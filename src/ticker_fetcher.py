"""
Ticker Fetcher Module

This module fetches stock ticker symbols from Wikipedia.
It includes proper User-Agent headers and parser configuration
to avoid common scraping issues.
"""

import pandas as pd
import requests
from typing import List, Optional


class TickerFetcher:
    """Fetches stock ticker symbols from Wikipedia."""

    # User-Agent header to identify our bot to Wikipedia
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # Wikipedia URLs for different stock indices
    SP500_URL = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    NASDAQ100_URL = 'https://en.wikipedia.org/wiki/Nasdaq-100'
    DOW30_URL = 'https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average'

    def __init__(self):
        """Initialize the TickerFetcher."""
        pass

    def fetch_sp500_tickers(self) -> List[str]:
        """
        Fetch S&P 500 ticker symbols from Wikipedia.

        Returns:
            List of ticker symbols (e.g., ['AAPL', 'MSFT', ...])
        """
        try:
            # Read HTML tables with proper parser and headers
            tables = pd.read_html(
                self.SP500_URL,
                attrs={'id': 'constituents'},
                flavor='lxml',
                storage_options=self.HEADERS
            )

            # The first table contains the S&P 500 constituents
            df = tables[0]

            # Extract the ticker symbols (usually in 'Symbol' column)
            tickers = df['Symbol'].tolist()

            print(f"✓ Successfully fetched {len(tickers)} S&P 500 tickers")
            return tickers

        except Exception as e:
            print(f"✗ Error fetching S&P 500 tickers: {e}")
            return []

    def fetch_nasdaq100_tickers(self) -> List[str]:
        """
        Fetch NASDAQ-100 ticker symbols from Wikipedia.

        Returns:
            List of ticker symbols
        """
        try:
            # Read HTML tables with proper parser and headers
            tables = pd.read_html(
                self.NASDAQ100_URL,
                flavor='lxml',
                storage_options=self.HEADERS
            )

            # Find the table with ticker symbols
            for table in tables:
                if 'Ticker' in table.columns or 'Symbol' in table.columns:
                    ticker_col = 'Ticker' if 'Ticker' in table.columns else 'Symbol'
                    tickers = table[ticker_col].tolist()
                    print(f"✓ Successfully fetched {len(tickers)} NASDAQ-100 tickers")
                    return tickers

            print("✗ Could not find ticker column in NASDAQ-100 tables")
            return []

        except Exception as e:
            print(f"✗ Error fetching NASDAQ-100 tickers: {e}")
            return []

    def fetch_dow30_tickers(self) -> List[str]:
        """
        Fetch Dow Jones Industrial Average (Dow 30) ticker symbols from Wikipedia.

        Returns:
            List of ticker symbols
        """
        try:
            # Read HTML tables with proper parser and headers
            tables = pd.read_html(
                self.DOW30_URL,
                flavor='lxml',
                storage_options=self.HEADERS
            )

            # Find the table with ticker symbols
            for table in tables:
                if 'Symbol' in table.columns or 'Ticker' in table.columns:
                    ticker_col = 'Symbol' if 'Symbol' in table.columns else 'Ticker'
                    tickers = table[ticker_col].tolist()
                    print(f"✓ Successfully fetched {len(tickers)} Dow 30 tickers")
                    return tickers

            print("✗ Could not find ticker column in Dow 30 tables")
            return []

        except Exception as e:
            print(f"✗ Error fetching Dow 30 tickers: {e}")
            return []

    def fetch_all_tickers(self) -> List[str]:
        """
        Fetch all available ticker symbols from supported indices.

        Returns:
            Combined list of unique ticker symbols
        """
        all_tickers = []

        # Fetch from all sources
        all_tickers.extend(self.fetch_sp500_tickers())
        all_tickers.extend(self.fetch_nasdaq100_tickers())
        all_tickers.extend(self.fetch_dow30_tickers())

        # Remove duplicates while preserving order
        unique_tickers = list(dict.fromkeys(all_tickers))

        print(f"\n✓ Total unique tickers: {len(unique_tickers)}")
        return unique_tickers


def main():
    """Test the ticker fetcher."""
    fetcher = TickerFetcher()

    print("=" * 60)
    print("STOCK TICKER FETCHER TEST")
    print("=" * 60)
    print()

    # Test S&P 500
    print("Fetching S&P 500 tickers...")
    sp500 = fetcher.fetch_sp500_tickers()
    print(f"Sample tickers: {sp500[:5]}")
    print()

    # Test NASDAQ-100
    print("Fetching NASDAQ-100 tickers...")
    nasdaq100 = fetcher.fetch_nasdaq100_tickers()
    print(f"Sample tickers: {nasdaq100[:5]}")
    print()

    # Test Dow 30
    print("Fetching Dow 30 tickers...")
    dow30 = fetcher.fetch_dow30_tickers()
    print(f"Sample tickers: {dow30[:5]}")
    print()

    # Fetch all
    print("Fetching all unique tickers...")
    all_tickers = fetcher.fetch_all_tickers()

    print("=" * 60)


if __name__ == "__main__":
    main()
