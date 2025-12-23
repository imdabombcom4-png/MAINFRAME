"""Module to fetch NASDAQ and S&P 500 stock tickers."""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict, Set
import logging
import pandas as pd

logger = logging.getLogger(__name__)


class TickerFetcher:
    """Fetches stock tickers from NASDAQ and S&P 500."""

    def __init__(self):
        self.tickers: Set[str] = set()
        self.ticker_info: Dict[str, Dict] = {}

    async def fetch_sp500_tickers(self) -> List[str]:
        """Fetch S&P 500 tickers from Wikipedia."""
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    html = await response.text()

            soup = BeautifulSoup(html, 'lxml')
            table = soup.find('table', {'id': 'constituents'})

            if not table:
                logger.error("Could not find S&P 500 table")
                return []

            tickers = []
            for row in table.find_all('tr')[1:]:  # Skip header
                cols = row.find_all('td')
                if cols:
                    ticker = cols[0].text.strip()
                    name = cols[1].text.strip()
                    sector = cols[2].text.strip() if len(cols) > 2 else ""

                    tickers.append(ticker)
                    self.ticker_info[ticker] = {
                        'name': name,
                        'sector': sector,
                        'index': 'S&P 500'
                    }

            logger.info(f"Fetched {len(tickers)} S&P 500 tickers")
            return tickers

        except Exception as e:
            logger.error(f"Error fetching S&P 500 tickers: {e}")
            return []

    async def fetch_nasdaq_tickers(self) -> List[str]:
        """Fetch NASDAQ tickers from Wikipedia."""
        url = "https://en.wikipedia.org/wiki/Nasdaq-100"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    html = await response.text()

            soup = BeautifulSoup(html, 'lxml')
            table = soup.find('table', {'id': 'constituents'})

            if not table:
                logger.error("Could not find NASDAQ-100 table")
                return []

            tickers = []
            for row in table.find_all('tr')[1:]:  # Skip header
                cols = row.find_all('td')
                if cols:
                    ticker = cols[1].text.strip()
                    name = cols[0].text.strip()
                    sector = cols[2].text.strip() if len(cols) > 2 else ""

                    tickers.append(ticker)
                    if ticker not in self.ticker_info:  # Don't overwrite S&P 500 info
                        self.ticker_info[ticker] = {
                            'name': name,
                            'sector': sector,
                            'index': 'NASDAQ-100'
                        }

            logger.info(f"Fetched {len(tickers)} NASDAQ-100 tickers")
            return tickers

        except Exception as e:
            logger.error(f"Error fetching NASDAQ tickers: {e}")
            return []

    async def fetch_all_tickers(self) -> Dict[str, Dict]:
        """Fetch all tickers from both indices."""
        sp500_task = self.fetch_sp500_tickers()
        nasdaq_task = self.fetch_nasdaq_tickers()

        sp500_tickers, nasdaq_tickers = await asyncio.gather(sp500_task, nasdaq_task)

        # Combine and deduplicate
        all_tickers = set(sp500_tickers + nasdaq_tickers)
        self.tickers = all_tickers

        logger.info(f"Total unique tickers: {len(all_tickers)}")

        return self.ticker_info

    def get_tickers_list(self) -> List[str]:
        """Get sorted list of all tickers."""
        return sorted(list(self.tickers))
