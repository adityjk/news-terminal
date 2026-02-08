"""
NewsAPI Client for fetching news articles.
"""

import requests
from typing import Optional
from datetime import datetime


class NewsAPIClient:
    """Client for interacting with NewsAPI.org"""
    
    BASE_URL = "https://newsapi.org/v2"
    
    CATEGORIES = {
        "1": ("general", "Headlines"),
        "2": ("business", "Business"),
        "3": ("technology", "Technology"),
        "4": ("sports", "Sports"),
        "5": ("health", "Health"),
    }
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "X-Api-Key": api_key,
            "User-Agent": "NewsTerminal/1.0"
        })
    
    def get_top_headlines(
        self,
        category: str = "general",
        country: str = "us",
        page_size: int = 20
    ) -> dict:
        """
        Fetch top headlines.
        
        Args:
            category: News category (general, business, technology, sports, health, etc.)
            country: Country code (us, id, gb, etc.)
            page_size: Number of articles to fetch
        
        Returns:
            dict with 'status', 'totalResults', and 'articles'
        """
        try:
            response = self.session.get(
                f"{self.BASE_URL}/top-headlines",
                params={
                    "category": category,
                    "country": country,
                    "pageSize": page_size
                },
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "status": "error",
                "message": str(e),
                "articles": []
            }
    
    def search_news(
        self,
        query: str,
        page_size: int = 20,
        sort_by: str = "publishedAt"
    ) -> dict:
        """
        Search news articles by keyword.
        
        Args:
            query: Search query
            page_size: Number of articles to fetch
            sort_by: Sort order (publishedAt, relevancy, popularity)
        
        Returns:
            dict with 'status', 'totalResults', and 'articles'
        """
        try:
            response = self.session.get(
                f"{self.BASE_URL}/everything",
                params={
                    "q": query,
                    "pageSize": page_size,
                    "sortBy": sort_by,
                    "language": "en"
                },
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "status": "error",
                "message": str(e),
                "articles": []
            }
    
    @staticmethod
    def format_article(article: dict) -> dict:
        """Format article data for display."""
        published = article.get("publishedAt", "")
        if published:
            try:
                dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
                published = dt.strftime("%H:%M • %d %b %Y")
            except ValueError:
                pass
        
        return {
            "title": article.get("title", "No title"),
            "description": article.get("description", "No description available."),
            "source": article.get("source", {}).get("name", "Unknown"),
            "url": article.get("url", ""),
            "published": published,
            "author": article.get("author", "Unknown"),
            "content": article.get("content", "")
        }
