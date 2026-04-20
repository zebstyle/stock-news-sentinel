"""
Sentiment Analyzer Agent
Autonomous agent for analyzing sentiment of news articles
"""

from typing import List, Dict, Any
from datetime import datetime

from services.sentiment import SentimentAnalyzer
from utils.config import Config
from utils.state_manager import StateManager
from utils.logger import LoggerMixin


class SentimentAnalyzerAgent(LoggerMixin):
    """Agent that autonomously analyzes sentiment of articles"""
    
    def __init__(self, config: Config, state_manager: StateManager):
        """
        Initialize sentiment analyzer agent
        
        Args:
            config: Configuration instance
            state_manager: State manager instance
        """
        self.config = config
        self.state_manager = state_manager
        self.analyzer = SentimentAnalyzer(config)
    
    def analyze_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze sentiment of a single article
        
        Args:
            article: Article data
            
        Returns:
            Article with sentiment data added
        """
        try:
            title = article.get('title', '')
            text = article.get('text', '')
            
            # Perform sentiment analysis
            sentiment_result = self.analyzer.analyze(text, title)
            
            # Determine impact
            impact, impact_description = self.analyzer.determine_impact(sentiment_result)
            
            # Add sentiment data to article
            article_with_sentiment = {
                **article,
                'sentiment_score': sentiment_result['sentiment_score'],
                'sentiment_label': sentiment_result['sentiment_label'],
                'confidence': sentiment_result['confidence'],
                'sentiment_model': sentiment_result['model'],
                'impact': impact,
                'impact_description': impact_description,
                'analyzed_at': datetime.now().isoformat()
            }
            
            self.logger.info(
                f"Analyzed article for {article.get('stock', 'Unknown')}: "
                f"{sentiment_result['sentiment_label']} ({sentiment_result['sentiment_score']:.2f})"
            )
            
            return article_with_sentiment
            
        except Exception as e:
            self.logger.error(f"Error analyzing article: {e}", exc_info=True)
            # Return article with neutral sentiment on error
            return {
                **article,
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'confidence': 0.0,
                'sentiment_model': 'error',
                'impact': 'neutral',
                'impact_description': 'Analysis failed',
                'analyzed_at': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def analyze_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze sentiment of multiple articles
        
        Args:
            articles: List of articles
            
        Returns:
            List of articles with sentiment data
        """
        analyzed_articles = []
        
        for i, article in enumerate(articles, 1):
            self.logger.info(f"Analyzing article {i}/{len(articles)}")
            analyzed_article = self.analyze_article(article)
            analyzed_articles.append(analyzed_article)
        
        # Persist only the latest scan's analyzed articles
        self.state_manager.replace_articles(analyzed_articles)
        
        return analyzed_articles
    
    def run(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run the sentiment analyzer agent
        
        Args:
            articles: List of articles to analyze
            
        Returns:
            Results dictionary with analyzed articles
        """
        self.logger.info(f"Sentiment Analyzer Agent starting with {len(articles)} articles...")
        
        start_time = datetime.now()
        
        try:
            if not articles:
                self.logger.info("No articles to analyze")
                return {
                    'success': True,
                    'articles': [],
                    'count': 0,
                    'message': 'No articles to analyze'
                }
            
            # Analyze all articles
            analyzed_articles = self.analyze_articles(articles)
            
            # Calculate statistics
            positive_count = sum(1 for a in analyzed_articles if a.get('sentiment_label') == 'positive')
            negative_count = sum(1 for a in analyzed_articles if a.get('sentiment_label') == 'negative')
            neutral_count = sum(1 for a in analyzed_articles if a.get('sentiment_label') == 'neutral')
            
            # Filter articles that should trigger alerts
            alert_articles = [
                a for a in analyzed_articles 
                if self.analyzer.should_alert({
                    'sentiment_score': a.get('sentiment_score', 0),
                    'confidence': a.get('confidence', 0)
                })
            ]
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.logger.info(
                f"Sentiment Analyzer Agent completed in {duration:.2f}s - "
                f"Positive: {positive_count}, Negative: {negative_count}, Neutral: {neutral_count}, "
                f"Alerts: {len(alert_articles)}"
            )
            
            return {
                'success': True,
                'articles': analyzed_articles,
                'alert_articles': alert_articles,
                'count': len(analyzed_articles),
                'statistics': {
                    'positive': positive_count,
                    'negative': negative_count,
                    'neutral': neutral_count,
                    'alerts': len(alert_articles)
                },
                'duration': duration,
                'timestamp': end_time.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in Sentiment Analyzer Agent: {e}", exc_info=True)
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
            'agent': 'SentimentAnalyzerAgent',
            'status': 'active',
            'total_analyzed': stats.get('total_articles', 0),
            'positive_articles': stats.get('positive_articles', 0),
            'negative_articles': stats.get('negative_articles', 0),
            'neutral_articles': stats.get('neutral_articles', 0)
        }


# Made with Bob