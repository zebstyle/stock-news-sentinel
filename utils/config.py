"""
Configuration Management Module
Handles loading and accessing configuration from config.properties
"""

import os
import configparser
from typing import List, Optional
from pathlib import Path


class Config:
    """Configuration manager for Stock News Sentinel"""
    
    def __init__(self, config_file: str = "config.properties"):
        """
        Initialize configuration manager
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file"""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")
        
        # Read the config file
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config_string = '[DEFAULT]\n' + f.read()
        
        self.config.read_string(config_string)
    
    def get(self, key: str, default: Optional[str] = None) -> str:
        """
        Get configuration value
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.config.get('DEFAULT', key, fallback=default)
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer configuration value"""
        try:
            return int(self.get(key, str(default)))
        except (ValueError, TypeError):
            return default
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get float configuration value"""
        try:
            return float(self.get(key, str(default)))
        except (ValueError, TypeError):
            return default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean configuration value"""
        value = self.get(key, str(default)).lower()
        return value in ('true', 'yes', '1', 'on')
    
    def get_list(self, key: str, default: Optional[List[str]] = None) -> List[str]:
        """
        Get list configuration value (comma-separated)
        
        Args:
            key: Configuration key
            default: Default list if key not found
            
        Returns:
            List of values
        """
        if default is None:
            default = []
        
        value = self.get(key)
        if not value:
            return default
        
        return [item.strip() for item in value.split(',') if item.strip()]
    
    # Stock Configuration
    @property
    def stocks(self) -> List[str]:
        """Get list of stocks to monitor"""
        return self.get_list('stocks', ['AAPL', 'GOOGL', 'MSFT'])
    
    # News Sources
    @property
    def news_sources(self) -> List[str]:
        """Get list of news source URLs"""
        return self.get_list('news_sources', [])
    
    @property
    def news_api_key(self) -> Optional[str]:
        """Get News API key"""
        return self.get('news_api_key')
    
    @property
    def alpha_vantage_key(self) -> Optional[str]:
        """Get Alpha Vantage API key"""
        return self.get('alpha_vantage_key')
    
    # Email Configuration
    @property
    def email_from(self) -> str:
        """Get sender email address"""
        return self.get('email_from', '')
    
    @property
    def email_to(self) -> str:
        """Get recipient email address"""
        return self.get('email_to', '')
    
    @property
    def email_password(self) -> str:
        """Get email password"""
        return self.get('email_password', '')
    
    @property
    def smtp_server(self) -> str:
        """Get SMTP server"""
        return self.get('smtp_server', 'smtp.gmail.com')
    
    @property
    def smtp_port(self) -> int:
        """Get SMTP port"""
        return self.get_int('smtp_port', 587)
    
    @property
    def email_subject_prefix(self) -> str:
        """Get email subject prefix"""
        return self.get('email_subject_prefix', '[Stock Alert]')
    
    # Monitoring Settings
    @property
    def check_interval_minutes(self) -> int:
        """Get check interval in minutes"""
        return self.get_int('check_interval_minutes', 30)
    
    @property
    def sentiment_threshold(self) -> float:
        """Get sentiment threshold for alerts"""
        return self.get_float('sentiment_threshold', 0.65)
    
    @property
    def confidence_threshold(self) -> float:
        """Get confidence threshold"""
        return self.get_float('confidence_threshold', 0.7)
    
    @property
    def max_articles_per_scan(self) -> int:
        """Get maximum articles per scan"""
        return self.get_int('max_articles_per_scan', 50)
    
    # Sentiment Analysis Settings
    @property
    def primary_sentiment_model(self) -> str:
        """Get primary sentiment model"""
        return self.get('primary_sentiment_model', 'finbert')
    
    @property
    def fallback_sentiment_model(self) -> str:
        """Get fallback sentiment model"""
        return self.get('fallback_sentiment_model', 'vader')
    
    @property
    def enable_ensemble(self) -> bool:
        """Check if ensemble sentiment is enabled"""
        return self.get_bool('enable_ensemble', True)
    
    # Scraping Settings
    @property
    def use_selenium(self) -> bool:
        """Check if Selenium should be used"""
        return self.get_bool('use_selenium', False)
    
    @property
    def selenium_browser(self) -> str:
        """Get Selenium browser"""
        return self.get('selenium_browser', 'chrome')
    
    @property
    def selenium_headless(self) -> bool:
        """Check if Selenium should run headless"""
        return self.get_bool('selenium_headless', True)
    
    @property
    def request_timeout(self) -> int:
        """Get request timeout in seconds"""
        return self.get_int('request_timeout', 10)
    
    @property
    def user_agent(self) -> str:
        """Get user agent string"""
        return self.get('user_agent', 
                       'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    # Persistence Settings
    @property
    def data_file(self) -> str:
        """Get data file path"""
        return self.get('data_file', 'data/analyzed_articles.json')
    
    @property
    def history_retention_days(self) -> int:
        """Get history retention days"""
        return self.get_int('history_retention_days', 30)
    
    # Logging Settings
    @property
    def log_level(self) -> str:
        """Get log level"""
        return self.get('log_level', 'INFO')
    
    @property
    def log_file(self) -> str:
        """Get log file path"""
        return self.get('log_file', 'logs/stock_news_sentinel.log')
    
    @property
    def log_to_console(self) -> bool:
        """Check if console logging is enabled"""
        return self.get_bool('log_to_console', True)
    
    # Agent Settings
    @property
    def enable_agents(self) -> bool:
        """Check if agents are enabled"""
        return self.get_bool('enable_agents', True)
    
    @property
    def agent_interval(self) -> int:
        """Get agent execution interval in seconds"""
        return self.get_int('agent_interval', 1800)
    
    @property
    def max_retries(self) -> int:
        """Get maximum retries"""
        return self.get_int('max_retries', 3)
    
    # Alert Settings
    @property
    def send_daily_summary(self) -> bool:
        """Check if daily summary should be sent"""
        return self.get_bool('send_daily_summary', True)
    
    @property
    def daily_summary_time(self) -> str:
        """Get daily summary time"""
        return self.get('daily_summary_time', '18:00')
    
    @property
    def alert_significant_only(self) -> bool:
        """Check if only significant alerts should be sent"""
        return self.get_bool('alert_significant_only', True)
    
    @property
    def include_article_snippet(self) -> bool:
        """Check if article snippet should be included"""
        return self.get_bool('include_article_snippet', True)
    
    @property
    def snippet_max_length(self) -> int:
        """Get maximum snippet length"""
        return self.get_int('snippet_max_length', 300)
    
    # Advanced Settings
    @property
    def enable_cache(self) -> bool:
        """Check if caching is enabled"""
        return self.get_bool('enable_cache', True)
    
    @property
    def cache_expiry_minutes(self) -> int:
        """Get cache expiry in minutes"""
        return self.get_int('cache_expiry_minutes', 60)
    
    @property
    def enable_parallel(self) -> bool:
        """Check if parallel processing is enabled"""
        return self.get_bool('enable_parallel', True)
    
    @property
    def worker_threads(self) -> int:
        """Get number of worker threads"""
        return self.get_int('worker_threads', 4)
    
    @property
    def rate_limit(self) -> int:
        """Get rate limit (requests per minute)"""
        return self.get_int('rate_limit', 30)
    
    def validate(self) -> List[str]:
        """
        Validate configuration
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required fields
        if not self.stocks:
            errors.append("No stocks configured")
        
        if not self.news_sources:
            errors.append("No news sources configured")
        
        if not self.email_from:
            errors.append("Sender email not configured")
        
        if not self.email_to:
            errors.append("Recipient email not configured")
        
        if not self.email_password:
            errors.append("Email password not configured")
        
        # Validate ranges
        if not 0 <= self.sentiment_threshold <= 1:
            errors.append("Sentiment threshold must be between 0 and 1")
        
        if not 0 <= self.confidence_threshold <= 1:
            errors.append("Confidence threshold must be between 0 and 1")
        
        if self.check_interval_minutes < 1:
            errors.append("Check interval must be at least 1 minute")
        
        return errors
    
    def ensure_directories(self):
        """Ensure required directories exist"""
        # Create data directory
        data_dir = Path(self.data_file).parent
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logs directory
        log_dir = Path(self.log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)


# Global config instance
_config_instance = None


def get_config(config_file: str = "config.properties") -> Config:
    """
    Get global configuration instance
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_file)
    return _config_instance

# Made with Bob
