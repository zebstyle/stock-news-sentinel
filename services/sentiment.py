"""
Sentiment Analysis Service
Performs sentiment analysis on news articles using FinBERT and other models
"""

from typing import Dict, Any, Optional, Tuple
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Optional imports
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False

from utils.logger import LoggerMixin
from utils.config import Config


class SentimentAnalyzer(LoggerMixin):
    """Analyzes sentiment of news articles"""
    
    def __init__(self, config: Config):
        """
        Initialize sentiment analyzer
        
        Args:
            config: Configuration instance
        """
        self.config = config
        self.finbert_model = None
        self.finbert_tokenizer = None
        self.vader_analyzer = None
        self._init_models()
    
    def _init_models(self):
        """Initialize sentiment analysis models"""
        # Initialize VADER (always available as fallback)
        try:
            self.vader_analyzer = SentimentIntensityAnalyzer()
            self.logger.info("VADER sentiment analyzer initialized")
        except Exception as e:
            self.logger.error(f"Error initializing VADER: {e}")
        
        # Initialize FinBERT if it's the primary model
        if self.config.primary_sentiment_model == 'finbert':
            if not TRANSFORMERS_AVAILABLE:
                self.logger.warning("transformers library not available. Install transformers and torch to use FinBERT.")
                self.logger.warning("Falling back to VADER for sentiment analysis")
            else:
                try:
                    self.logger.info("Loading FinBERT model (this may take a while on first run)...")
                    model_name = "ProsusAI/finbert"
                    self.finbert_tokenizer = AutoTokenizer.from_pretrained(model_name)
                    self.finbert_model = AutoModelForSequenceClassification.from_pretrained(model_name)
                    self.finbert_model.eval()
                    self.logger.info("FinBERT model loaded successfully")
                except Exception as e:
                    self.logger.error(f"Error loading FinBERT: {e}")
                    self.logger.warning("Falling back to VADER for sentiment analysis")
    
    def _analyze_with_finbert(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Analyze sentiment using FinBERT
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment results or None
        """
        if not TRANSFORMERS_AVAILABLE or not self.finbert_model or not self.finbert_tokenizer:
            return None
        
        try:
            # Truncate text if too long
            max_length = 512
            inputs = self.finbert_tokenizer(
                text[:2000],  # Limit input length
                return_tensors="pt",
                truncation=True,
                max_length=max_length,
                padding=True
            )
            
            with torch.no_grad():
                outputs = self.finbert_model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # FinBERT labels: negative, neutral, positive
            scores = predictions[0].tolist()
            labels = ['negative', 'neutral', 'positive']
            
            # Get the dominant sentiment
            max_idx = scores.index(max(scores))
            sentiment_label = labels[max_idx]
            confidence = scores[max_idx]
            
            # Convert to -1 to 1 scale
            sentiment_score = scores[2] - scores[0]  # positive - negative
            
            return {
                'model': 'finbert',
                'sentiment_score': sentiment_score,
                'sentiment_label': sentiment_label,
                'confidence': confidence,
                'scores': {
                    'negative': scores[0],
                    'neutral': scores[1],
                    'positive': scores[2]
                }
            }
        except Exception as e:
            self.logger.error(f"Error in FinBERT analysis: {e}")
            return None
    
    def _analyze_with_vader(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Analyze sentiment using VADER
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment results or None
        """
        if not self.vader_analyzer:
            return None
        
        try:
            scores = self.vader_analyzer.polarity_scores(text)
            compound = scores['compound']
            
            # Determine sentiment label
            if compound >= 0.05:
                sentiment_label = 'positive'
            elif compound <= -0.05:
                sentiment_label = 'negative'
            else:
                sentiment_label = 'neutral'
            
            # Calculate confidence (absolute value of compound score)
            confidence = abs(compound)
            
            return {
                'model': 'vader',
                'sentiment_score': compound,
                'sentiment_label': sentiment_label,
                'confidence': confidence,
                'scores': {
                    'negative': scores['neg'],
                    'neutral': scores['neu'],
                    'positive': scores['pos'],
                    'compound': compound
                }
            }
        except Exception as e:
            self.logger.error(f"Error in VADER analysis: {e}")
            return None
    
    def _analyze_with_textblob(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Analyze sentiment using TextBlob
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment results or None
        """
        if not TEXTBLOB_AVAILABLE:
            return None
        
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # -1 to 1
            subjectivity = blob.sentiment.subjectivity  # 0 to 1
            
            # Determine sentiment label
            if polarity >= 0.1:
                sentiment_label = 'positive'
            elif polarity <= -0.1:
                sentiment_label = 'negative'
            else:
                sentiment_label = 'neutral'
            
            # Use subjectivity as confidence (more subjective = more confident)
            confidence = subjectivity
            
            return {
                'model': 'textblob',
                'sentiment_score': polarity,
                'sentiment_label': sentiment_label,
                'confidence': confidence,
                'scores': {
                    'polarity': polarity,
                    'subjectivity': subjectivity
                }
            }
        except Exception as e:
            self.logger.error(f"Error in TextBlob analysis: {e}")
            return None
    
    def _ensemble_analysis(self, results: list) -> Dict[str, Any]:
        """
        Combine multiple sentiment analysis results
        
        Args:
            results: List of sentiment results
            
        Returns:
            Combined sentiment result
        """
        if not results:
            return None
        
        # Average sentiment scores
        avg_score = sum(r['sentiment_score'] for r in results) / len(results)
        avg_confidence = sum(r['confidence'] for r in results) / len(results)
        
        # Determine label based on average score
        if avg_score >= 0.1:
            sentiment_label = 'positive'
        elif avg_score <= -0.1:
            sentiment_label = 'negative'
        else:
            sentiment_label = 'neutral'
        
        return {
            'model': 'ensemble',
            'sentiment_score': avg_score,
            'sentiment_label': sentiment_label,
            'confidence': avg_confidence,
            'individual_results': results
        }
    
    def analyze(self, text: str, title: str = "") -> Dict[str, Any]:
        """
        Analyze sentiment of text
        
        Args:
            text: Article text
            title: Article title (optional, will be prepended to text)
            
        Returns:
            Sentiment analysis results
        """
        # Combine title and text for analysis
        full_text = f"{title}. {text}" if title else text
        
        # Limit text length
        full_text = full_text[:5000]
        
        self.logger.info(f"Analyzing sentiment for text of length {len(full_text)}")
        
        results = []
        
        # Try primary model
        if self.config.primary_sentiment_model == 'finbert':
            result = self._analyze_with_finbert(full_text)
            if result:
                results.append(result)
        elif self.config.primary_sentiment_model == 'vader':
            result = self._analyze_with_vader(full_text)
            if result:
                results.append(result)
        elif self.config.primary_sentiment_model == 'textblob':
            result = self._analyze_with_textblob(full_text)
            if result:
                results.append(result)
        
        # Try fallback model if primary failed or ensemble is enabled
        if not results or self.config.enable_ensemble:
            if self.config.fallback_sentiment_model == 'vader':
                result = self._analyze_with_vader(full_text)
                if result:
                    results.append(result)
            elif self.config.fallback_sentiment_model == 'textblob':
                result = self._analyze_with_textblob(full_text)
                if result:
                    results.append(result)
        
        # If ensemble is enabled and we have multiple results, combine them
        if self.config.enable_ensemble and len(results) > 1:
            return self._ensemble_analysis(results)
        
        # Return the first result or a default
        if results:
            return results[0]
        
        # Default neutral sentiment if all models failed
        self.logger.warning("All sentiment models failed, returning neutral")
        return {
            'model': 'default',
            'sentiment_score': 0.0,
            'sentiment_label': 'neutral',
            'confidence': 0.0,
            'scores': {}
        }
    
    def determine_impact(self, sentiment_result: Dict[str, Any]) -> Tuple[str, str]:
        """
        Determine stock price impact from sentiment
        
        Args:
            sentiment_result: Sentiment analysis result
            
        Returns:
            Tuple of (impact, description)
        """
        score = sentiment_result['sentiment_score']
        confidence = sentiment_result['confidence']
        label = sentiment_result['sentiment_label']
        
        # Determine impact based on score and confidence
        if label == 'positive' and confidence >= self.config.confidence_threshold:
            if score >= 0.7:
                return 'very_positive', 'Strong bullish signal - likely positive price movement'
            else:
                return 'positive', 'Bullish signal - potential positive price movement'
        elif label == 'negative' and confidence >= self.config.confidence_threshold:
            if score <= -0.7:
                return 'very_negative', 'Strong bearish signal - likely negative price movement'
            else:
                return 'negative', 'Bearish signal - potential negative price movement'
        else:
            return 'neutral', 'Neutral signal - minimal expected price impact'
    
    def should_alert(self, sentiment_result: Dict[str, Any]) -> bool:
        """
        Determine if sentiment warrants an alert
        
        Args:
            sentiment_result: Sentiment analysis result
            
        Returns:
            True if alert should be sent
        """
        score = abs(sentiment_result['sentiment_score'])
        confidence = sentiment_result['confidence']
        
        # Alert if sentiment is strong and confidence is high
        return (score >= self.config.sentiment_threshold and 
                confidence >= self.config.confidence_threshold)


# Made with Bob