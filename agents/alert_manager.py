"""
Alert Manager Agent
Autonomous agent for managing and sending email alerts
"""

from typing import List, Dict, Any
from datetime import datetime

from services.email_service import EmailService
from utils.config import Config
from utils.state_manager import StateManager
from utils.logger import LoggerMixin


class AlertManagerAgent(LoggerMixin):
    """Agent that autonomously manages email alerts"""
    
    def __init__(self, config: Config, state_manager: StateManager):
        """
        Initialize alert manager agent
        
        Args:
            config: Configuration instance
            state_manager: State manager instance
        """
        self.config = config
        self.state_manager = state_manager
        self.email_service = EmailService(config)
    
    def send_article_alert(self, article: Dict[str, Any]) -> bool:
        """
        Send alert for a single article
        
        Args:
            article: Article with sentiment data
            
        Returns:
            True if alert sent successfully
        """
        try:
            # Extract sentiment data
            sentiment = {
                'sentiment_score': article.get('sentiment_score', 0),
                'sentiment_label': article.get('sentiment_label', 'neutral'),
                'confidence': article.get('confidence', 0),
                'model': article.get('sentiment_model', 'unknown')
            }
            
            # Send email
            success = self.email_service.send_alert(article, sentiment)
            
            if success:
                self.state_manager.increment_alert_count()
                self.logger.info(f"Alert sent for {article.get('stock', 'Unknown')}: {article.get('title', '')[:50]}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending article alert: {e}", exc_info=True)
            return False
    
    def send_alerts(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Send alerts for multiple articles
        
        Args:
            articles: List of articles to alert on
            
        Returns:
            Results dictionary
        """
        if not articles:
            self.logger.info("No articles to alert on")
            return {
                'success': True,
                'sent': 0,
                'failed': 0,
                'total': 0
            }
        
        sent_count = 0
        failed_count = 0
        
        for article in articles:
            if self.send_article_alert(article):
                sent_count += 1
            else:
                failed_count += 1
        
        self.logger.info(f"Alerts sent: {sent_count}, Failed: {failed_count}")
        
        return {
            'success': True,
            'sent': sent_count,
            'failed': failed_count,
            'total': len(articles)
        }
    
    def send_summary(self, articles: List[Dict[str, Any]]) -> bool:
        """
        Send daily summary email
        
        Args:
            articles: List of articles for summary
            
        Returns:
            True if summary sent successfully
        """
        try:
            if not self.config.send_daily_summary:
                self.logger.info("Daily summary disabled in config")
                return False
            
            success = self.email_service.send_daily_summary(articles)
            
            if success:
                self.logger.info(f"Daily summary sent with {len(articles)} articles")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending daily summary: {e}", exc_info=True)
            return False
    
    def run(self, alert_articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run the alert manager agent
        
        Args:
            alert_articles: List of articles that should trigger alerts
            
        Returns:
            Results dictionary
        """
        self.logger.info(f"Alert Manager Agent starting with {len(alert_articles)} articles...")
        
        start_time = datetime.now()
        
        try:
            if not alert_articles:
                self.logger.info("No articles require alerts")
                return {
                    'success': True,
                    'sent': 0,
                    'failed': 0,
                    'total': 0,
                    'message': 'No articles require alerts'
                }
            
            # Filter articles if only significant alerts are enabled
            articles_to_alert = alert_articles
            if self.config.alert_significant_only:
                articles_to_alert = [
                    a for a in alert_articles
                    if abs(a.get('sentiment_score', 0)) >= self.config.sentiment_threshold
                ]
                self.logger.info(f"Filtered to {len(articles_to_alert)} significant articles")
            
            # Send individual alerts
            alert_results = self.send_alerts(articles_to_alert)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.logger.info(f"Alert Manager Agent completed in {duration:.2f}s")
            
            return {
                'success': True,
                'sent': alert_results['sent'],
                'failed': alert_results['failed'],
                'total': alert_results['total'],
                'duration': duration,
                'timestamp': end_time.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in Alert Manager Agent: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'sent': 0,
                'failed': 0,
                'total': 0
            }
    
    def test_email_connection(self) -> bool:
        """
        Test email connection
        
        Returns:
            True if connection successful
        """
        return self.email_service.test_connection()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get agent status
        
        Returns:
            Status dictionary
        """
        stats = self.state_manager.get_stats()
        
        return {
            'agent': 'AlertManagerAgent',
            'status': 'active',
            'alert_count': stats.get('alert_count', 0),
            'email_configured': bool(self.config.email_from and self.config.email_password)
        }


# Made with Bob