# Web Scraper - Dual Mode Edition 

**Version: V0.0.1**

A sophisticated Web Scraper designed to download chapters from web platforms and save them as beautifully formatted Markdown files. It features two scraping engines, a REST API for remote control, and built-in CAPTCHA handling.

## 🚀 Features

- **Dual Scraping Engines:**
  - **Playwright Mode:** Uses a local Chromium browser with stealth mode to bypass bot detection. Supports manual CAPTCHA solving.
  - **WebScrapingAPI Mode:** Uses a cloud-based service for high-speed, concurrent scraping (requires API key).
- **REST API (FastAPI):** Control your scraper remotely with endpoints for starting, pausing, resuming, and monitoring progress.
- **Robust Extraction:** Uses XPath and `lxml` to target chapter content while automatically cleaning advertisements and redundant text.
- **Smart Management:**
  - **Session Persistence:** Saves browser cookies to avoid repeated CAPTCHAs.
  - **Rate Limiting:** Tracks and enforces API usage limits for WebScrapingAPI.
  - **Auto-Formatting:** Generates Markdown files with YAML front-matter and a central `chapters_index.md`.

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Ahnaf181419/knowledge-agent.git
   cd knowledge-agent
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers:**
   ```bash
   playwright install chromium
   ```

4. **Configuration:**
   Copy the example config and edit it with your settings:
   ```bash
   cp config.py.example config.py
   ```

## 📖 Usage

### Interactive CLI Mode
Simply run the script to start the interactive prompt:
```bash
python scraper.py
```

### Command Line Arguments
You can also run the scraper with specific arguments:
```bash
# Scrape range using Playwright
python scraper.py --start 1 --end 50 --mode playwright

# Scrape specific chapters using WebScrapingAPI
python scraper.py --selection-mode specific --chapters "24,58,304" --mode webscrapingapi --api-key YOUR_API_KEY
```

### REST API Mode
Start the API server to control the scraper via HTTP:
```bash
python scraper.py --api --port 8000
```
Visit `http://localhost:8000/docs` to see the interactive API documentation.

## ⚙️ Configuration

Edit `config.py` to customize:
- `NAME` / `SLUG`: Metadata for the files.
- `BASE_URL`: The URL template (e.g., `https://example.com/chapter-{n}`).
- `DELAY_MIN` / `DELAY_MAX`: Human-like delays between chapters.
- `WEBSCRAPINGAPI_KEY`: Your cloud API credentials.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---
*Disclaimer: This tool is for educational purposes only. Please respect the Terms of Service of the websites you scrape.*
