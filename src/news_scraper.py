"""Module to scrape investor relations news from company websites."""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import Optional, Dict, List
import logging
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
import re
import config

logger = logging.getLogger(__name__)


class NewsScraper:
    """Scrapes investor relations news from company websites."""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.headers = {
            'User-Agent': config.USER_AGENT
        }

    async def _init_session(self):
        """Initialize aiohttp session."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)
            self.session = aiohttp.ClientSession(headers=self.headers, timeout=timeout)

    async def _find_ir_page(self, website: str) -> Optional[str]:
        """Find the investor relations page URL."""
        if not website:
            return None

        await self._init_session()

        # Common IR page patterns
        ir_paths = [
            '/investors',
            '/investor-relations',
            '/ir',
            '/investor',
            '/investorrelations',
            '/shareholders',
            '/investors/news',
            '/investors/press-releases',
            '/newsroom/press-releases',
            '/news',
            '/press-releases',
            '/media/press-releases'
        ]

        # Try the main website first
        try:
            async with self.session.get(website, allow_redirects=True) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')

                    # Look for investor relations links
                    for link in soup.find_all('a', href=True):
                        href = link['href'].lower()
                        text = link.get_text().lower()

                        if any(keyword in text for keyword in ['investor', 'ir ', 'shareholders']):
                            full_url = urljoin(website, link['href'])
                            return full_url

                    # If no link found, try common paths
                    for path in ir_paths:
                        test_url = urljoin(website, path)
                        try:
                            async with self.session.head(test_url, allow_redirects=True) as test_response:
                                if test_response.status == 200:
                                    return test_url
                        except:
                            continue

        except Exception as e:
            logger.debug(f"Error finding IR page for {website}: {e}")

        return website  # Fall back to main website

    async def _extract_news_items(self, url: str, html: str) -> List[Dict]:
        """Extract news items from HTML."""
        soup = BeautifulSoup(html, 'lxml')
        news_items = []

        # Look for common news/press release patterns
        news_containers = []

        # Try to find news sections
        for tag in soup.find_all(['article', 'div', 'section']):
            class_str = ' '.join(tag.get('class', [])).lower()
            id_str = tag.get('id', '').lower()

            if any(keyword in class_str or keyword in id_str
                   for keyword in ['news', 'press', 'release', 'article', 'post']):
                news_containers.append(tag)

        # If no specific containers found, look for all links
        if not news_containers:
            news_containers = [soup]

        for container in news_containers[:10]:  # Limit to first 10 containers
            # Find all links that might be news items
            for link in container.find_all('a', href=True)[:20]:  # Limit links per container
                href = link['href']
                text = link.get_text(strip=True)

                # Skip empty or very short links
                if not text or len(text) < 10:
                    continue

                # Look for date patterns nearby
                date_pattern = r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b'

                parent_text = link.parent.get_text() if link.parent else ""
                date_match = re.search(date_pattern, parent_text)

                news_date = date_match.group(0) if date_match else None

                # Build full URL
                full_url = urljoin(url, href)

                news_items.append({
                    'title': text[:200],  # Limit title length
                    'url': full_url,
                    'date': news_date,
                    'source_page': url
                })

        # Deduplicate by URL
        seen_urls = set()
        unique_items = []
        for item in news_items:
            if item['url'] not in seen_urls:
                seen_urls.add(item['url'])
                unique_items.append(item)

        return unique_items[:10]  # Return top 10 news items

    async def scrape_news(self, ticker: str, website: str) -> Dict:
        """Scrape news for a single company."""
        try:
            await self._init_session()

            # Find IR page
            ir_url = await self._find_ir_page(website)

            if not ir_url:
                return {
                    'ticker': ticker,
                    'website': website,
                    'ir_page': None,
                    'news_found': False,
                    'news_items': [],
                    'error': 'No IR page found'
                }

            # Fetch IR page
            async with self.session.get(ir_url, allow_redirects=True) as response:
                if response.status != 200:
                    return {
                        'ticker': ticker,
                        'website': website,
                        'ir_page': ir_url,
                        'news_found': False,
                        'news_items': [],
                        'error': f'HTTP {response.status}'
                    }

                html = await response.text()

            # Extract news items
            news_items = await self._extract_news_items(ir_url, html)

            return {
                'ticker': ticker,
                'website': website,
                'ir_page': ir_url,
                'news_found': len(news_items) > 0,
                'news_items': news_items,
                'news_count': len(news_items),
                'scraped_at': datetime.now().isoformat()
            }

        except asyncio.TimeoutError:
            logger.warning(f"Timeout scraping news for {ticker}")
            return {
                'ticker': ticker,
                'website': website,
                'news_found': False,
                'news_items': [],
                'error': 'Timeout'
            }
        except Exception as e:
            logger.error(f"Error scraping news for {ticker}: {e}")
            return {
                'ticker': ticker,
                'website': website,
                'news_found': False,
                'news_items': [],
                'error': str(e)
            }

    async def scrape_news_batch(self, stocks_data: Dict[str, Dict]) -> Dict[str, Dict]:
        """Scrape news for multiple stocks with rate limiting."""
        results = {}
        batch_size = config.MAX_CONCURRENT_REQUESTS

        stocks_list = list(stocks_data.items())

        for i in range(0, len(stocks_list), batch_size):
            batch = stocks_list[i:i + batch_size]
            logger.info(f"Scraping news batch {i // batch_size + 1}/{(len(stocks_list) + batch_size - 1) // batch_size}")

            tasks = [
                self.scrape_news(ticker, data.get('website', ''))
                for ticker, data in batch
            ]

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for (ticker, _), result in zip(batch, batch_results):
                if isinstance(result, dict):
                    results[ticker] = result
                elif isinstance(result, Exception):
                    logger.error(f"Exception for {ticker}: {result}")
                    results[ticker] = {
                        'ticker': ticker,
                        'news_found': False,
                        'news_items': [],
                        'error': str(result)
                    }

            # Rate limiting between batches
            if i + batch_size < len(stocks_list):
                await asyncio.sleep(config.BATCH_DELAY)

        return results

    async def cleanup(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
