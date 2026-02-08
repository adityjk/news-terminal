"""
Configuration handler for News Terminal.
Manages API key storage and retrieval.
"""

import json
import os
from pathlib import Path

CONFIG_FILE = Path(__file__).parent.parent / "config.json"


def get_api_key() -> str:
    """Get API key from config file or prompt user to enter one."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                if config.get("api_key"):
                    return config["api_key"]
        except (json.JSONDecodeError, IOError):
            pass
    
    # Prompt user for API key
    print("\n" + "=" * 60)
    print("  WELCOME TO NEWS TERMINAL")
    print("=" * 60)
    print("\nTo use this application, you need a NewsAPI key.")
    print("Get your FREE API key at: https://newsapi.org/register")
    print()
    
    api_key = input("Enter your NewsAPI key: ").strip()
    
    if api_key:
        save_api_key(api_key)
        print("\n✓ API key saved successfully!\n")
        return api_key
    else:
        raise ValueError("API key is required to use News Terminal")


def save_api_key(api_key: str) -> None:
    """Save API key to config file."""
    config = {"api_key": api_key}
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def clear_api_key() -> None:
    """Remove stored API key."""
    if CONFIG_FILE.exists():
        os.remove(CONFIG_FILE)
