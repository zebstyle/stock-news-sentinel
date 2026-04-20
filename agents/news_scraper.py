"""
News Scraper Agent
Autonomous agent for collecting news articles about stocks
"""

from typing import List, Dict, Any
from datetime import datetime

from services.scraper import NewsScraper
from utils.config import Config
from utils.state_manager import StateManager
from utils.logger import LoggerMixin


class NewsScraperAgent(LoggerMixin):
    """Agent that autonomously scrapes news for stocks"""
    
    def __init__(self, config: Config, state_manager: StateManager):
        """
        Initialize news scraper agent
        
        Args:
            config: Configuration instance
            state_manager: State manager instance
        """
        self.config = config
        self.state_manager = state_manager
        self.scraper = NewsScraper(config)
        self.agent = None
    
    def scrape_news(self, stocks: List[str]) -> List[Dict[str, Any]]:
        """
        Scrape news for given stocks
        
        Args:
            stocks: List of stock symbols
            
        Returns:
            List of new articles
        """
        self.logger.info(f"Starting news scraping for stocks: {', '.join(stocks)}")
        
        # Scrape all sources
        all_articles = self.scraper.scrape_all_sources(
            stocks, 
            self.config.max_articles_per_scan
        )
        
        # Filter out articles we've already seen
        new_articles = []
        for article in all_articles:
            article_id = article.get('id')
            if article_id and not self.state_manager.article_exists(article_id):
                new_articles.append(article)
                self.logger.debug(f"New article found: {article.get('title', '')[:50]}")
            else:
                self.logger.debug(f"Skipping duplicate article: {article_id}")
        
        self.logger.info(f"Found {len(new_articles)} new articles out of {len(all_articles)} total")
        
        return new_articles
    
    def run(self) -> Dict[str, Any]:
        """
        Run the news scraper agent
        
        Returns:
            Results dictionary with scraped articles
        """
        self.logger.info("News Scraper Agent starting...")
        
        start_time = datetime.now()
        
        try:
            # Get stocks from config
            stocks = self.config.stocks
            
            if not stocks:
                self.logger.warning("No stocks configured for monitoring")
                return {
                    'success': False,
                    'error': 'No stocks configured',
                    'articles': []
                }
            
            # Scrape news
            articles = self.scrape_news(stocks)
            
            # Update scan info
            self.state_manager.update_scan_info()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.logger.info(f"News Scraper Agent completed in {duration:.2f}s")
            
            return {
                'success': True,
                'articles': articles,
                'count': len(articles),
                'duration': duration,
                'timestamp': end_time.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in News Scraper Agent: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'articles': []
            }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get agent status
        
        Returns:
            Status dictionary
        """
        stats = self.state_manager.get_stats()
        
        return {
            'agent': 'NewsScraperAgent',
            'status': 'active',
            'last_scan': stats.get('last_scan'),
            'scan_count': stats.get('scan_count', 0),
            'total_articles': stats.get('total_articles', 0)
        }


# Made with Bob