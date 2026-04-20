"""
Web Scraping Service
Handles news scraping from various sources
"""

import re
import hashlib
from typing import List, Dict, Optional, Any
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time

# Optional imports
try:
    from newspaper import Article
    NEWSPAPER_AVAILABLE = True
except ImportError:
    NEWSPAPER_AVAILABLE = False

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from utils.logger import LoggerMixin
from utils.config import Config


class NewsScraper(LoggerMixin):
    """Scrapes news articles from various sources"""
    
    def __init__(self, config: Config):
        """
        Initialize news scraper
        
        Args:
            config: Configuration instance
        """
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.user_agent
        })
        self.driver = None
    
    def _init_selenium(self):
        """Initialize Selenium WebDriver"""
        if not SELENIUM_AVAILABLE:
            self.logger.warning("Selenium is not available. Install selenium and webdriver-manager to use this feature.")
            return
        
        if self.driver is None:
            try:
                chrome_options = Options()
                if self.config.selenium_headless:
                    chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument(f'user-agent={self.config.user_agent}')
                
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.logger.info("Selenium WebDriver initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Selenium: {e}")
                raise
    
    def _close_selenium(self):
        """Close Selenium WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.logger.info("Selenium WebDriver closed")
            except Exception as e:
                self.logger.error(f"Error closing Selenium: {e}")
    
    def _generate_article_id(self, url: str, title: str) -> str:
        """
        Generate unique article ID
        
        Args:
            url: Article URL
            title: Article title
            
        Returns:
            Unique article ID
        """
        content = f"{url}:{title}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _extract_with_newspaper(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract article using newspaper3k
        
        Args:
            url: Article URL
            
        Returns:
            Article data or None
        """
        if not NEWSPAPER_AVAILABLE:
            self.logger.debug("newspaper3k is not available")
            return None
        
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            return {
                'url': url,
                'title': article.title,
                'text': article.text,
                'authors': article.authors,
                'publish_date': article.publish_date.isoformat() if article.publish_date else None,
                'top_image': article.top_image,
                'extracted_at': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error extracting article with newspaper3k: {e}")
            return None
    
    def _extract_with_beautifulsoup(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract article using BeautifulSoup
        
        Args:
            url: Article URL
            
        Returns:
            Article data or None
        """
        try:
            response = self.session.get(url, timeout=self.config.request_timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = None
            title_tag = soup.find('h1') or soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
            
            # Extract text from paragraphs
            paragraphs = soup.find_all('p')
            text = ' '.join([p.get_text().strip() for p in paragraphs])
            
            return {
                'url': url,
                'title': title,
                'text': text,
                'extracted_at': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error extracting article with BeautifulSoup: {e}")
            return None
    
    def _extract_with_selenium(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract article using Selenium
        
        Args:
            url: Article URL
            
        Returns:
            Article data or None
        """
        if not SELENIUM_AVAILABLE:
            self.logger.debug("Selenium is not available")
            return None
        
        try:
            if self.driver is None:
                self._init_selenium()
            
            if self.driver is None:
                return None
            
            self.driver.get(url)
            time.sleep(2)  # Wait for page to load
            
            # Extract title
            title = None
            try:
                title_element = self.driver.find_element(By.TAG_NAME, 'h1')
                title = title_element.text.strip()
            except:
                title = self.driver.title
            
            # Extract text
            paragraphs = self.driver.find_elements(By.TAG_NAME, 'p')
            text = ' '.join([p.text.strip() for p in paragraphs])
            
            return {
                'url': url,
                'title': title,
                'text': text,
                'extracted_at': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error extracting article with Selenium: {e}")
            return None
    
    def extract_article(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract article content from URL
        
        Args:
            url: Article URL
            
        Returns:
            Article data or None
        """
        self.logger.info(f"Extracting article: {url}")
        
        # Try newspaper3k first (most reliable)
        article_data = self._extract_with_newspaper(url)
        
        # Fallback to BeautifulSoup
        if not article_data or not article_data.get('text'):
            article_data = self._extract_with_beautifulsoup(url)
        
        # Fallback to Selenium if enabled
        if (not article_data or not article_data.get('text')) and self.config.use_selenium:
            article_data = self._extract_with_selenium(url)
        
        if article_data and article_data.get('title') and article_data.get('text'):
            article_data['id'] = self._generate_article_id(url, article_data['title'])
            return article_data
        
        return None
    
    def _find_article_links(self, url: str) -> List[str]:
        """
        Find article links on a page
        
        Args:
            url: Page URL
            
        Returns:
            List of article URLs
        """
        try:
            response = self.session.get(url, timeout=self.config.request_timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            links = []
            
            # Find all links
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                # Convert relative URLs to absolute
                if href.startswith('/'):
                    from urllib.parse import urljoin
                    href = urljoin(url, href)
                
                # Filter for article-like URLs
                if href.startswith('http') and any(pattern in href.lower() for pattern in [
                    'article', 'news', 'story', 'post', '/20', 'finance', 'market', 'stock'
                ]):
                    links.append(href)
            
            return list(set(links))  # Remove duplicates
        except Exception as e:
            self.logger.error(f"Error finding article links: {e}")
            return []
    
    def scrape_news_source(self, source_url: str, stocks: List[str], max_articles: int = 10) -> List[Dict[str, Any]]:
        """
        Scrape news from a source for specific stocks
        
        Args:
            source_url: News source URL
            stocks: List of stock symbols to filter
            max_articles: Maximum articles to return
            
        Returns:
            List of article data
        """
        self.logger.info(f"Scraping news from: {source_url}")
        
        articles = []
        article_links = self._find_article_links(source_url)
        
        self.logger.info(f"Found {len(article_links)} potential article links")
        
        for link in article_links[:max_articles * 2]:  # Get more links to filter
            article_data = self.extract_article(link)
            
            if article_data:
                # Check if article mentions any of the stocks
                text_lower = (article_data.get('text', '') + ' ' + article_data.get('title', '')).lower()
                
                for stock in stocks:
                    stock_patterns = [
                        stock.lower(),
                        stock.upper(),
                        f"${stock.upper()}",  # Ticker format
                    ]
                    
                    if any(pattern in text_lower for pattern in stock_patterns):
                        article_data['stock'] = stock.upper()
                        articles.append(article_data)
                        self.logger.info(f"Found article for {stock}: {article_data['title'][:50]}...")
                        break
            
            if len(articles) >= max_articles:
                break
            
            time.sleep(0.5)  # Rate limiting
        
        return articles
    
    def scrape_all_sources(self, stocks: List[str], max_articles_per_source: int = 10) -> List[Dict[str, Any]]:
        """
        Scrape all configured news sources
        
        Args:
            stocks: List of stock symbols
            max_articles_per_source: Maximum articles per source
            
        Returns:
            List of all articles
        """
        all_articles = []
        
        for source in self.config.news_sources:
            try:
                articles = self.scrape_news_source(source, stocks, max_articles_per_source)
                all_articles.extend(articles)
                self.logger.info(f"Scraped {len(articles)} articles from {source}")
            except Exception as e:
                self.logger.error(f"Error scraping {source}: {e}")
        
        # Close Selenium if it was used
        self._close_selenium()
        
        return all_articles
    
    def __del__(self):
        """Cleanup on deletion"""
        self._close_selenium()


# Made with Bob