"""
Article scraper with fallback search to fetch full content from multiple sources.
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional, List, Tuple
import re
import urllib.parse


class ArticleScraper:
    """Scrapes full article content from URLs with fallback search."""
    
    # Common content selectors used by news sites
    CONTENT_SELECTORS = [
        'article',
        '[class*="article-body"]',
        '[class*="article-content"]',
        '[class*="post-content"]',
        '[class*="entry-content"]',
        '[class*="story-body"]',
        '[class*="content-body"]',
        '[itemprop="articleBody"]',
        '.article__body',
        '.article-text',
        '.story-content',
        'main',
    ]
    
    # Elements to remove
    REMOVE_SELECTORS = [
        'script', 'style', 'nav', 'header', 'footer', 'aside',
        '.advertisement', '.ad', '.ads', '.social-share',
        '.related-articles', '.comments', '.sidebar',
        '[class*="newsletter"]', '[class*="subscribe"]',
        '[class*="popup"]', '[class*="modal"]',
    ]
    
    def __init__(self):
        self.session = requests.Session()
        # Use mobile user-agent for better compatibility
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        # Disable SSL verification for Termux compatibility
        self.session.verify = False
        # Suppress SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def fetch_article(self, url: str, title: str = None) -> Tuple[Optional[str], str]:
        """
        Fetch article content, with fallback to alternative sources if blocked.
        
        Args:
            url: The primary article URL
            title: Article title for fallback search
            
        Returns:
            Tuple of (content, source_info) where source_info indicates the source
        """
        # Try primary URL first
        content = self._scrape_url(url)
        if content:
            return content, "original"
        
        # If failed and we have a title, search for alternative sources
        if title:
            alt_urls = self._search_alternative_sources(title)
            for alt_url in alt_urls:
                if alt_url != url:  # Don't retry the same URL
                    content = self._scrape_url(alt_url)
                    if content:
                        return content, f"alternative: {self._get_domain(alt_url)}"
        
        return None, "failed"
    
    def _scrape_url(self, url: str) -> Optional[str]:
        """Try to scrape content from a single URL."""
        if not url:
            return None
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # Try lxml first, fall back to html.parser
            try:
                soup = BeautifulSoup(response.text, 'lxml')
            except Exception:
                soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for selector in self.REMOVE_SELECTORS:
                for element in soup.select(selector):
                    element.decompose()
            
            # Try to find main content
            content = None
            for selector in self.CONTENT_SELECTORS:
                elements = soup.select(selector)
                if elements:
                    content = max(elements, key=lambda x: len(x.get_text()))
                    break
            
            if not content:
                content = soup.body if soup.body else soup
            
            text = self._extract_text(content)
            
            if len(text) < 100:
                return None
            
            return text
            
        except Exception:
            return None
    
    def _search_alternative_sources(self, title: str) -> List[str]:
        """
        Search for alternative sources using DuckDuckGo HTML.
        Returns list of alternative article URLs.
        """
        try:
            # Clean title for search
            search_query = re.sub(r'[^\w\s]', '', title)[:100]
            encoded_query = urllib.parse.quote(f"{search_query} news")
            
            # Use DuckDuckGo HTML version (no API key needed)
            search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Extract result URLs
            urls = []
            for link in soup.select('a.result__a'):
                href = link.get('href', '')
                # DuckDuckGo wraps URLs, extract the actual URL
                if 'uddg=' in href:
                    match = re.search(r'uddg=([^&]+)', href)
                    if match:
                        actual_url = urllib.parse.unquote(match.group(1))
                        if self._is_news_url(actual_url):
                            urls.append(actual_url)
                elif href.startswith('http'):
                    if self._is_news_url(href):
                        urls.append(href)
                
                if len(urls) >= 5:  # Limit to 5 alternatives
                    break
            
            return urls
            
        except Exception:
            return []
    
    def _is_news_url(self, url: str) -> bool:
        """Check if URL is likely a news article."""
        # Skip non-article pages
        skip_patterns = [
            'youtube.com', 'twitter.com', 'facebook.com', 'instagram.com',
            'reddit.com', 'wikipedia.org', 'amazon.com', 'ebay.com',
            '/search', '/category', '/tag/', '/author/'
        ]
        return not any(pattern in url.lower() for pattern in skip_patterns)
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc.replace('www.', '')
        except Exception:
            return "unknown"
    
    def _extract_text(self, element) -> str:
        """Extract clean text from HTML element."""
        paragraphs = element.find_all(['p', 'h2', 'h3', 'blockquote'])
        
        if paragraphs:
            texts = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 20:
                    texts.append(text)
            return '\n\n'.join(texts)
        else:
            text = element.get_text(separator='\n', strip=True)
            text = re.sub(r'\n{3,}', '\n\n', text)
            return text
