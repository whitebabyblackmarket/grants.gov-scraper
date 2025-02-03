# Grants.gov Scraper

A robust web scraping solution for extracting and analyzing grant opportunities from grants.gov. This project automates the collection of both grant listings and detailed grant information using a two-phase approach.

## 📁 Project Structure 

grants-scraper/
├── scrape_links.py # Phase 1: Scrapes grant listings and URLs
├── scrape_details.py # Phase 2: Scrapes detailed grant information
├── parser.py # HTML parsing utilities and data extraction
├── utilities.py # Shared utility functions (logging, retry logic)
├── grant_ids.csv # Output from Phase 1
└── grant_details.csv # Output from Phase 2



## ✨ Features

- **Two-Phase Scraping**
  - Phase 1: Collects grant opportunity listings and URLs
  - Phase 2: Extracts detailed information from each grant page
- **Smart Pagination**
  - Handles dynamic page loading
  - Maintains state between pages
- **Anti-Bot Protection**
  - Simulates human-like behavior
  - Configurable delays and retries
- **Robust Error Handling**
  - Comprehensive logging system
  - Automatic retries with backoff
  - Data validation
- **Clean Data Export**
  - Structured CSV output
  - UTF-8 encoding support

## 🔧 Requirements

- Python 3.7+
- Firefox Browser
- Dependencies:
  ```
  selenium>=4.0.0
  beautifulsoup4>=4.9.0
  ```

## 🚀 Installation

1. **Clone the Repository**
   ```bash
   git clone [repository-url]
   cd grants-scraper
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup WebDriver**
   - Download [GeckoDriver](https://github.com/mozilla/geckodriver/releases)
   - Add to system PATH or place in project directory

## 📋 Usage

### Phase 1: Collect Grant Listings

```bash
python scrape_links.py
```

This script will:
- Navigate to grants.gov search page
- Extract grant opportunities
- Handle pagination automatically
- Save results to `grant_ids.csv`

### Phase 2: Extract Detailed Information

```bash
python scrape_details.py
```

This script will:
- Read URLs from `grant_ids.csv`
- Visit each grant's detail page
- Extract comprehensive information
- Export to `grant_details.csv`

## 📄 Output Format

### grant_ids.csv
```csv
Opportunity Number,Detail Page URL
GRANT12345,https://grants.gov/...
```

Fields:
- Opportunity Number: Unique identifier for the grant
- Detail Page URL: Full URL to the grant's detail page

### grant_details.csv
```csv
Opportunity Number,Title,Agency,Amount,Due Date,...
GRANT12345,Research Grant,NSF,$500000,2024-03-01,...
```

Fields:
- Opportunity Number: Matches the ID from grant_ids.csv
- Title: Full grant title
- Agency: Issuing agency name
- Amount: Grant funding amount
- Due Date: Application deadline
- Additional Fields: Various grant-specific details

## 🛠️ Error Handling

The system includes:
- Comprehensive logging
- Anti-bot detection avoidance
- Automatic retries
- Data validation
- Safe file handling

## ⚠️ Known Issues

1. Pagination handling may require adjustments due to dynamic page loading
2. Anti-bot measures might occasionally trigger
3. Site structure changes may require parser updates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to the branch
5. Create a Pull Request

## 📝 License

[Your chosen license]

## 👏 Acknowledgments

- Selenium WebDriver team
- BeautifulSoup4 developers
- Grants.gov for providing public access to grant information

## 💬 Support

For issues and feature requests, please use the GitHub issue tracker.

