"""
Scoring models for options analysis
Provides quantitative scores for different aspects of options trading
"""

from typing import Dict, Any
from services.options_enums import Bias, MoveBucket, Uncertainty, Freshness, DirectionClarity


class OptionsScoring:
    """Calculate various scores for options trading decisions"""
    
    @staticmethod
    def calculate_spot_direction_score(llm_extraction: Dict[str, Any]) -> float:
        """
        Calculate spot direction score (-5 to +5)
        
        Args:
            llm_extraction: LLM extraction output
            
        Returns:
            Score from -5 (strong bearish) to +5 (strong bullish)
        """
        bias = llm_extraction['bias']
        bias_strength = llm_extraction['bias_strength']
        direction_clarity = llm_extraction['direction_clarity']
        source_trust = llm_extraction['source_trust']
        freshness = llm_extraction['freshness']
        
        # Base score from bias and strength
        if bias == Bias.BULLISH:
            base_score = bias_strength
        elif bias == Bias.BEARISH:
            base_score = -bias_strength
        else:
            base_score = 0
        
        # Adjust for clarity
        if direction_clarity == DirectionClarity.CLEAR:
            clarity_multiplier = 1.0
        elif direction_clarity == DirectionClarity.MODERATE:
            clarity_multiplier = 0.7
        else:
            clarity_multiplier = 0.4
        
        # Adjust for source trust
        trust_multiplier = 0.5 + (source_trust * 0.5)
        
        # Adjust for freshness
        if freshness == Freshness.BREAKING:
            freshness_multiplier = 1.0
        elif freshness == Freshness.RECENT:
            freshness_multiplier = 0.8
        else:
            freshness_multiplier = 0.5
        
        final_score = base_score * clarity_multiplier * trust_multiplier * freshness_multiplier
        
        return max(-5.0, min(5.0, final_score))
    
    @staticmethod
    def calculate_volatility_score(llm_extraction: Dict[str, Any]) -> float:
        """
        Calculate volatility score (-5 to +5)
        Positive = IV expansion likely, Negative = IV compression likely
        
        Args:
            llm_extraction: LLM extraction output
            
        Returns:
            Score from -5 (strong compression) to +5 (strong expansion)
        """
        iv_reaction = llm_extraction['iv_reaction_post_event']
        event_type = llm_extraction['event_type']
        
        # Map IV reaction to score
        iv_score_map = {
            'strong_increase': 5,
            'moderate_increase': 3,
            'mild_increase': 1,
            'flat': 0,
            'mild_decrease': -1,
            'moderate_decrease': -3,
            'strong_decrease': -5,
            'not_applicable': 0
        }
        
        base_score = iv_score_map.get(iv_reaction, 0)
        
        # Adjust for event type
        high_vol_events = ['fraud_or_governance', 'regulatory_action', 'demerger_restructuring']
        low_vol_events = ['routine_filing', 'analyst_upgrade', 'analyst_downgrade']
        
        if any(evt in event_type for evt in high_vol_events):
            base_score = max(base_score, 3)
        elif any(evt in event_type for evt in low_vol_events):
            base_score = min(base_score, -1)
        
        return float(base_score)
    
    @staticmethod
    def calculate_tradability_score(llm_extraction: Dict[str, Any]) -> float:
        """
        Calculate tradability score (0 to 10)
        Higher = more tradable
        
        Args:
            llm_extraction: LLM extraction output
            
        Returns:
            Score from 0 (avoid) to 10 (highly tradable)
        """
        source_trust = llm_extraction['source_trust']
        novelty = llm_extraction['novelty']
        direction_clarity = llm_extraction['direction_clarity']
        uncertainty = llm_extraction['uncertainty']
        freshness = llm_extraction['freshness']
        move_bucket = llm_extraction['expected_spot_move_bucket']
        
        # Start with source trust (0-10 scale)
        score = source_trust * 10
        
        # Adjust for novelty
        if novelty == 'new_information':
            score += 1
        elif novelty == 'rumor':
            score -= 3
        elif novelty == 'already_known':
            score -= 2
        
        # Adjust for clarity
        if direction_clarity == DirectionClarity.CLEAR:
            score += 2
        elif direction_clarity == DirectionClarity.UNCLEAR:
            score -= 2
        
        # Adjust for uncertainty
        if uncertainty == Uncertainty.LOW:
            score += 1
        elif uncertainty == Uncertainty.HIGH:
            score -= 2
        elif uncertainty == Uncertainty.VERY_HIGH:
            score -= 4
        
        # Adjust for freshness
        if freshness == Freshness.BREAKING:
            score += 1
        elif freshness == Freshness.STALE:
            score -= 3
        
        # Adjust for move size (very low moves are less tradable)
        if move_bucket == MoveBucket.VERY_LOW:
            score -= 2
        elif move_bucket in [MoveBucket.MEDIUM, MoveBucket.HIGH]:
            score += 1
        
        return max(0.0, min(10.0, score))
    
    @staticmethod
    def calculate_premium_edge_score(llm_extraction: Dict[str, Any]) -> float:
        """
        Calculate premium edge score (-5 to +5)
        Positive = good for buying premium, Negative = good for selling premium
        
        Args:
            llm_extraction: LLM extraction output
            
        Returns:
            Score from -5 (sell premium) to +5 (buy premium)
        """
        move_bucket = llm_extraction['expected_spot_move_bucket']
        iv_reaction = llm_extraction['iv_reaction_post_event']
        realized_vs_implied = llm_extraction['realized_vs_implied_hint']
        direction_clarity = llm_extraction['direction_clarity']
        
        # Base score from expected move vs IV reaction
        if 'increase' in iv_reaction and move_bucket in [MoveBucket.MEDIUM, MoveBucket.HIGH, MoveBucket.EXTREME]:
            base_score = 3  # Good for buying premium
        elif 'decrease' in iv_reaction and move_bucket in [MoveBucket.LOW, MoveBucket.VERY_LOW]:
            base_score = -3  # Good for selling premium
        elif move_bucket in [MoveBucket.HIGH, MoveBucket.EXTREME]:
            base_score = 2  # Large move expected
        elif move_bucket == MoveBucket.VERY_LOW:
            base_score = -2  # Small move expected
        else:
            base_score = 0
        
        # Adjust for realized vs implied
        if realized_vs_implied == 'above_implied':
            base_score += 2
        elif realized_vs_implied == 'below_implied':
            base_score -= 2
        
        # Adjust for clarity
        if direction_clarity == DirectionClarity.CLEAR:
            base_score += 1
        elif direction_clarity == DirectionClarity.UNCLEAR:
            base_score -= 1
        
        return max(-5.0, min(5.0, float(base_score)))
    
    @staticmethod
    def calculate_all_scores(llm_extraction: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate all scores
        
        Args:
            llm_extraction: LLM extraction output
            
        Returns:
            Dictionary with all scores
        """
        return {
            'spot_direction_score': OptionsScoring.calculate_spot_direction_score(llm_extraction),
            'volatility_score': OptionsScoring.calculate_volatility_score(llm_extraction),
            'tradability_score': OptionsScoring.calculate_tradability_score(llm_extraction),
            'premium_edge_score': OptionsScoring.calculate_premium_edge_score(llm_extraction)
        }
    
    @staticmethod
    def interpret_scores(scores: Dict[str, float]) -> Dict[str, str]:
        """
        Provide human-readable interpretations of scores
        
        Args:
            scores: Dictionary of scores
            
        Returns:
            Dictionary of interpretations
        """
        spot_score = scores['spot_direction_score']
        vol_score = scores['volatility_score']
        trade_score = scores['tradability_score']
        premium_score = scores['premium_edge_score']
        
        # Spot direction interpretation
        if spot_score >= 4:
            spot_interp = "Strong bullish"
        elif spot_score >= 2:
            spot_interp = "Moderate bullish"
        elif spot_score <= -4:
            spot_interp = "Strong bearish"
        elif spot_score <= -2:
            spot_interp = "Moderate bearish"
        else:
            spot_interp = "Neutral/Mixed"
        
        # Volatility interpretation
        if vol_score >= 3:
            vol_interp = "Strong IV expansion expected"
        elif vol_score >= 1:
            vol_interp = "Mild IV expansion expected"
        elif vol_score <= -3:
            vol_interp = "Strong IV compression expected"
        elif vol_score <= -1:
            vol_interp = "Mild IV compression expected"
        else:
            vol_interp = "IV likely flat"
        
        # Tradability interpretation
        if trade_score >= 8:
            trade_interp = "Highly tradable"
        elif trade_score >= 5:
            trade_interp = "Tradable with defined risk"
        elif trade_score >= 3:
            trade_interp = "Watch only"
        else:
            trade_interp = "Avoid trading"
        
        # Premium edge interpretation
        if premium_score >= 3:
            premium_interp = "Strong edge for buying premium"
        elif premium_score >= 1:
            premium_interp = "Slight edge for buying premium"
        elif premium_score <= -3:
            premium_interp = "Strong edge for selling premium"
        elif premium_score <= -1:
            premium_interp = "Slight edge for selling premium"
        else:
            premium_interp = "No clear premium edge"
        
        return {
            'spot_direction': spot_interp,
            'volatility': vol_interp,
            'tradability': trade_interp,
            'premium_edge': premium_interp
        }


# Made with Bob