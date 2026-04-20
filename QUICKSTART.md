# Stock News Sentinel - Quick Start Guide

Get up and running with Stock News Sentinel in 5 minutes!

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Gmail account (for email alerts)

## Installation Steps

### 1. Install Dependencies

```bash
cd stock-news-sentinel
pip install -r requirements.txt
```

**Note:** First-time installation may take 5-10 minutes as it downloads the FinBERT model (~400MB).

### 2. Configure Email (Gmail)

#### Enable 2-Factor Authentication
1. Go to your Google Account: https://myaccount.google.com
2. Navigate to Security → 2-Step Verification
3. Enable 2-Step Verification

#### Generate App Password
1. Go to: https://myaccount.google.com/apppasswords
2. Select "Mail" and "Windows Computer" (or your device)
3. Click "Generate"
4. Copy the 16-character password (remove spaces)

### 3. Edit Configuration

Open `config.properties` and update:

```properties
# Your stocks (comma-separated)
stocks=AAPL,GOOGL,MSFT,TSLA

# Email settings
email_from=your-email@gmail.com
email_to=recipient@example.com
email_password=your-16-char-app-password
```

**Important:** Use the app password, NOT your regular Gmail password!

### 4. Run the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## First Use

### Test Email Connection
1. In the sidebar, click "Test Email Connection"
2. Verify you see "✅ Email connection successful"
3. If it fails, double-check your email settings

### Run Your First Scan
1. Click "🚀 Run Scan Now" in the sidebar
2. Wait for the scan to complete (may take 1-2 minutes)
3. View results in the Dashboard tab

### Enable Auto-Scan (Optional)
1. Check "Enable Auto-Scan" in the sidebar
2. The app will automatically scan every 30 minutes (configurable)

## Understanding the Dashboard

### Tabs Overview

1. **📊 Dashboard**
   - View overall statistics
   - See articles by stock
   - Monitor scan activity

2. **📰 Recent Articles**
   - Browse analyzed articles
   - Filter by stock or sentiment
   - View detailed sentiment scores

3. **📈 Statistics**
   - Sentiment distribution charts
   - Agent status information
   - Activity summary

4. **⚙️ Settings**
   - View configuration
   - Clear data
   - Cleanup old articles

## Email Alerts

You'll receive email alerts when:
- Sentiment score ≥ 0.65 (configurable)
- Confidence ≥ 0.7 (configurable)

Alert emails include:
- Stock symbol
- Article title and link
- Sentiment analysis (positive/negative/neutral)
- Confidence score
- Article snippet

## Customization

### Change Monitored Stocks

Edit `config.properties`:
```properties
stocks=AAPL,GOOGL,MSFT,NVDA,META,AMZN
```

### Adjust Scan Frequency

```properties
check_interval_minutes=15  # Scan every 15 minutes
```

### Change Sentiment Threshold

```properties
sentiment_threshold=0.7  # Only alert on strong sentiment
```

### Add News Sources

```properties
news_sources=https://finance.yahoo.com,https://www.cnbc.com,https://www.marketwatch.com,https://www.reuters.com/business
```

## Troubleshooting

### Email Alerts Not Working

**Problem:** "Email connection failed"

**Solutions:**
1. Verify 2-factor authentication is enabled
2. Generate a new app password
3. Check for typos in email settings
4. Ensure no spaces in app password
5. Try a different email provider

### No Articles Found

**Problem:** "Found 0 new articles"

**Solutions:**
1. Check internet connection
2. Verify news source URLs are accessible
3. Try different news sources
4. Enable Selenium for dynamic content:
   ```properties
   use_selenium=true
   ```

### Slow Performance

**Problem:** Scans take too long

**Solutions:**
1. Reduce number of stocks monitored
2. Decrease `max_articles_per_scan`:
   ```properties
   max_articles_per_scan=20
   ```
3. Disable ensemble sentiment:
   ```properties
   enable_ensemble=false
   ```

### FinBERT Model Issues

**Problem:** "Error loading FinBERT"

**Solutions:**
1. Check disk space (need ~1GB free)
2. Check internet connection (first download)
3. Use VADER as primary model:
   ```properties
   primary_sentiment_model=vader
   ```

## Advanced Features

### Scheduled Daily Summary

Receive a daily email summary at 6 PM:

```properties
send_daily_summary=true
daily_summary_time=18:00
```

### Parallel Processing

Speed up analysis with parallel processing:

```properties
enable_parallel=true
worker_threads=4
```

### Custom Sentiment Models

Switch between models:

```properties
primary_sentiment_model=finbert  # or vader, textblob
fallback_sentiment_model=vader
enable_ensemble=true  # Use multiple models
```

## Data Management

### View Stored Data

Articles are stored in: `data/analyzed_articles.json`

### Clear All Data

In the Settings tab, click "Clear All Data"

### Cleanup Old Articles

Set retention period:
```properties
history_retention_days=30
```

Or manually cleanup in Settings tab.

## Best Practices

1. **Start Small:** Begin with 3-5 stocks
2. **Test First:** Always test email connection before enabling auto-scan
3. **Monitor Logs:** Check `logs/stock_news_sentinel.log` for issues
4. **Regular Cleanup:** Clean old articles monthly
5. **Backup Config:** Keep a backup of your `config.properties`

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore advanced configuration options
- Customize sentiment thresholds for your needs
- Add more news sources
- Set up daily summaries

## Support

For issues or questions:
1. Check the [README.md](README.md) troubleshooting section
2. Review logs in `logs/stock_news_sentinel.log`
3. Verify configuration in `config.properties`

## Security Reminder

⚠️ **Never commit `config.properties` with real credentials to version control!**

Use environment variables for production deployments.

---

**Made with Bob** 🤖

Happy monitoring! 📈