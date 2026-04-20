"""
State Management Module
Handles in-memory state management for the application using Streamlit session state
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from .logger import LoggerMixin


class StateManager(LoggerMixin):
    """Manages application state in memory and provides persistence"""
    
    def __init__(self, data_file: str = "data/analyzed_articles.json"):
        """
        Initialize state manager
        
        Args:
            data_file: Path to JSON file for persistence
        """
        self.data_file = data_file
        self.state: Dict[str, Any] = {
            'articles': {},
            'last_scan': None,
            'scan_count': 0,
            'alert_count': 0,
            'stats': {
                'total_articles': 0,
                'positive_articles': 0,
                'negative_articles': 0,
                'neutral_articles': 0
            }
        }
        self._load_from_file()
    
    def _load_from_file(self):
        """Load state from JSON file if it exists"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.state['articles'] = data.get('articles', {})
                    self.state['last_scan'] = data.get('last_scan')
                    self.state['scan_count'] = data.get('scan_count', 0)
                    self.state['alert_count'] = data.get('alert_count', 0)
                    self._recalculate_stats()
                    self.logger.info(f"Loaded {len(self.state['articles'])} articles from {self.data_file}")
            except Exception as e:
                self.logger.error(f"Error loading state from file: {e}")
    
    def _save_to_file(self):
        """Save state to JSON file"""
        try:
            Path(self.data_file).parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'articles': self.state['articles'],
                    'last_scan': self.state['last_scan'],
                    'scan_count': self.state['scan_count'],
                    'alert_count': self.state['alert_count'],
                    'stats': self.state['stats'],
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"State saved to {self.data_file}")
        except Exception as e:
            self.logger.error(f"Error saving state to file: {e}")

    def _recalculate_stats(self):
        """Recalculate article statistics from current in-memory state."""
        articles = list(self.state['articles'].values())
        self.state['stats'] = {
            'total_articles': len(articles),
            'positive_articles': sum(1 for article in articles if article.get('sentiment_label', '').lower() == 'positive'),
            'negative_articles': sum(1 for article in articles if article.get('sentiment_label', '').lower() == 'negative'),
            'neutral_articles': sum(1 for article in articles if article.get('sentiment_label', '').lower() == 'neutral')
        }
    
    def add_article(self, article_id: str, article_data: Dict[str, Any]):
        """
        Add or update an article in state
        
        Args:
            article_id: Unique article identifier
            article_data: Article data dictionary
        """
        self.state['articles'][article_id] = {
            **article_data,
            'added_at': datetime.now().isoformat()
        }
        
        self._recalculate_stats()
        self._save_to_file()
        self.logger.debug(f"Added article: {article_id}")

    def replace_articles(self, articles: List[Dict[str, Any]]):
        """
        Replace all persisted articles with the latest scan articles only.
        
        Args:
            articles: Latest analyzed articles for current scan
        """
        replaced_articles: Dict[str, Dict[str, Any]] = {}
        timestamp = datetime.now().isoformat()

        for article in articles:
            article_id = article.get('id')
            if not article_id:
                continue
            replaced_articles[article_id] = {
                **article,
                'added_at': timestamp
            }

        self.state['articles'] = replaced_articles
        self._recalculate_stats()
        self._save_to_file()
        self.logger.info(f"Replaced persisted articles with {len(replaced_articles)} latest-scan records")
    
    def get_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        """
        Get article by ID
        
        Args:
            article_id: Article identifier
            
        Returns:
            Article data or None if not found
        """
        return self.state['articles'].get(article_id)
    
    def article_exists(self, article_id: str) -> bool:
        """
        Check if article exists in state
        
        Args:
            article_id: Article identifier
            
        Returns:
            True if article exists
        """
        return article_id in self.state['articles']
    
    def get_all_articles(self) -> Dict[str, Dict[str, Any]]:
        """Get all articles"""
        return self.state['articles']
    
    def get_recent_articles(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most recent articles
        
        Args:
            limit: Maximum number of articles to return
            
        Returns:
            List of recent articles
        """
        articles = list(self.state['articles'].values())
        articles.sort(key=lambda x: x.get('added_at', ''), reverse=True)
        return articles[:limit]
    
    def get_articles_by_stock(self, stock: str) -> List[Dict[str, Any]]:
        """
        Get articles for a specific stock
        
        Args:
            stock: Stock symbol
            
        Returns:
            List of articles for the stock
        """
        return [
            article for article in self.state['articles'].values()
            if article.get('stock', '').upper() == stock.upper()
        ]
    
    def get_articles_by_sentiment(self, sentiment: str) -> List[Dict[str, Any]]:
        """
        Get articles by sentiment
        
        Args:
            sentiment: Sentiment label (positive, negative, neutral)
            
        Returns:
            List of articles with matching sentiment
        """
        return [
            article for article in self.state['articles'].values()
            if article.get('sentiment_label', '').lower() == sentiment.lower()
        ]
    
    def update_scan_info(self):
        """Update last scan timestamp and count"""
        self.state['last_scan'] = datetime.now().isoformat()
        self.state['scan_count'] += 1
        self._save_to_file()
        self.logger.info(f"Scan #{self.state['scan_count']} completed")
    
    def increment_alert_count(self):
        """Increment alert counter"""
        self.state['alert_count'] += 1
        self._save_to_file()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics
        
        Returns:
            Statistics dictionary
        """
        return {
            **self.state['stats'],
            'last_scan': self.state['last_scan'],
            'scan_count': self.state['scan_count'],
            'alert_count': self.state['alert_count']
        }
    
    def cleanup_old_articles(self, days: int = 30):
        """
        Remove articles older than specified days
        
        Args:
            days: Number of days to keep
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        articles_to_remove = []
        for article_id, article in self.state['articles'].items():
            added_at = article.get('added_at')
            if added_at:
                try:
                    article_date = datetime.fromisoformat(added_at)
                    if article_date < cutoff_date:
                        articles_to_remove.append(article_id)
                except ValueError:
                    pass
        
        for article_id in articles_to_remove:
            del self.state['articles'][article_id]
        
        if articles_to_remove:
            self._recalculate_stats()
            self._save_to_file()
            self.logger.info(f"Cleaned up {len(articles_to_remove)} old articles")
    
    def clear_articles(self):
        """Clear only persisted article data while preserving scan counters."""
        self.state['articles'] = {}
        self._recalculate_stats()
        self._save_to_file()
        self.logger.info("Article state cleared")
    
    def clear_all(self):
        """Clear all state (use with caution)"""
        self.state = {
            'articles': {},
            'last_scan': None,
            'scan_count': 0,
            'alert_count': 0,
            'stats': {
                'total_articles': 0,
                'positive_articles': 0,
                'negative_articles': 0,
                'neutral_articles': 0
            }
        }
        self._save_to_file()
        self.logger.warning("All state cleared")


# Global state manager instance
_state_manager_instance = None


def get_state_manager(data_file: str = "data/analyzed_articles.json") -> StateManager:
    """
    Get global state manager instance
    
    Args:
        data_file: Path to data file
        
    Returns:
        StateManager instance
    """
    global _state_manager_instance
    if _state_manager_instance is None:
        _state_manager_instance = StateManager(data_file)
    return _state_manager_instance


# Made with Bob