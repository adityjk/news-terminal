#!/usr/bin/env python3
"""
News Terminal - Bloomberg-inspired terminal news reader with clickable UI.
Main entry point using Textual.
"""

import sys
import os
import webbrowser

# Add parent directory to path for direct execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Button, Label, ListView, ListItem
from textual.binding import Binding
from textual import on
from rich.text import Text
from rich.panel import Panel

from news_terminal.config import get_api_key
from news_terminal.api import NewsAPIClient
from news_terminal.scraper import ArticleScraper


# Colors
ORANGE = "#FF9500"
SOFT_ORANGE = "#FFB347"


class NewsItem(ListItem):
    """A clickable news article item."""
    
    def __init__(self, article: dict, index: int):
        super().__init__()
        self.article = article
        self.index = index
    
    def compose(self) -> ComposeResult:
        title = self.article.get("title", "No title")[:75]
        if len(self.article.get("title", "")) > 75:
            title += "..."
        
        source = self.article.get("source", "Unknown")
        time = self.article.get("published", "")
        
        yield Static(f"[bold]{title}[/]\n[dim italic]{source}[/dim italic] • [dim]{time}[/dim]")


class CategoryButton(Button):
    """Category selection button."""
    
    def __init__(self, label: str, category_id: str, **kwargs):
        super().__init__(label, **kwargs)
        self.category_id = category_id


class ArticleDetail(Container):
    """Article detail view with full scrollable content."""
    
    def __init__(self, article: dict, full_content: str = None, source_info: str = "original"):
        self.article = article
        self.full_content = full_content
        self.source_info = source_info
        super().__init__()
    
    def compose(self) -> ComposeResult:
        content = Text()
        content.append(self.article.get("title", "No title"), style=f"bold {ORANGE}")
        content.append("\n\n")
        content.append("Source: ", style="bold dim")
        content.append(self.article.get("source", "Unknown"), style=SOFT_ORANGE)
        content.append("  •  ", style="dim")
        content.append(self.article.get("published", ""), style="dim")
        
        if self.article.get("author") and self.article["author"] != "Unknown":
            content.append("\n")
            content.append("Author: ", style="bold dim")
            content.append(self.article["author"])
        
        # Show source info if from alternative source
        if self.source_info and self.source_info.startswith("alternative"):
            content.append("\n")
            content.append("🔄 Content from: ", style="bold dim")
            content.append(self.source_info.replace("alternative: ", ""), style="cyan")
        
        content.append("\n")
        content.append("─" * 60, style="dim")
        content.append("\n\n")
        
        # Show full content if available, otherwise description
        if self.full_content:
            content.append(self.full_content)
        else:
            desc = self.article.get("description", "No description available.")
            if desc:
                content.append(desc)
            content.append("\n\n")
            content.append("[Could not fetch full article - try Open in Browser]", style="dim italic")
        
        content.append("\n\n")
        content.append("─" * 60, style="dim")
        content.append("\n")
        content.append("🔗 ", style="dim")
        content.append(self.article.get("url", ""), style=f"underline {SOFT_ORANGE}")
        
        # Buttons at top for easy access
        yield Horizontal(
            Button("← Back", id="back", variant="default"),
            Button("🌐 Open in Browser", id="open_browser", variant="primary"),
            classes="detail-buttons"
        )
        # Scrollable content area
        yield ScrollableContainer(
            Static(Panel(content, title="[bold]📰 Full Article[/]", border_style=ORANGE)),
            id="article-content"
        )


