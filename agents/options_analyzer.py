"""
Options Analyzer Agent
Autonomous agent for analyzing news events and providing options trading recommendations
"""

from typing import List, Dict, Any
from datetime import datetime, timezone

from services.options_extractor import OptionsFeatureExtractor
from services.options_rules_engine import OptionsRulesEngine
from services.options_scoring import OptionsScoring
from services.market_data_service import MarketDataService
from utils.config import Config
from utils.state_manager import StateManager
from utils.logger import LoggerMixin


class OptionsAnalyzerAgent(LoggerMixin):
    """Agent that analyzes news for options trading implications"""
    
    def __init__(self, config: Config, state_manager: StateManager):
        """
        Initialize options analyzer agent
        
        Args:
            config: Configuration instance
            state_manager: State manager instance
        """
        self.config = config
        self.state_manager = state_manager
        self.extractor = OptionsFeatureExtractor()
        self.rules_engine = OptionsRulesEngine()
        self.scoring = OptionsScoring()
        self.market_data_service = MarketDataService(config)
    
    def analyze_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single article for options implications
        
        Args:
            article: Article with sentiment analysis
            
        Returns:
            Complete options analysis
        """
        try:
            # Step 1: Extract LLM features
            llm_extraction = self.extractor.extract_features(article)
            
            # Step 2: Enrich with market data
            market_data = self._get_market_data(article, llm_extraction)

            # Step 3: Apply deterministic rules
            options_impact = self.rules_engine.apply_rules(llm_extraction, market_data)
            
            # Step 4: Calculate scores
            scores = self.scoring.calculate_all_scores(llm_extraction)
            score_interpretations = self.scoring.interpret_scores(scores)
            
            # Step 5: Build final report
            report = self._build_report(
                article,
                llm_extraction,
                options_impact,
                market_data,
                scores,
                score_interpretations
            )
            
            self.logger.info(
                f"Options analysis complete for {article.get('stock', 'Unknown')}: "
                f"Strategy family: {options_impact['option_view']['strategy_preference']['best_trade_family']}"
            )
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error analyzing article for options: {e}", exc_info=True)
            return {
                'ticker': article.get('stock', 'UNKNOWN'),
                'error': str(e),
                'success': False
            }
    
    def analyze_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze multiple articles for options implications
        
        Consolidates results to one latest/best record per ticker.
        
        Args:
            articles: List of articles with sentiment analysis
            
        Returns:
            List of consolidated options analyses
        """
        analyses_by_ticker: Dict[str, Dict[str, Any]] = {}
        
        for i, article in enumerate(articles, 1):
            self.logger.info(f"Analyzing article {i}/{len(articles)} for options")
            analysis = self.analyze_article(article)
            if not analysis.get('success', True):
                continue

            ticker = analysis.get('ticker', 'UNKNOWN').upper()
            existing = analyses_by_ticker.get(ticker)

            if existing is None or self._is_better_analysis(analysis, existing):
                analyses_by_ticker[ticker] = analysis
        
        consolidated = sorted(
            analyses_by_ticker.values(),
            key=lambda x: (
                x.get('scores', {}).get('tradability_score', 0),
                x.get('confidence', 0),
                x.get('analyzed_at', '')
            ),
            reverse=True
        )

        self.logger.info(
            f"Consolidated {len(articles)} article analyses into {len(consolidated)} ticker-level analyses"
        )

        return consolidated
    
    def run(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run the options analyzer agent
        
        Args:
            articles: List of articles with sentiment analysis
            
        Returns:
            Results dictionary with options analyses
        """
        self.logger.info(f"Options Analyzer Agent starting with {len(articles)} articles...")
        
        start_time = datetime.now()
        
        try:
            if not articles:
                self.logger.info("No articles to analyze for options")
                return {
                    'success': True,
                    'analyses': [],
                    'count': 0,
                    'message': 'No articles to analyze'
                }
            
            analyses = self.analyze_articles(articles)
            stats = self._calculate_statistics(analyses)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.logger.info(
                f"Options Analyzer Agent completed in {duration:.2f}s - "
                f"Generated {len(analyses)} consolidated ticker analyses"
            )
            
            return {
                'success': True,
                'analyses': analyses,
                'count': len(analyses),
                'statistics': stats,
                'duration': duration,
                'timestamp': end_time.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in Options Analyzer Agent: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'analyses': []
            }
    
    def _build_report(
        self,
        article: Dict[str, Any],
        llm_extraction: Dict[str, Any],
        options_impact: Dict[str, Any],
        market_data: Dict[str, Any],
        scores: Dict[str, float],
        score_interpretations: Dict[str, str]
    ) -> Dict[str, Any]:
        """Build comprehensive options analysis report"""
        
        ticker = article.get('stock', 'UNKNOWN')
        option_view = options_impact['option_view']
        
        headline = self._generate_headline_assessment(
            llm_extraction['bias'],
            option_view['strategy_preference']['best_trade_family'],
            scores['tradability_score']
        )
        
        return {
            'success': True,
            'ticker': ticker,
            'market_data': market_data,
            'headline_assessment': headline,
            'news_classification': {
                'event_type': llm_extraction['event_type'],
                'bias': llm_extraction['bias'],
                'strength': llm_extraction['bias_strength'],
                'freshness': llm_extraction['freshness'],
                'source_trust': llm_extraction['source_trust']
            },
            'spot_forecast': option_view['spot_view'],
            'vol_forecast': option_view['vol_view'],
            'premium_forecast': option_view['premium_impact'],
            'trade_setup': option_view.get('trade_setup', {}),
            'strategy_view': {
                'best_family': option_view['strategy_preference']['best_trade_family'],
                'preferred': option_view['strategy_preference']['preferred'],
                'acceptable': option_view['strategy_preference']['acceptable'],
                'avoid': option_view['strategy_preference']['avoid'],
                'why': option_view['summary']
            },
            'consolidated_view': option_view.get('consolidated_view', {}),
            'scores': scores,
            'score_interpretations': score_interpretations,
            'confidence': option_view['confidence'],
            'key_risks': llm_extraction['key_risks'],
            'reasoning': llm_extraction['reasoning'],
            'article_title': article.get('title', ''),
            'article_url': article.get('url', ''),
            'news_timestamp': article.get('published_at', ''),
            'analyzed_at': datetime.now().isoformat()
        }
    
    def _get_market_data(self, article: Dict[str, Any], llm_extraction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build market data enrichment layer.

        Priority:
        1. Live Alpha Vantage quote lookup
        2. Explicit price fields attached to article, only if close enough to live quote or live quote unavailable
        3. Deterministic fallback estimation
        """
        ticker = llm_extraction.get('ticker', 'UNKNOWN')
        explicit_price = (
            article.get('current_price')
            or article.get('market_price')
            or article.get('ltp')
            or article.get('price')
        )

        self.logger.info(f"Getting market data for {ticker}, explicit_price={explicit_price}")
        
        live_market_data = self.market_data_service.get_market_data(ticker)
        
        if live_market_data:
            self.logger.info(f"Live market data received for {ticker}: price={live_market_data.get('current_price')}")
            
            # Only validate if article has an explicit price to compare
            if explicit_price is not None:
                try:
                    self.logger.info(f"Validating article price {explicit_price} against API price {live_market_data.get('current_price')}")
                    validated_market_data = self._apply_price_validation(
                        article=article,
                        llm_extraction=llm_extraction,
                        market_data=live_market_data,
                        explicit_price=float(explicit_price)
                    )
                    if not validated_market_data.get('trade_allowed', True):
                        self.logger.warning(
                            f"Trade blocked for {ticker}: API price={validated_market_data.get('current_price')}, "
                            f"Article price={validated_market_data.get('article_price')}, "
                            f"Deviation={validated_market_data.get('price_deviation_pct')}%"
                        )
                    else:
                        self.logger.info(f"Price validation passed for {ticker}")
                    return validated_market_data
                except (ValueError, TypeError) as e:
                    self.logger.warning(
                        f"Failed to validate article price for {ticker}: {e}. Using live market data."
                    )
                    return live_market_data
            
            # No article price to validate, use live data directly
            self.logger.info(f"Using live market data for {ticker} (no article price to validate): price={live_market_data.get('current_price')}")
            return live_market_data
        
        self.logger.warning(f"No live market data available for {ticker}")

        if explicit_price is not None:
            self.logger.warning(
                f"Falling back to article-attached price for {ticker}: {explicit_price}"
            )
            return self._build_market_data_from_explicit_price(article, llm_extraction, float(explicit_price))

        self.logger.warning(f"Using fallback pseudo-price calculation for {ticker}")
        return self._build_fallback_market_data(article, llm_extraction)

    def _build_market_data_from_explicit_price(
        self,
        article: Dict[str, Any],
        llm_extraction: Dict[str, Any],
        current_price: float
    ) -> Dict[str, Any]:
        """Normalize explicit article-attached price into market-data schema."""
        move_low = float(llm_extraction.get('expected_spot_move_pct_low', 0.0))
        move_high = float(llm_extraction.get('expected_spot_move_pct_high', 0.0))
        avg_move = (move_low + move_high) / 2.0
        sentiment_score = abs(float(article.get('sentiment_score', 0.0)))

        if avg_move < 2:
            volatility_context = 'low'
        elif avg_move <= 4:
            volatility_context = 'moderate'
        else:
            volatility_context = 'high'

        bias = llm_extraction.get('bias')
        if bias == 'bullish':
            day_change_pct = round(min(move_high, max(0.3, sentiment_score * 2.0)), 2)
        elif bias == 'bearish':
            day_change_pct = round(-min(move_high, max(0.3, sentiment_score * 2.0)), 2)
        else:
            day_change_pct = 0.0

        return {
            'current_price': round(current_price, 2),
            'last_updated': datetime.now(timezone.utc).astimezone().isoformat(),
            'day_change_pct': day_change_pct,
            'volatility_context': volatility_context,
            'source': 'article',
            'source_label': 'Article',
            'is_fresh': False,
            'trade_allowed': True,
            'price_deviation_pct': 0.0
        }

    def _apply_price_validation(
        self,
        article: Dict[str, Any],
        llm_extraction: Dict[str, Any],
        market_data: Dict[str, Any],
        explicit_price: float
    ) -> Dict[str, Any]:
        """Validate article price against API price and reject trade if divergence is too large."""
        validated_market_data = dict(market_data)
        api_price = float(validated_market_data.get('current_price', 0.0))

        if api_price <= 0:
            validated_market_data['trade_allowed'] = False
            validated_market_data['price_deviation_pct'] = None
            validated_market_data['validation_warning'] = 'invalid_api_price'
            return validated_market_data

        price_deviation_pct = round(abs(explicit_price - api_price) / api_price * 100, 2)
        validated_market_data['price_deviation_pct'] = price_deviation_pct
        validated_market_data['article_price'] = round(explicit_price, 2)
        validated_market_data['trade_allowed'] = price_deviation_pct <= 2.0

        if not validated_market_data['trade_allowed']:
            validated_market_data['validation_warning'] = 'article_price_deviates_from_api'

        return validated_market_data

    def _build_fallback_market_data(self, article: Dict[str, Any], llm_extraction: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback market data when live and explicit pricing are unavailable."""
        move_low = float(llm_extraction.get('expected_spot_move_pct_low', 0.0))
        move_high = float(llm_extraction.get('expected_spot_move_pct_high', 0.0))
        avg_move = (move_low + move_high) / 2.0
        sentiment_score = abs(float(article.get('sentiment_score', 0.0)))

        ticker_seed = sum(ord(ch) for ch in llm_extraction.get('ticker', 'UNKNOWN'))
        current_price = round(500 + (ticker_seed % 2500) + (sentiment_score * 25), 2)

        if avg_move < 2:
            volatility_context = 'low'
        elif avg_move <= 4:
            volatility_context = 'moderate'
        else:
            volatility_context = 'high'

        bias = llm_extraction.get('bias')
        if bias == 'bullish':
            day_change_pct = round(min(move_high, max(0.3, sentiment_score * 2.0)), 2)
        elif bias == 'bearish':
            day_change_pct = round(-min(move_high, max(0.3, sentiment_score * 2.0)), 2)
        else:
            day_change_pct = 0.0

        self.logger.warning(
            f"Using fallback pseudo-price for {llm_extraction.get('ticker', 'UNKNOWN')} because live quote "
            f"and article price were unavailable"
        )

        return {
            'current_price': current_price,
            'last_updated': datetime.now(timezone.utc).astimezone().isoformat(),
            'day_change_pct': day_change_pct,
            'volatility_context': volatility_context,
            'source': 'fallback',
            'source_label': 'Fallback',
            'is_fresh': False,
            'trade_allowed': False,
            'price_deviation_pct': None
        }
    
    def _generate_headline_assessment(
        self,
        bias: str,
        strategy_family: str,
        tradability: float
    ) -> str:
        """Generate headline assessment"""
        
        if tradability < 3:
            return f"{bias.title()} signal but not tradable - avoid"
        elif tradability < 5:
            return f"{bias.title()} signal - watch only, low confidence"
        elif 'avoid' in strategy_family.lower() or 'no_trade' in strategy_family.lower():
            return f"{bias.title()} but unclear setup - better to wait"
        elif 'defined_risk' in strategy_family.lower():
            return f"{bias.title()} - use defined-risk strategies"
        elif 'long_volatility' in strategy_family.lower():
            return f"Binary event - consider long volatility strategies"
        elif 'short_volatility' in strategy_family.lower():
            return f"Low impact event - premium selling opportunity"
        else:
            return f"{bias.title()} - directional opportunity"

    def _is_better_analysis(self, candidate: Dict[str, Any], existing: Dict[str, Any]) -> bool:
        """Choose the better per-ticker analysis, favoring latest high-quality setup with real market data."""
        candidate_scores = candidate.get('scores', {})
        existing_scores = existing.get('scores', {})
        
        # Prioritize real market data over fallback
        candidate_market_data = candidate.get('market_data', {})
        existing_market_data = existing.get('market_data', {})
        
        candidate_data_quality = 2 if candidate_market_data.get('source') == 'alpha_vantage' else (
            1 if candidate_market_data.get('source') == 'article' else 0
        )
        existing_data_quality = 2 if existing_market_data.get('source') == 'alpha_vantage' else (
            1 if existing_market_data.get('source') == 'article' else 0
        )

        candidate_rank = (
            candidate_data_quality,  # Prioritize real market data first
            candidate_scores.get('tradability_score', 0),
            candidate.get('confidence', 0),
            candidate.get('news_classification', {}).get('strength', 0),
            candidate.get('news_timestamp', ''),
            candidate.get('analyzed_at', '')
        )
        existing_rank = (
            existing_data_quality,
            existing_scores.get('tradability_score', 0),
            existing.get('confidence', 0),
            existing.get('news_classification', {}).get('strength', 0),
            existing.get('news_timestamp', ''),
            existing.get('analyzed_at', '')
        )

        return candidate_rank >= existing_rank
    
    def _calculate_statistics(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics"""
        
        if not analyses:
            return {}
        
        bullish = sum(1 for a in analyses if a.get('news_classification', {}).get('bias') == 'bullish')
        bearish = sum(1 for a in analyses if a.get('news_classification', {}).get('bias') == 'bearish')
        neutral = sum(1 for a in analyses if a.get('news_classification', {}).get('bias') == 'neutral')
        binary = sum(1 for a in analyses if a.get('news_classification', {}).get('bias') == 'binary')
        
        strategy_families = {}
        for analysis in analyses:
            family = analysis.get('strategy_view', {}).get('best_family', 'unknown')
            strategy_families[family] = strategy_families.get(family, 0) + 1
        
        tradable = sum(1 for a in analyses if a.get('scores', {}).get('tradability_score', 0) >= 5)
        
        avg_spot_score = sum(a.get('scores', {}).get('spot_direction_score', 0) for a in analyses) / len(analyses)
        avg_vol_score = sum(a.get('scores', {}).get('volatility_score', 0) for a in analyses) / len(analyses)
        avg_tradability = sum(a.get('scores', {}).get('tradability_score', 0) for a in analyses) / len(analyses)
        
        return {
            'total_analyzed': len(analyses),
            'by_bias': {
                'bullish': bullish,
                'bearish': bearish,
                'neutral': neutral,
                'binary': binary
            },
            'by_strategy_family': strategy_families,
            'tradable_count': tradable,
            'non_tradable_count': len(analyses) - tradable,
            'average_scores': {
                'spot_direction': round(avg_spot_score, 2),
                'volatility': round(avg_vol_score, 2),
                'tradability': round(avg_tradability, 2)
            }
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get agent status
        
        Returns:
            Status dictionary
        """
        return {
            'agent': 'OptionsAnalyzerAgent',
            'status': 'active',
            'components': {
                'extractor': 'OptionsFeatureExtractor',
                'rules_engine': 'OptionsRulesEngine',
                'scoring': 'OptionsScoring',
                'market_data_service': 'MarketDataService'
            }
        }


# Made with Bob