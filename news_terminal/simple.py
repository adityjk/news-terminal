#!/usr/bin/env python3
"""
News Terminal - Simple version for Termux/mobile compatibility.
Uses Rich instead of Textual for wider terminal support.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from datetime import datetime
import time

from news_terminal.config import get_api_key
from news_terminal.api import NewsAPIClient
from news_terminal.scraper import ArticleScraper

# Colors
ORANGE = "#FF9500"
SOFT_ORANGE = "#FFB347"

console = Console()


def clear_screen():
    """Clear terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def show_header():
    """Display header."""
    now = datetime.now().strftime("%H:%M • %d %b %Y")
    header = Text()
    header.append("██ ", style=f"bold {ORANGE}")
    header.append("NEWS TERMINAL", style=f"bold {ORANGE}")
    header.append(f"  │  {now}", style=SOFT_ORANGE)
    console.print(Panel(header, box=box.HEAVY, border_style=ORANGE))


def show_menu():
    """Display category menu."""
    menu = Text()
    menu.append("[H] Headlines  ", style=f"bold {ORANGE}")
    menu.append("[B] Business  ", style=SOFT_ORANGE)
    menu.append("[T] Tech  ", style=SOFT_ORANGE)
    menu.append("[S] Sports  ", style=SOFT_ORANGE)
    menu.append("[E] Health  ", style=SOFT_ORANGE)
    menu.append("  │  ", style="dim")
    menu.append("[R] Refresh  ", style="dim")
    menu.append("[Q] Quit", style="dim")
    console.print(menu)
    console.print()


def show_articles(articles: list, selected: int = 0):
    """Display article list."""
    table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    table.add_column("num", width=3)
    table.add_column("title", ratio=3)
    table.add_column("source", ratio=1, justify="right")
    
    for i, article in enumerate(articles[:10]):
        num_style = f"bold {ORANGE}" if i == selected else "dim"
        title_style = f"bold white" if i == selected else "white"
        
        title = article.get("title", "No title")[:60]
        if len(article.get("title", "")) > 60:
            title += "..."
        
        table.add_row(
            f"[{num_style}]{i+1}.[/]",
            f"[{title_style}]{title}[/]",
            f"[dim italic]{article.get('source', '')}[/]"
        )
    
    console.print(Panel(table, title=f"[bold {ORANGE}]TOP HEADLINES[/]", 
                       border_style=ORANGE, box=box.ROUNDED))


def show_article_detail(article: dict, content: str, source_info: str):
    """Display article detail."""
    clear_screen()
    show_header()
    
    text = Text()
    text.append(article.get("title", "No title"), style=f"bold {ORANGE}")
    text.append("\n\n")
    text.append("Source: ", style="bold dim")
    text.append(article.get("source", "Unknown"), style=SOFT_ORANGE)
    text.append("  •  ", style="dim")
    text.append(article.get("published", ""), style="dim")
    
    if source_info.startswith("alternative"):
        text.append("\n")
        text.append("🔄 Content from: ", style="bold dim")
        text.append(source_info.replace("alternative: ", ""), style="cyan")
    
    text.append("\n")
    text.append("─" * 50, style="dim")
    text.append("\n\n")
    
    if content:
        # Truncate very long content for display
        if len(content) > 2000:
            content = content[:2000] + "\n\n[...truncated, open in browser for full article]"
        text.append(content)
    else:
        text.append(article.get("description", "No description."))
        text.append("\n\n[Could not fetch full article]", style="dim italic")
    
    text.append("\n\n")
    text.append("─" * 50, style="dim")
    text.append("\n🔗 ", style="dim")
    text.append(article.get("url", ""), style=f"underline {SOFT_ORANGE}")
    
    console.print(Panel(text, title=f"[bold {ORANGE}]📰 ARTICLE[/]", 
                       border_style=ORANGE, box=box.ROUNDED))
    
    console.print("\n[dim]Press Enter to go back...[/]")
    input()


def main():
    """Main entry point."""
    console.print("\n[bold]Loading News Terminal...[/]\n")
    
    try:
        api_key = get_api_key()
    except (ValueError, KeyboardInterrupt):
        console.print("[red]API key required. Exiting.[/]")
        sys.exit(1)
    
    client = NewsAPIClient(api_key)
    scraper = ArticleScraper()
    
    categories = {
        "h": "general",
        "b": "business",
        "t": "technology",
        "s": "sports",
        "e": "health",
    }
    
    category_names = {
        "h": "Headlines",
        "b": "Business",
        "t": "Technology",
        "s": "Sports",
        "e": "Health",
    }
    
    current_category = "h"
    articles = []
    
    # Load initial news
    console.print("[dim]Fetching news...[/]")
    result = client.get_top_headlines(category=categories[current_category])
    articles = [client.format_article(a) for a in result.get("articles", [])]
    
    while True:
        clear_screen()
        show_header()
        show_menu()
        show_articles(articles)
        
        console.print("\n[dim]Enter 1-10 to read article, or H/B/T/S/E/R/Q:[/] ", end="")
        
        try:
            choice = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            break
        
        if choice == 'q':
            clear_screen()
            console.print(f"\n[bold {ORANGE}]Thanks for using News Terminal![/]\n")
            break
        
        elif choice == 'r':
            console.print("[dim]Refreshing...[/]")
            result = client.get_top_headlines(category=categories[current_category])
            articles = [client.format_article(a) for a in result.get("articles", [])]
        
        elif choice in categories:
            current_category = choice
            console.print(f"[dim]Loading {category_names[choice]}...[/]")
            result = client.get_top_headlines(category=categories[current_category])
            articles = [client.format_article(a) for a in result.get("articles", [])]
        
        elif choice.isdigit() and 1 <= int(choice) <= min(10, len(articles)):
            idx = int(choice) - 1
            article = articles[idx]
            
            console.print("[dim]Fetching full article...[/]")
            content, source_info = scraper.fetch_article(
                article.get("url"), 
                article.get("title")
            )
            show_article_detail(article, content, source_info)


if __name__ == "__main__":
    main()