class NewsTerminalApp(App):
    """Main News Terminal Application."""
    
    CSS = """
    Screen {
        background: #0d0d0d;
    }
    
    #header-bar {
        dock: top;
        height: 3;
        background: #1a1a1a;
        border-bottom: solid #FF9500;
        padding: 0 1;
    }
    
    #header-title {
        color: #FF9500;
        text-style: bold;
        width: 1fr;
    }
    
    #header-bar Button {
        min-width: 8;
        margin-left: 1;
    }
    
    #quit-btn {
        background: #cc0000;
    }
    
    #categories {
        dock: top;
        height: 3;
        background: #1a1a1a;
        padding: 0 1;
    }
    
    #categories Button {
        margin: 0 1;
        min-width: 12;
    }
    
    #categories Button.active {
        background: #FF9500;
        color: #000;
    }
    
    #news-list {
        background: #0d0d0d;
        border: round #FF9500;
        margin: 1;
        padding: 1;
    }
    
    #news-list ListItem {
        padding: 1;
        background: #1a1a1a;
        margin: 0 0 1 0;
    }
    
    #news-list ListItem:hover {
        background: #2a2a2a;
    }
    
    #news-list ListItem.-selected {
        background: #FF9500 20%;
        border-left: thick #FF9500;
    }
    
    #article-detail {
        margin: 1;
        padding: 0;
    }
    
    #article-content {
        height: 100%;
        padding: 1;
    }
    
    .detail-buttons {
        dock: top;
        height: 3;
        padding: 0 1;
    }
    
    .detail-buttons Button {
        margin-right: 2;
    }
    
    #status-bar {
        dock: bottom;
        height: 1;
        background: #1a1a1a;
        color: #888;
        padding: 0 2;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("1", "category_1", "Headlines", show=False),
        Binding("2", "category_2", "Business", show=False),
        Binding("3", "category_3", "Technology", show=False),
        Binding("4", "category_4", "Sports", show=False),
        Binding("5", "category_5", "Health", show=False),
        Binding("escape", "back", "Back", show=False),
    ]
    
    def __init__(self):
        super().__init__()
        self.api_key = None
        self.client = None
        self.articles = []
        self.current_category = "1"
        self.current_article = None
        self.showing_detail = False
        self.scraper = ArticleScraper()
        self.auto_refresh_seconds = 300  # 5 minutes (adjustable)
        
        self.categories = {
            "1": ("general", "Headlines"),
            "2": ("business", "Business"),
            "3": ("technology", "Tech"),
            "4": ("sports", "Sports"),
            "5": ("health", "Health"),
        }
    
    def compose(self) -> ComposeResult:
        yield Horizontal(
            Static(f"██ NEWS TERMINAL  │  {datetime.now().strftime('%H:%M • %d %b %Y')}", id="header-title"),
            Button("🔄", id="refresh-btn", variant="default"),
            Button("❌ Quit", id="quit-btn", variant="error"),
            id="header-bar"
        )
        yield Horizontal(
            CategoryButton("1 Headlines", "1", id="cat-1", classes="active"),
            CategoryButton("2 Business", "2", id="cat-2"),
            CategoryButton("3 Tech", "3", id="cat-3"),
            CategoryButton("4 Sports", "4", id="cat-4"),
            CategoryButton("5 Health", "5", id="cat-5"),
            id="categories"
        )
        yield ScrollableContainer(
            ListView(id="articles-list"),
            id="news-list"
        )
        yield Container(id="article-detail")
        yield Static("↑↓ Navigate • Click/Enter read • R Refresh • Auto-refresh: 5min • Q Quit", id="status-bar")
    
    def on_mount(self) -> None:
        """Initialize the app."""
        try:
            self.api_key = get_api_key()
            self.client = NewsAPIClient(self.api_key)
            self.load_news()
            # Start auto-refresh timer (efficient, doesn't use extra RAM)
            self.set_interval(self.auto_refresh_seconds, self.auto_refresh)
        except ValueError:
            self.exit(message="API key required")
    
    def auto_refresh(self) -> None:
        """Auto-refresh news if not viewing article detail."""
        if not self.showing_detail:
            self.load_news()
    
    def load_news(self) -> None:
        """Load news from API."""
        cat_code = self.categories.get(self.current_category, ("general", "Headlines"))[0]
        result = self.client.get_top_headlines(category=cat_code)
        
        self.articles = [self.client.format_article(a) for a in result.get("articles", [])]
        
        # Update list
        list_view = self.query_one("#articles-list", ListView)
        list_view.clear()
        
        for i, article in enumerate(self.articles[:15]):
            list_view.append(NewsItem(article, i))
        
        # Hide detail view
        self.query_one("#article-detail").display = False
        self.query_one("#news-list").display = True
        self.showing_detail = False
    
    def show_article(self, article: dict) -> None:
        """Show article detail view with scraped content."""
        self.current_article = article
        
        # Fetch full article content (with fallback search if needed)
        full_content = None
        source_info = "failed"
        url = article.get("url")
        title = article.get("title")
        
        if url:
            full_content, source_info = self.scraper.fetch_article(url, title)
        
        detail_container = self.query_one("#article-detail")
        detail_container.remove_children()
        detail_container.mount(ArticleDetail(article, full_content, source_info))
        
        self.query_one("#news-list").display = False
        detail_container.display = True
        self.showing_detail = True
    
    @on(ListView.Selected, "#articles-list")
    def on_article_selected(self, event: ListView.Selected) -> None:
        """Handle article selection."""
        if isinstance(event.item, NewsItem):
            self.show_article(event.item.article)
    
    @on(Button.Pressed, "#back")
    def on_back_pressed(self) -> None:
        """Go back to list view."""
        self.action_back()
    
    @on(Button.Pressed, "#open_browser")
    def on_open_browser(self) -> None:
        """Open article in browser."""
        if self.current_article and self.current_article.get("url"):
            webbrowser.open(self.current_article["url"])
    
    @on(Button.Pressed, "#quit-btn")
    def on_quit_pressed(self) -> None:
        """Quit the app."""
        self.exit()
    
    @on(Button.Pressed, "#refresh-btn")
    def on_refresh_pressed(self) -> None:
        """Manual refresh."""
        self.action_refresh()
    
    @on(Button.Pressed, "#categories Button")
    def on_category_pressed(self, event: Button.Pressed) -> None:
        """Handle category button press."""
        if isinstance(event.button, CategoryButton):
            self.switch_category(event.button.category_id)
    
    def switch_category(self, cat_id: str) -> None:
        """Switch to a different category."""
        if cat_id == self.current_category:
            return
        
        # Update button styles
        for btn in self.query(CategoryButton):
            btn.remove_class("active")
            if btn.category_id == cat_id:
                btn.add_class("active")
        
        self.current_category = cat_id
        self.load_news()
    
    def action_back(self) -> None:
        """Return to list view."""
        if self.showing_detail:
            self.query_one("#article-detail").display = False
            self.query_one("#news-list").display = True
            self.showing_detail = False
    
    def action_refresh(self) -> None:
        """Refresh news."""
        self.load_news()
    
    def action_category_1(self) -> None:
        self.switch_category("1")
    
    def action_category_2(self) -> None:
        self.switch_category("2")
    
    def action_category_3(self) -> None:
        self.switch_category("3")
    
    def action_category_4(self) -> None:
        self.switch_category("4")
    
    def action_category_5(self) -> None:
        self.switch_category("5")


def main():
    """Main entry point."""
    app = NewsTerminalApp()
    app.run()


if __name__ == "__main__":
    main()
