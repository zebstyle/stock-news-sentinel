# Stock News Sentinel - AI-Powered Stock News Monitoring & Sentiment Analysis

An autonomous agent-based application that monitors news for specific stocks, performs sentiment analysis, and sends automated email alerts about significant market-moving news.

## Features

- Autonomous agent-based architecture using LangChain
- Real-time news scraping from multiple sources
- Advanced sentiment analysis using FinBERT (financial domain-specific)
- Automated email alerts for significant news
- In-memory state management (no database required)
- JSON-based persistence to avoid duplicate analysis
- Scheduled automated monitoring
- Interactive Streamlit dashboard

## Architecture

```
Stock News Sentinel
├── agents/                 # Autonomous agents
│   ├── news_scraper.py    # News collection agent
│   ├── sentiment_analyzer.py  # Sentiment analysis agent
│   └── alert_manager.py   # Email alert agent
├── services/              # Core services
│   ├── scraper.py        # Web scraping logic
│   ├── sentiment.py      # Sentiment analysis
│   └── email_service.py  # Email notifications
├── utils/                # Utilities
│   ├── config.py         # Configuration management
│   ├── logger.py         # Logging setup
│   └── state_manager.py  # Session state management
├── data/                 # Data storage
│   └── analyzed_articles.json  # Persistence
├── config.properties     # Configuration file
├── app.py               # Main Streamlit application
└── requirements.txt     # Dependencies
```

## Technology Stack

- **Python 3.10+**
- **Streamlit** - Web interface
- **LangChain** - Agent framework
- **BeautifulSoup4** - Web scraping
- **Selenium** - Dynamic content scraping
- **FinBERT** - Financial sentiment analysis
- **VADER** - Fallback sentiment analysis
- **APScheduler** - Task scheduling
- **smtplib** - Email notifications

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure `config.properties`:
```properties
# Stocks to monitor (comma-separated)
stocks=AAPL,GOOGL,MSFT,TSLA,AMZN

# News sources (comma-separated URLs)
news_sources=https://finance.yahoo.com,https://www.cnbc.com,https://www.bloomberg.com

# Email configuration
email_from=your-email@gmail.com
email_to=recipient@example.com
email_password=your-app-password
smtp_server=smtp.gmail.com
smtp_port=587

# Monitoring settings
check_interval_minutes=30
sentiment_threshold=0.7
```

4. Run the application:
```bash
streamlit run app.py
```

## Usage

1. **Dashboard**: View monitored stocks and recent news
2. **Manual Scan**: Trigger immediate news scan
3. **Configure**: Update stocks and settings
4. **History**: View analyzed articles and sentiment scores
5. **Alerts**: Configure email alert preferences

## Configuration

### config.properties

- `stocks`: Comma-separated list of stock symbols
- `news_sources`: URLs to scrape for news
- `email_from`: Sender email address
- `email_to`: Recipient email address
- `email_password`: Email app password (not regular password)
- `smtp_server`: SMTP server address
- `smtp_port`: SMTP port (usually 587 for TLS)
- `check_interval_minutes`: How often to check for news
- `sentiment_threshold`: Minimum sentiment score to trigger alert (0-1)

## Email Setup (Gmail)

1. Enable 2-factor authentication
2. Generate an app password: https://myaccount.google.com/apppasswords
3. Use the app password in `config.properties`

## Agent Architecture

### News Scraper Agent
- Monitors configured news sources
- Extracts articles related to tracked stocks
- Filters duplicate articles
- Passes articles to sentiment analyzer

### Sentiment Analyzer Agent
- Analyzes article sentiment using FinBERT
- Determines potential stock price impact
- Calculates confidence scores
- Triggers alerts for significant news

### Alert Manager Agent
- Evaluates sentiment scores against thresholds
- Composes email alerts with article details
- Sends notifications to configured recipients
- Logs all alert activities

## Data Persistence

Articles are stored in `data/analyzed_articles.json`:
```json
{
  "article_id": {
    "title": "Article Title",
    "url": "https://...",
    "stock": "AAPL",
    "sentiment": 0.85,
    "impact": "positive",
    "analyzed_at": "2026-04-02T10:00:00",
    "alerted": true
  }
}
```

## Sentiment Scores

- **Positive**: 0.6 to 1.0 (Bullish news)
- **Neutral**: -0.6 to 0.6 (No significant impact)
- **Negative**: -1.0 to -0.6 (Bearish news)

## Security Notes

- Never commit `config.properties` with real credentials
- Use environment variables for production
- Use app-specific passwords, not account passwords
- Regularly rotate credentials

## Troubleshooting

### News not being scraped
- Check internet connection
- Verify news source URLs are accessible
- Some sites may require Selenium for dynamic content

### Email alerts not working
- Verify SMTP settings
- Check email credentials
- Ensure app password is used (not regular password)
- Check spam folder

### Sentiment analysis errors
- Ensure transformers library is installed
- FinBERT model will download on first run (may take time)
- Check available disk space for model storage

## Future Enhancements

- Support for more news sources
- Advanced filtering (by date, relevance)
- Historical sentiment trends
- Multi-language support
- Telegram/Slack notifications
- Custom sentiment models
- Portfolio tracking integration

## License

MIT License

## Contributing

Contributions welcome! Please open an issue or submit a pull request.