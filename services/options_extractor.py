"""
LLM Extraction Layer for Options Analysis
Extracts structured features from news articles for options trading
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from services.options_enums import (
    EventType, Bias, MoveBucket, Timing, IVReaction,
    GapRisk, Freshness, Novelty, DirectionClarity,
    ImpactPersistence, Uncertainty, RealizedVsImplied,
    MOVE_BUCKET_RANGES
)


class OptionsFeatureExtractor:
    """Extracts options-relevant features from analyzed news articles"""
    
    def __init__(self):
        """Initialize feature extractor"""
        self.event_keywords = self._init_event_keywords()
    
    def _init_event_keywords(self) -> Dict[str, List[str]]:
        """Initialize keyword mappings for event classification"""
        return {
            'earnings_beat': ['earnings beat', 'profit surge', 'revenue growth', 'strong results', 'quarterly beat'],
            'earnings_miss': ['earnings miss', 'profit decline', 'revenue miss', 'disappointing results'],
            'guidance_raise': ['guidance raise', 'forecast increase', 'outlook upgrade', 'raised guidance'],
            'guidance_cut': ['guidance cut', 'forecast reduction', 'outlook downgrade', 'lowered guidance'],
            'large_order_win': ['order win', 'contract award', 'deal signed', 'major order'],
            'regulatory_approval': ['approval', 'cleared', 'authorized', 'license granted'],
            'regulatory_action': ['investigation', 'probe', 'regulatory action', 'penalty'],
            'management_exit': ['ceo exit', 'cfo resign', 'management change', 'executive departure'],
            'promoter_buying': ['promoter buy', 'insider buying', 'promoter purchase'],
            'promoter_selling': ['promoter sell', 'insider selling', 'stake sale'],
            'fraud_or_governance': ['fraud', 'scam', 'governance issue', 'accounting irregularity'],
            'analyst_upgrade': ['upgrade', 'rating raised', 'target price increase'],
            'analyst_downgrade': ['downgrade', 'rating cut', 'target price reduction'],
            'product_launch': ['product launch', 'new product', 'product release'],
            'litigation': ['lawsuit', 'litigation', 'legal action', 'court case']
        }
    
    def extract_features(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract LLM-style features from article
        
        Args:
            article: Analyzed article with sentiment
            
        Returns:
            LLM extraction schema
        """
        ticker = article.get('stock', 'UNKNOWN')
        title = article.get('title', '')
        text = article.get('text', '')
        sentiment_score = article.get('sentiment_score', 0.0)
        sentiment_label = article.get('sentiment_label', 'neutral')
        confidence = article.get('confidence', 0.0)
        
        # Classify event
        event_type = self._classify_event_type(title, text, sentiment_label)
        event_subtype = self._determine_event_subtype(event_type, sentiment_score)
        
        # Determine bias and strength
        bias = self._determine_bias(sentiment_label, sentiment_score)
        bias_strength = self._calculate_bias_strength(sentiment_score, confidence)
        
        # Determine expected move
        move_bucket = self._determine_move_bucket(event_type, bias_strength, confidence)
        move_pct_low, move_pct_high = self._estimate_move_range(move_bucket)
        
        # Determine timing
        timing = self._determine_timing(event_type)
        
        # Determine IV reaction
        iv_reaction_post = self._determine_iv_reaction(event_type, bias)
        
        # Determine gap risk
        gap_risk = self._determine_gap_risk(event_type, move_bucket)
        
        # Determine realized vs implied
        realized_vs_implied = self._determine_realized_vs_implied(event_type, iv_reaction_post)
        
        # Calculate uncertainty
        uncertainty = self._calculate_uncertainty(confidence, event_type)
        
        # Identify key risks
        key_risks = self._identify_key_risks(event_type, iv_reaction_post, move_bucket)
        
        return {
            "ticker": ticker,
            "company_name": article.get('company_name', ticker),
            "news_timestamp": article.get('published_at', datetime.now().isoformat()),
            "source_name": article.get('source', 'unknown'),
            "source_trust": self._calculate_source_trust(article.get('source', '')),
            "event_type": event_type,
            "event_subtype": event_subtype,
            "freshness": self._determine_freshness(article),
            "novelty": self._determine_novelty(article),
            "bias": bias,
            "bias_strength": bias_strength,
            "direction_clarity": self._determine_direction_clarity(confidence, bias),
            "expected_spot_direction": self._map_bias_to_direction(bias),
            "expected_spot_move_bucket": move_bucket,
            "expected_spot_move_pct_low": move_pct_low,
            "expected_spot_move_pct_high": move_pct_high,
            "expected_move_timing": timing,
            "impact_persistence": self._determine_impact_persistence(event_type),
            "gap_risk": gap_risk,
            "iv_reaction_pre_event": IVReaction.NOT_APPLICABLE,
            "iv_reaction_post_event": iv_reaction_post,
            "realized_vs_implied_hint": realized_vs_implied,
            "uncertainty": uncertainty,
            "key_risks": key_risks,
            "reasoning": self._generate_reasoning(event_type, bias, iv_reaction_post, move_bucket)
        }
    
    def _classify_event_type(self, title: str, text: str, sentiment: str) -> str:
        """Classify event type from title and text"""
        content = (title + ' ' + text).lower()
        
        # Check each event type
        for event_type, keywords in self.event_keywords.items():
            if any(keyword in content for keyword in keywords):
                # Adjust for sentiment
                if 'earnings' in event_type:
                    return EventType.EARNINGS_BEAT if sentiment == 'positive' else EventType.EARNINGS_MISS
                elif 'guidance' in event_type:
                    return EventType.GUIDANCE_RAISE if sentiment == 'positive' else EventType.GUIDANCE_CUT
                else:
                    return getattr(EventType, event_type.upper(), EventType.ROUTINE_FILING)
        
        # Default based on sentiment
        if sentiment == 'positive':
            return EventType.MACRO_SECTOR_POSITIVE
        elif sentiment == 'negative':
            return EventType.MACRO_SECTOR_NEGATIVE
        else:
            return EventType.ROUTINE_FILING
    
    def _determine_event_subtype(self, event_type: str, sentiment_score: float) -> str:
        """Determine event subtype"""
        if event_type == EventType.EARNINGS_BEAT:
            if sentiment_score > 0.8:
                return "beat_and_guidance_raise"
            else:
                return "beat_only"
        elif event_type == EventType.EARNINGS_MISS:
            if sentiment_score < -0.8:
                return "miss_and_guidance_cut"
            else:
                return "miss_only"
        else:
            return "standard"
    
    def _determine_bias(self, sentiment_label: str, sentiment_score: float) -> str:
        """Determine directional bias"""
        if sentiment_label == 'positive':
            return Bias.BULLISH
        elif sentiment_label == 'negative':
            return Bias.BEARISH
        elif abs(sentiment_score) < 0.1:
            return Bias.NEUTRAL
        else:
            return Bias.MIXED
    
    def _calculate_bias_strength(self, sentiment_score: float, confidence: float) -> int:
        """Calculate bias strength (1-5)"""
        strength = abs(sentiment_score) * confidence * 5
        return max(1, min(5, int(strength)))
    
    def _determine_move_bucket(self, event_type: str, bias_strength: int, confidence: float) -> str:
        """Determine expected move bucket"""
        # High impact events
        if event_type in [EventType.FRAUD_OR_GOVERNANCE, EventType.REGULATORY_APPROVAL]:
            return MoveBucket.EXTREME if bias_strength >= 4 else MoveBucket.HIGH
        
        # Earnings events
        if 'earnings' in event_type.lower():
            if bias_strength >= 4 and confidence > 0.7:
                return MoveBucket.HIGH
            elif bias_strength >= 3:
                return MoveBucket.MEDIUM
            else:
                return MoveBucket.LOW
        
        # Guidance events
        if 'guidance' in event_type.lower():
            if bias_strength >= 4:
                return MoveBucket.HIGH
            else:
                return MoveBucket.MEDIUM
        
        # Low impact events
        if event_type in [EventType.ROUTINE_FILING, EventType.ANALYST_UPGRADE, EventType.ANALYST_DOWNGRADE]:
            return MoveBucket.LOW if bias_strength >= 3 else MoveBucket.VERY_LOW
        
        # Default
        if bias_strength >= 4:
            return MoveBucket.MEDIUM
        elif bias_strength >= 2:
            return MoveBucket.LOW
        else:
            return MoveBucket.VERY_LOW
    
    def _estimate_move_range(self, move_bucket: str) -> tuple:
        """Estimate move percentage range"""
        ranges = MOVE_BUCKET_RANGES.get(MoveBucket(move_bucket), (0.0, 1.0))
        return ranges
    
    def _determine_timing(self, event_type: str) -> str:
        """Determine expected move timing"""
        if event_type in [EventType.EARNINGS_BEAT, EventType.EARNINGS_MISS, EventType.FRAUD_OR_GOVERNANCE]:
            return Timing.SAME_DAY
        elif event_type in [EventType.REGULATORY_APPROVAL, EventType.LARGE_ORDER_WIN]:
            return Timing.NEXT_DAY
        elif event_type in [EventType.GUIDANCE_RAISE, EventType.GUIDANCE_CUT]:
            return Timing.NEXT_1_2_SESSIONS
        elif event_type in [EventType.ANALYST_UPGRADE, EventType.ANALYST_DOWNGRADE]:
            return Timing.NEXT_WEEK
        else:
            return Timing.UNKNOWN
    
    def _determine_iv_reaction(self, event_type: str, bias: str) -> str:
        """Determine post-event IV reaction"""
        # Earnings typically see IV crush
        if 'earnings' in event_type.lower():
            return IVReaction.MODERATE_DECREASE
        
        # High uncertainty events see IV expansion
        if event_type in [EventType.FRAUD_OR_GOVERNANCE, EventType.REGULATORY_ACTION]:
            return IVReaction.STRONG_INCREASE
        
        # Regulatory approval
        if event_type == EventType.REGULATORY_APPROVAL:
            return IVReaction.MODERATE_INCREASE
        
        # Guidance events
        if 'guidance' in event_type.lower():
            return IVReaction.MILD_INCREASE if bias == Bias.BEARISH else IVReaction.FLAT
        
        # Low impact events
        if event_type in [EventType.ROUTINE_FILING]:
            return IVReaction.FLAT
        
        # Default
        return IVReaction.MILD_INCREASE
    
    def _determine_gap_risk(self, event_type: str, move_bucket: str) -> str:
        """Determine gap risk"""
        if event_type in [EventType.FRAUD_OR_GOVERNANCE, EventType.REGULATORY_APPROVAL]:
            return GapRisk.EXTREME
        elif event_type in [EventType.EARNINGS_BEAT, EventType.EARNINGS_MISS] and move_bucket in [MoveBucket.HIGH, MoveBucket.EXTREME]:
            return GapRisk.HIGH
        elif move_bucket in [MoveBucket.MEDIUM, MoveBucket.HIGH]:
            return GapRisk.MEDIUM
        else:
            return GapRisk.LOW
    
    def _determine_realized_vs_implied(self, event_type: str, iv_reaction: str) -> str:
        """Determine realized vs implied volatility hint"""
        if 'earnings' in event_type.lower():
            return RealizedVsImplied.BELOW_IMPLIED
        elif iv_reaction in [IVReaction.STRONG_INCREASE, IVReaction.MODERATE_INCREASE]:
            return RealizedVsImplied.ABOVE_IMPLIED
        else:
            return RealizedVsImplied.NEAR_IMPLIED
    
    def _calculate_uncertainty(self, confidence: float, event_type: str) -> str:
        """Calculate uncertainty level"""
        if event_type in [EventType.RUMOR_UNVERIFIED, EventType.DEMERGER_RESTRUCTURING]:
            return Uncertainty.VERY_HIGH
        elif confidence < 0.5:
            return Uncertainty.HIGH
        elif confidence < 0.7:
            return Uncertainty.MODERATE
        else:
            return Uncertainty.LOW
    
    def _identify_key_risks(self, event_type: str, iv_reaction: str, move_bucket: str) -> List[str]:
        """Identify key risks"""
        risks = []
        
        if 'decrease' in iv_reaction:
            risks.append('iv_crush')
        
        if move_bucket in [MoveBucket.LOW, MoveBucket.VERY_LOW]:
            risks.append('priced_in_move')
        
        if event_type in [EventType.RUMOR_UNVERIFIED]:
            risks.append('rumor_risk')
        
        if move_bucket in [MoveBucket.HIGH, MoveBucket.EXTREME]:
            risks.append('gap_risk')
        
        return risks if risks else ['standard_risk']
    
    def _determine_freshness(self, article: Dict[str, Any]) -> str:
        """Determine news freshness"""
        published_at = article.get('published_at')
        if not published_at:
            return Freshness.RECENT
        
        try:
            pub_time = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            age = datetime.now() - pub_time.replace(tzinfo=None)
            
            if age < timedelta(hours=1):
                return Freshness.BREAKING
            elif age < timedelta(hours=24):
                return Freshness.RECENT
            else:
                return Freshness.STALE
        except:
            return Freshness.RECENT
    
    def _determine_novelty(self, article: Dict[str, Any]) -> str:
        """Determine information novelty"""
        # Simple heuristic - can be enhanced with duplicate detection
        return Novelty.NEW_INFORMATION
    
    def _determine_direction_clarity(self, confidence: float, bias: str) -> str:
        """Determine direction clarity"""
        if bias in [Bias.BINARY, Bias.MIXED]:
            return DirectionClarity.UNCLEAR
        elif confidence > 0.7:
            return DirectionClarity.CLEAR
        else:
            return DirectionClarity.MODERATE
    
    def _map_bias_to_direction(self, bias: str) -> str:
        """Map bias to spot direction"""
        if bias == Bias.BULLISH:
            return "up"
        elif bias == Bias.BEARISH:
            return "down"
        elif bias == Bias.BINARY:
            return "binary"
        else:
            return "flat"
    
    def _determine_impact_persistence(self, event_type: str) -> str:
        """Determine impact persistence"""
        if event_type in [EventType.FRAUD_OR_GOVERNANCE, EventType.REGULATORY_ACTION]:
            return ImpactPersistence.LONG_TERM
        elif event_type in [EventType.GUIDANCE_RAISE, EventType.GUIDANCE_CUT]:
            return ImpactPersistence.MEDIUM_TERM
        elif event_type in [EventType.EARNINGS_BEAT, EventType.EARNINGS_MISS]:
            return ImpactPersistence.SHORT_TERM_PERSISTENT
        else:
            return ImpactPersistence.INTRADAY
    
    def _calculate_source_trust(self, source: str) -> float:
        """Calculate source trust score"""
        trusted_sources = {
            'exchange_filing': 0.95,
            'bloomberg': 0.90,
            'reuters': 0.90,
            'cnbc': 0.85,
            'economic_times': 0.85,
            'moneycontrol': 0.80
        }
        
        source_lower = source.lower()
        for trusted, score in trusted_sources.items():
            if trusted in source_lower:
                return score
        
        return 0.70  # Default trust
    
    def _generate_reasoning(self, event_type: str, bias: str, iv_reaction: str, move_bucket: str) -> str:
        """Generate reasoning for the analysis"""
        direction = "bullish" if bias == Bias.BULLISH else ("bearish" if bias == Bias.BEARISH else "neutral")
        iv_direction = "compress" if 'decrease' in iv_reaction else ("expand" if 'increase' in iv_reaction else "remain stable")
        
        return f"{event_type.replace('_', ' ').title()} is directionally {direction} with {move_bucket.replace('_', ' ')} expected move. Post-event IV may {iv_direction}."


# Made with Bob