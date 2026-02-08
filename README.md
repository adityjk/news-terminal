# News Terminal

Terminal-based news reader inspired by Bloomberg Terminal, fetching news from NewsAPI.org.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

- 📰 **Real-time news** from NewsAPI.org
- 🖱️ **Clickable UI** - mouse support for navigation
- 📖 **Full article content** - auto-scrapes full article from source
- 🔄 **Fallback search** - finds alternative sources if original is blocked
- ⏰ **Auto-refresh** - updates every 5 minutes
- 🎨 **Bloomberg-style design** - orange theme, clean interface

## Installation

### Linux / macOS / Termux (Android)

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/news-terminal.git
cd news-terminal

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Quick Start

```bash
# Run directly
python news_terminal/main.py

# Or add alias for quick access
echo 'alias news="source /path/to/news-terminal/venv/bin/activate && python /path/to/news-terminal/news_terminal/main.py"' >> ~/.bashrc
source ~/.bashrc
news
```

### First Run
1. Get your FREE API key from [newsapi.org](https://newsapi.org/register)
2. Run `news` and enter your API key when prompted
3. API key is saved locally - only need to enter once!

## Usage

### Keyboard Controls
| Key | Action |
|-----|--------|
| ↑↓ | Navigate articles |
| 1-5 | Switch category |
| Enter | Read full article |
| R | Refresh |
| Q | Quit |

### Mouse Controls
- **Click article** - Read full content
- **Click category buttons** - Switch category
- **Scroll** - Navigate long articles

### Categories
1. **Headlines** - Top news
2. **Business** - Finance & economy
3. **Technology** - Tech news
4. **Sports** - Sports updates
5. **Health** - Health news

## Mobile Usage (Termux on Android)

```bash
# Install Termux from F-Droid
# Then run:
pkg install python git
pip install --upgrade pip

# Clone and setup (same as above)
git clone https://github.com/YOUR_USERNAME/news-terminal.git
cd news-terminal
pip install -r requirements.txt

# Run
python news_terminal/main.py
```

## Configuration

API key is stored in `config.json` (auto-created on first run).

To change auto-refresh interval, edit `main.py`:
```python
self.auto_refresh_seconds = 300  # Change to desired seconds
```

## License

MIT License - feel free to use and modify!
