"""
Terminal UI for News Terminal - Simple Bloomberg-inspired design.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich.align import Align
from rich import box
from datetime import datetime
import sys
import os

# Colors - Orange accent with dark theme, easy on eyes
ORANGE = "#FF9500"
SOFT_ORANGE = "#FFB347"
YELLOW = "#FFD700"
DARK_BG = "#1a1a1a"
GRAY = "#888888"
WHITE = "#FFFFFF"


class NewsTerminalUI:
    """Simple terminal UI for displaying news."""
    
    def __init__(self, console: Console = None):
        self.console = console or Console()
        self.current_category = "1"
        self.selected_index = 0
        self.articles = []
        self.category_names = {
            "1": "TOP HEADLINES",
            "2": "BUSINESS",
            "3": "TECHNOLOGY",
            "4": "SPORTS",
            "5": "HEALTH"
        }
    
    def clear(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def render_header(self) -> Panel:
        """Render the header with logo and time."""
        now = datetime.now().strftime("%H:%M:%S • %d %b %Y")
        
        header_text = Text()
        header_text.append("██ ", style=f"bold {ORANGE}")
        header_text.append("NEWS TERMINAL", style=f"bold {ORANGE}")
        header_text.append("  │  ", style=GRAY)
        header_text.append(now, style=f"{SOFT_ORANGE}")
        
        return Panel(
            Align.center(header_text),
            style=f"on #0d0d0d",
            box=box.HEAVY,
            border_style=ORANGE
        )
    
    def render_menu(self) -> Text:
        """Render category menu bar."""
        menu = Text()
        
        categories = [
            ("1", "Headlines"),
            ("2", "Business"),
            ("3", "Tech"),
            ("4", "Sports"),
            ("5", "Health"),
        ]
        
        for key, name in categories:
            if key == self.current_category:
                menu.append(f" [{key}] {name} ", style=f"bold {ORANGE} on #333333")
            else:
                menu.append(f" [{key}] {name} ", style=f"{GRAY}")
            menu.append(" ")
        
        menu.append("  │  ", style=GRAY)
        menu.append("[R] ", style=f"bold {SOFT_ORANGE}")
        menu.append("Refresh  ", style=GRAY)
        menu.append("[Q] ", style=f"bold {SOFT_ORANGE}")
        menu.append("Quit", style=GRAY)
        
        return menu
    
    def render_articles(self, articles: list) -> Panel:
        """Render the news articles list."""
        self.articles = articles
        
        table = Table(
            show_header=False,
            box=None,
            padding=(0, 1),
            expand=True
        )
        table.add_column("indicator", width=2)
        table.add_column("title", ratio=4)
        table.add_column("source", ratio=1, justify="right")
        table.add_column("time", width=18, justify="right")
        
        if not articles:
            return Panel(
                Align.center(Text("No articles available. Press [R] to refresh.", style=GRAY)),
                title=f"[bold {ORANGE}]{self.category_names.get(self.current_category, 'NEWS')}[/]",
                border_style=ORANGE,
                box=box.ROUNDED
            )
        
        for i, article in enumerate(articles[:15]):  # Show max 15 articles
            # Indicator
            if i == self.selected_index:
                indicator = Text("►", style=f"bold {ORANGE}")
            else:
                indicator = Text(" ")
            
            # Title - truncate if too long
            title_text = article.get("title", "No title")[:80]
            if len(article.get("title", "")) > 80:
                title_text += "..."
            
            if i == self.selected_index:
                title = Text(title_text, style=f"bold {WHITE}")
            else:
                title = Text(title_text, style=f"{GRAY}")
            
            # Source
            source = Text(article.get("source", ""), style=f"italic {SOFT_ORANGE}")
            
            # Time
            time_text = Text(article.get("published", ""), style=f"dim {GRAY}")
            
            table.add_row(indicator, title, source, time_text)
        
        return Panel(
            table,
            title=f"[bold {ORANGE}]{self.category_names.get(self.current_category, 'NEWS')}[/]",
            subtitle=f"[{GRAY}]↑↓ Navigate • Enter to read • {len(articles)} articles[/]",
            border_style=ORANGE,
            box=box.ROUNDED,
            padding=(1, 2)
        )
    
    def render_detail(self, article: dict) -> Panel:
        """Render article detail view."""
        content = Text()
        
        # Title
        content.append(article.get("title", "No title"), style=f"bold {ORANGE}")
        content.append("\n\n")
        
        # Source and time
        content.append("Source: ", style=f"bold {GRAY}")
        content.append(article.get("source", "Unknown"), style=SOFT_ORANGE)
        content.append("  •  ", style=GRAY)
        content.append(article.get("published", ""), style=GRAY)
        content.append("\n")
        
        if article.get("author") and article["author"] != "Unknown":
            content.append("Author: ", style=f"bold {GRAY}")
            content.append(article["author"], style=WHITE)
            content.append("\n")
        
        content.append("\n")
        
        # Description
        description = article.get("description", "No description available.")
        if description:
            content.append(description, style=WHITE)
            content.append("\n\n")
        
        # URL
        content.append("Read more: ", style=f"bold {GRAY}")
        content.append(article.get("url", ""), style=f"underline {SOFT_ORANGE}")
        
        return Panel(
            content,
            title=f"[bold {ORANGE}]ARTICLE DETAIL[/]",
            subtitle=f"[{GRAY}]Press any key to go back[/]",
            border_style=ORANGE,
            box=box.ROUNDED,
            padding=(1, 2)
        )
    
    def render_loading(self) -> Panel:
        """Render loading indicator."""
        return Panel(
            Align.center(Text("Loading news...", style=f"bold {ORANGE}")),
            border_style=GRAY,
            box=box.ROUNDED
        )
    
    def render_error(self, message: str) -> Panel:
        """Render error message."""
        return Panel(
            Align.center(Text(f"Error: {message}", style="bold red")),
            border_style="red",
            box=box.ROUNDED
        )
    
    def display(self, articles: list):
        """Display the main news view."""
        self.clear()
        self.console.print(self.render_header())
        self.console.print(Align.center(self.render_menu()))
        self.console.print()
        self.console.print(self.render_articles(articles))
    
    def display_detail(self, article: dict):
        """Display article detail view."""
        self.clear()
        self.console.print(self.render_header())
        self.console.print()
        self.console.print(self.render_detail(article))
    
    def display_loading(self):
        """Display loading screen."""
        self.clear()
        self.console.print(self.render_header())
        self.console.print()
        self.console.print(self.render_loading())
    
    def display_error(self, message: str):
        """Display error screen."""
        self.clear()
        self.console.print(self.render_header())
        self.console.print()
        self.console.print(self.render_error(message))
    
    def navigate_up(self):
        """Move selection up."""
        if self.selected_index > 0:
            self.selected_index -= 1
    
    def navigate_down(self):
        """Move selection down."""
        if self.selected_index < len(self.articles) - 1:
            self.selected_index += 1
    
    def get_selected_article(self) -> dict:
        """Get currently selected article."""
        if 0 <= self.selected_index < len(self.articles):
            return self.articles[self.selected_index]
        return None
    
    def set_category(self, category: str):
        """Set current category and reset selection."""
        if category in self.category_names:
            self.current_category = category
            self.selected_index = 0
