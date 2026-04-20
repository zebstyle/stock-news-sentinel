"""
Deterministic rules engine for options implications
Translates LLM extraction into concrete options strategies
"""

from typing import Dict, Any, List, Tuple
from services.options_enums import (
    EventType, Bias, MoveBucket, IVReaction, GapRisk,
    StrategyFamily
)


class OptionsRulesEngine:
    """Deterministic rules engine for options strategy recommendations"""
    
    def __init__(self):
        """Initialize rules engine with event-to-options mappings"""
        self._init_event_mappings()
    
    def _init_event_mappings(self):
        """Initialize event type to options characteristics mapping"""
        self.event_mappings = {
            # Bullish directional events
            EventType.EARNINGS_BEAT: {
                'typical_spot': 'up',
                'typical_iv': IVReaction.MODERATE_DECREASE,
                'preferred_strategies': ['bull_call_spread', 'itm_call_buy', 'short_put'],
                'avoid_strategies': ['otm_weekly_call_buy'],
                'notes': 'IV crush risk makes spreads better than naked calls'
            },
            EventType.GUIDANCE_RAISE: {
                'typical_spot': 'up',
                'typical_iv': IVReaction.MILD_INCREASE,
                'preferred_strategies': ['long_call', 'bull_call_spread'],
                'avoid_strategies': ['bearish_credit_spreads'],
                'notes': 'Clean bullish setup with moderate IV'
            },
            EventType.LARGE_ORDER_WIN: {
                'typical_spot': 'up',
                'typical_iv': IVReaction.MILD_INCREASE,
                'preferred_strategies': ['long_call', 'bull_call_spread'],
                'avoid_strategies': ['long_put'],
                'notes': 'Usually cleaner than earnings moves'
            },
            EventType.REGULATORY_APPROVAL: {
                'typical_spot': 'up',
                'typical_iv': IVReaction.STRONG_INCREASE,
                'preferred_strategies': ['long_call', 'call_spread'],
                'avoid_strategies': ['short_call'],
                'notes': 'Strong bullish catalyst with vol expansion'
            },
            EventType.PROMOTER_BUYING: {
                'typical_spot': 'up',
                'typical_iv': IVReaction.FLAT,
                'preferred_strategies': ['call_spread', 'short_put'],
                'avoid_strategies': ['short_delta_bets'],
                'notes': 'Gradual bullish repricing'
            },
            
            # Bearish directional events
            EventType.EARNINGS_MISS: {
                'typical_spot': 'down',
                'typical_iv': IVReaction.MODERATE_DECREASE,
                'preferred_strategies': ['bear_put_spread', 'itm_put'],
                'avoid_strategies': ['cheap_far_otm_puts'],
                'notes': 'IV crush despite bearish move'
            },
            EventType.GUIDANCE_CUT: {
                'typical_spot': 'down',
                'typical_iv': IVReaction.MODERATE_INCREASE,
                'preferred_strategies': ['long_put', 'bear_put_spread'],
                'avoid_strategies': ['bullish_premium_selling'],
                'notes': 'Strong bearish signal'
            },
            EventType.REGULATORY_ACTION: {
                'typical_spot': 'down',
                'typical_iv': IVReaction.STRONG_INCREASE,
                'preferred_strategies': ['long_put', 'put_spread'],
                'avoid_strategies': ['naked_short_puts'],
                'notes': 'High uncertainty drives vol expansion'
            },
            EventType.FRAUD_OR_GOVERNANCE: {
                'typical_spot': 'down',
                'typical_iv': IVReaction.STRONG_INCREASE,
                'preferred_strategies': ['long_put', 'put_backspread', 'long_strangle'],
                'avoid_strategies': ['short_vol'],
                'notes': 'Extreme bearish with vol explosion'
            },
            EventType.MANAGEMENT_EXIT: {
                'typical_spot': 'down',
                'typical_iv': IVReaction.MODERATE_INCREASE,
                'preferred_strategies': ['bear_spread'],
                'avoid_strategies': ['naked_calls'],
                'notes': 'Moderate bearish impact'
            },
            
            # Binary/uncertain events
            EventType.DEMERGER_RESTRUCTURING: {
                'typical_spot': 'binary',
                'typical_iv': IVReaction.STRONG_INCREASE,
                'preferred_strategies': ['long_straddle', 'long_strangle'],
                'avoid_strategies': ['single_leg_directional'],
                'notes': 'High uncertainty, both sides expensive'
            },
            EventType.RUMOR_UNVERIFIED: {
                'typical_spot': 'erratic',
                'typical_iv': IVReaction.MODERATE_INCREASE,
                'preferred_strategies': ['small_defined_risk_only'],
                'avoid_strategies': ['aggressive_short_premium'],
                'notes': 'Junky premium behavior, avoid or use small size'
            },
            
            # Low impact events
            EventType.ROUTINE_FILING: {
                'typical_spot': 'flat',
                'typical_iv': IVReaction.FLAT,
                'preferred_strategies': ['iron_condor', 'credit_spreads', 'no_trade'],
                'avoid_strategies': ['buying_premium'],
                'notes': 'Premium decay environment'
            },
            EventType.ANALYST_UPGRADE: {
                'typical_spot': 'mild_up',
                'typical_iv': IVReaction.MILD_INCREASE,
                'preferred_strategies': ['call_spread'],
                'avoid_strategies': ['large_long_vol'],
                'notes': 'Moderate bullish, limited move'
            },
            EventType.ANALYST_DOWNGRADE: {
                'typical_spot': 'mild_down',
                'typical_iv': IVReaction.MILD_INCREASE,
                'preferred_strategies': ['put_spread'],
                'avoid_strategies': ['large_long_vol'],
                'notes': 'Moderate bearish, limited move'
            },
            EventType.CAPEX_EXPANSION: {
                'typical_spot': 'mixed',
                'typical_iv': IVReaction.MILD_INCREASE,
                'preferred_strategies': ['defined_risk_directional_only'],
                'avoid_strategies': ['oversized_single_leg_bets'],
                'notes': 'Interpretation dependent'
            }
        }
    
    def calculate_premium_impact(
        self,
        bias: str,
        iv_direction: str,
        move_bucket: str
    ) -> Dict[str, str]:
        """
        Calculate premium impact for different option types
        
        Args:
            bias: Directional bias (bullish/bearish/neutral/binary)
            iv_direction: IV direction (up/down/flat)
            move_bucket: Expected move size
            
        Returns:
            Premium impact for each option type
        """
        # Scenario A: bullish + IV up
        if bias == Bias.BULLISH and iv_direction in ['strong_increase', 'moderate_increase']:
            return {
                'atm_calls': 'strong_gain',
                'otm_calls': 'very_strong_gain',
                'itm_calls': 'moderate_gain',
                'atm_puts': 'flat_to_mild_loss',
                'otm_puts': 'loss_but_slower_if_iv_high',
                'itm_puts': 'strong_loss'
            }
        
        # Scenario B: bullish + IV down
        elif bias == Bias.BULLISH and iv_direction in ['moderate_decrease', 'mild_decrease', 'strong_decrease']:
            return {
                'atm_calls': 'modest_gain_unless_strong_spot_move',
                'otm_calls': 'can_disappoint_badly',
                'itm_calls': 'best_among_long_calls',
                'atm_puts': 'strong_decay',
                'otm_puts': 'strong_decay',
                'itm_puts': 'strong_loss'
            }
        
        # Scenario C: bearish + IV up
        elif bias == Bias.BEARISH and iv_direction in ['strong_increase', 'moderate_increase']:
            return {
                'atm_calls': 'can_remain_elevated_briefly',
                'otm_calls': 'directional_drag_dominates',
                'itm_calls': 'strong_loss',
                'atm_puts': 'strong_gain',
                'otm_puts': 'very_strong_gain',
                'itm_puts': 'moderate_to_strong_gain'
            }
        
        # Scenario D: bearish + IV down
        elif bias == Bias.BEARISH and iv_direction in ['moderate_decrease', 'mild_decrease']:
            return {
                'atm_calls': 'decay_sharply',
                'otm_calls': 'strong_decay',
                'itm_calls': 'strong_loss',
                'atm_puts': 'gains_only_if_move_large_enough',
                'otm_puts': 'can_fail_if_move_not_big',
                'itm_puts': 'cleaner_exposure'
            }
        
        # Scenario E: binary + IV very high
        elif bias == Bias.BINARY:
            return {
                'atm_calls': 'expensive',
                'otm_calls': 'expensive',
                'itm_calls': 'expensive',
                'atm_puts': 'expensive',
                'otm_puts': 'expensive',
                'itm_puts': 'expensive'
            }
        
        # Default neutral scenario
        else:
            return {
                'atm_calls': 'neutral',
                'otm_calls': 'neutral',
                'itm_calls': 'neutral',
                'atm_puts': 'neutral',
                'otm_puts': 'neutral',
                'itm_puts': 'neutral'
            }
    
    def select_strategy_family(
        self,
        bias: str,
        direction_clarity: str,
        move_bucket: str,
        iv_reaction: str,
        uncertainty: str,
        freshness: str
    ) -> Tuple[str, List[str], List[str], str]:
        """
        Select appropriate strategy family
        
        Returns:
            Tuple of (family, preferred_strategies, avoid_strategies, reasoning)
        """
        # Avoid family for stale/weak signals
        if freshness == 'stale' or uncertainty == 'very_high':
            return (
                StrategyFamily.AVOID,
                ['no_trade'],
                ['any_premium_buying'],
                'Stale news or very high uncertainty makes trading unattractive'
            )
        
        # Binary events
        if bias == Bias.BINARY:
            if move_bucket in ['high', 'extreme']:
                return (
                    StrategyFamily.LONG_VOLATILITY,
                    ['long_straddle', 'long_strangle'],
                    ['single_leg_directional'],
                    'Binary event with large expected move favors long vol'
                )
            else:
                return (
                    StrategyFamily.SHORT_VOLATILITY,
                    ['iron_condor', 'short_strangle_small'],
                    ['long_premium'],
                    'Binary event but small expected move, implied likely rich'
                )
        
        # Clear bullish direction
        if bias == Bias.BULLISH and direction_clarity in ['clear', 'moderate']:
            if iv_reaction in ['moderate_decrease', 'strong_decrease']:
                return (
                    StrategyFamily.DEFINED_RISK_BULLISH,
                    ['bull_call_spread', 'short_put', 'itm_call_buy'],
                    ['otm_weekly_call_buy'],
                    'Bullish direction clear but IV crush risk makes spreads better'
                )
            else:
                return (
                    StrategyFamily.DIRECTIONAL_LONG_PREMIUM,
                    ['long_call', 'itm_call_buy'],
                    ['bearish_strategies'],
                    'Clear bullish direction with manageable IV'
                )
        
        # Clear bearish direction
        if bias == Bias.BEARISH and direction_clarity in ['clear', 'moderate']:
            if iv_reaction in ['strong_increase', 'moderate_increase']:
                return (
                    StrategyFamily.DEFINED_RISK_BEARISH,
                    ['bear_put_spread', 'long_put'],
                    ['short_put', 'short_strangle'],
                    'Bearish move with vol expansion'
                )
            else:
                return (
                    StrategyFamily.DEFINED_RISK_BEARISH,
                    ['bear_put_spread', 'itm_put', 'call_credit_spread'],
                    ['far_otm_puts'],
                    'Bearish direction but IV not expanding much'
                )
        
        # Low impact / neutral
        if move_bucket in ['very_low', 'low'] or bias == Bias.NEUTRAL:
            return (
                StrategyFamily.SHORT_VOLATILITY,
                ['iron_condor', 'credit_spreads', 'no_trade'],
                ['long_premium'],
                'Low expected impact favors premium decay strategies or no trade'
            )
        
        # Default to no trade for unclear situations
        return (
            StrategyFamily.NO_TRADE,
            ['wait_for_clarity'],
            ['aggressive_positions'],
            'Unclear setup, better to wait'
        )

    def apply_rules(self, llm_extraction: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply deterministic rules to LLM extraction
        
        Args:
            llm_extraction: Output from LLM extraction layer
            market_data: Enriched market data layer
            
        Returns:
            Complete options impact analysis
        """
        ticker = llm_extraction['ticker']
        bias = llm_extraction['bias']
        move_bucket = llm_extraction['expected_spot_move_bucket']
        iv_reaction = llm_extraction['iv_reaction_post_event']
        direction_clarity = llm_extraction['direction_clarity']
        uncertainty = llm_extraction['uncertainty']
        freshness = llm_extraction['freshness']
        
        premium_impact = self.calculate_premium_impact(
            bias,
            iv_reaction,
            move_bucket
        )
        
        strategy_family, preferred, avoid, reasoning = self.select_strategy_family(
            bias,
            direction_clarity,
            move_bucket,
            iv_reaction,
            uncertainty,
            freshness
        )

        trade_setup = self._build_trade_setup(llm_extraction, market_data)
        consolidated_view = self._build_consolidated_view(
            llm_extraction=llm_extraction,
            market_data=market_data,
            strategy_family=strategy_family,
            preferred=preferred,
            avoid=avoid,
            reasoning=reasoning,
            trade_setup=trade_setup
        )
        
        option_view = {
            'spot_view': {
                'direction': llm_extraction['expected_spot_direction'],
                'expected_move_pct': f"{llm_extraction['expected_spot_move_pct_low']}-{llm_extraction['expected_spot_move_pct_high']}",
                'move_pct_range': f"{llm_extraction['expected_spot_move_pct_low']}-{llm_extraction['expected_spot_move_pct_high']}",
                'timing': llm_extraction['expected_move_timing']
            },
            'vol_view': {
                'iv_direction': 'down' if 'decrease' in iv_reaction else ('up' if 'increase' in iv_reaction else 'flat'),
                'iv_intensity': iv_reaction.replace('_', ' '),
                'gap_risk': llm_extraction['gap_risk'],
                'realized_vs_implied': llm_extraction['realized_vs_implied_hint']
            },
            'premium_impact': premium_impact,
            'trade_setup': trade_setup,
            'consolidated_view': consolidated_view,
            'strategy_preference': {
                'preferred': preferred,
                'acceptable': self._get_acceptable_strategies(strategy_family),
                'avoid': avoid,
                'best_trade_family': strategy_family
            },
            'confidence': self._calculate_confidence(llm_extraction),
            'summary': reasoning
        }
        
        return {
            'ticker': ticker,
            'option_view': option_view,
            'llm_extraction': llm_extraction,
            'market_data': market_data
        }
    
    def _build_trade_setup(self, llm_extraction: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build trade setup using deterministic entry/exit rules."""
        current_price = float(market_data.get('current_price', 0.0))
        bias = llm_extraction.get('bias')
        move_low = float(llm_extraction.get('expected_spot_move_pct_low', 0.0))
        move_high = float(llm_extraction.get('expected_spot_move_pct_high', 0.0))
        move_bucket = llm_extraction.get('expected_spot_move_bucket')

        if current_price <= 0:
            return {}

        if bias == Bias.BULLISH and move_bucket in [MoveBucket.MEDIUM, MoveBucket.HIGH, MoveBucket.EXTREME]:
            entry_low = current_price * 0.995
            entry_high = current_price * 1.01
            ideal_entry = current_price
            stop_loss = current_price * 0.98
            target_1 = current_price * (1 + (move_low / 100))
            target_2 = current_price * (1 + (move_high / 100))
            risk = max(ideal_entry - stop_loss, 0.01)
            reward = max(target_1 - ideal_entry, 0.01)

            return {
                'entry_price_range': f"{round(entry_low, 2)} - {round(entry_high, 2)}",
                'entry_range': f"{round(entry_low, 2)} - {round(entry_high, 2)}",
                'ideal_entry': round(ideal_entry, 2),
                'stop_loss': round(stop_loss, 2),
                'target_1': round(target_1, 2),
                'target_2': round(target_2, 2),
                'time_horizon': self._format_time_horizon(llm_extraction.get('expected_move_timing', 'unknown')),
                'risk_reward_ratio': f"1:{round(reward / risk, 1)}",
                'risk_reward': f"1:{round(reward / risk, 1)}"
            }

        if bias == Bias.BEARISH:
            entry_low = current_price * 0.99
            entry_high = current_price * 1.005
            ideal_entry = current_price
            stop_loss = current_price * 1.02
            target_1 = current_price * (1 - (move_low / 100))
            target_2 = current_price * (1 - (move_high / 100))
            risk = max(stop_loss - ideal_entry, 0.01)
            reward = max(ideal_entry - target_1, 0.01)

            return {
                'entry_price_range': f"{round(entry_low, 2)} - {round(entry_high, 2)}",
                'entry_range': f"{round(entry_low, 2)} - {round(entry_high, 2)}",
                'ideal_entry': round(ideal_entry, 2),
                'stop_loss': round(stop_loss, 2),
                'target_1': round(target_1, 2),
                'target_2': round(target_2, 2),
                'time_horizon': self._format_time_horizon(llm_extraction.get('expected_move_timing', 'unknown')),
                'risk_reward_ratio': f"1:{round(reward / risk, 1)}",
                'risk_reward': f"1:{round(reward / risk, 1)}"
            }

        if bias == Bias.BINARY:
            upper_breakout = round(current_price * (1 + (move_low / 100)), 2)
            lower_breakdown = round(current_price * (1 - (move_low / 100)), 2)
            return {
                'entry_price_range': 'no_directional_entry',
                'entry_range': 'no_directional_entry',
                'ideal_entry': None,
                'stop_loss': None,
                'target_1': upper_breakout,
                'target_2': lower_breakdown,
                'time_horizon': self._format_time_horizon(llm_extraction.get('expected_move_timing', 'unknown')),
                'risk_reward_ratio': 'not_applicable',
                'risk_reward': 'not_applicable',
                'upper_breakout': upper_breakout,
                'lower_breakdown': lower_breakdown
            }

        return {}

    def _build_consolidated_view(
        self,
        llm_extraction: Dict[str, Any],
        market_data: Dict[str, Any],
        strategy_family: str,
        preferred: List[str],
        avoid: List[str],
        reasoning: str,
        trade_setup: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert all signals into a single action output."""
        bias = llm_extraction.get('bias')
        tradability_proxy = self._calculate_tradability_proxy(llm_extraction)
        iv_reaction = llm_extraction.get('iv_reaction_post_event', '')
        volatility_context = market_data.get('volatility_context', 'moderate')

        if bias == Bias.BULLISH and tradability_proxy >= 8 and strategy_family == StrategyFamily.DIRECTIONAL_LONG_PREMIUM:
            action = 'BUY'
            conviction = 'HIGH'
        elif bias == Bias.BULLISH and tradability_proxy >= 5 and (
            strategy_family == StrategyFamily.DEFINED_RISK_BULLISH or 'decrease' in iv_reaction
        ):
            action = 'BUY_WITH_SPREAD'
            conviction = 'HIGH' if tradability_proxy >= 7 else 'MEDIUM'
        elif bias == Bias.BEARISH and tradability_proxy >= 5:
            action = 'SELL'
            conviction = 'HIGH' if tradability_proxy >= 7 else 'MEDIUM'
        elif bias == Bias.BINARY:
            action = 'WAIT'
            conviction = 'MEDIUM'
        elif tradability_proxy < 3:
            action = 'NO_TRADE'
            conviction = 'LOW'
        else:
            action = 'NO_TRADE'
            conviction = 'LOW'

        headline_map = {
            'BUY': 'Bullish directional setup with actionable entry',
            'BUY_WITH_SPREAD': 'Bullish setup with controlled risk; better via spreads than naked calls',
            'SELL': 'Bearish setup favors downside positioning with defined risk',
            'WAIT': 'Binary setup with high uncertainty; wait for breakout or use volatility structure',
            'NO_TRADE': 'Low-impact or unclear setup; capital better preserved'
        }

        what_to_do = self._build_what_to_do(action, preferred, trade_setup)
        what_to_avoid = ', '.join(avoid) if avoid else 'aggressive premium buying without edge'

        return {
            'headline': headline_map[action],
            'action': action,
            'conviction': conviction,
            'what_to_do': what_to_do,
            'what_to_avoid': what_to_avoid,
            'key_reason': f"{reasoning}; volatility context is {volatility_context}"
        }

    def _build_what_to_do(self, action: str, preferred: List[str], trade_setup: Dict[str, Any]) -> str:
        """Create execution-oriented recommendation text."""
        preferred_text = ', '.join(preferred[:2]) if preferred else 'defined-risk strategy'
        if action in ['BUY', 'BUY_WITH_SPREAD'] and trade_setup:
            return (
                f"Enter near {trade_setup.get('ideal_entry', trade_setup.get('entry_price_range'))} "
                f"with defined risk; prefer {preferred_text}"
            )
        if action == 'SELL' and trade_setup:
            return (
                f"Use bearish positioning near {trade_setup.get('ideal_entry', trade_setup.get('entry_price_range'))} "
                f"with disciplined stop at {trade_setup.get('stop_loss')}"
            )
        if action == 'WAIT' and trade_setup:
            return (
                f"Wait for upper breakout {trade_setup.get('upper_breakout')} or "
                f"lower breakdown {trade_setup.get('lower_breakdown')}"
            )
        return 'Stand aside until signal quality improves'

    def _calculate_tradability_proxy(self, llm_extraction: Dict[str, Any]) -> float:
        """Lightweight internal tradability proxy for action selection."""
        score = float(llm_extraction.get('source_trust', 0.5)) * 10
        if llm_extraction.get('direction_clarity') == 'clear':
            score += 2
        elif llm_extraction.get('direction_clarity') == 'unclear':
            score -= 2

        if llm_extraction.get('uncertainty') == 'low':
            score += 1
        elif llm_extraction.get('uncertainty') == 'high':
            score -= 2
        elif llm_extraction.get('uncertainty') == 'very_high':
            score -= 4

        if llm_extraction.get('freshness') == 'breaking':
            score += 1
        elif llm_extraction.get('freshness') == 'stale':
            score -= 3

        move_bucket = llm_extraction.get('expected_spot_move_bucket')
        if move_bucket == MoveBucket.VERY_LOW:
            score -= 2
        elif move_bucket in [MoveBucket.MEDIUM, MoveBucket.HIGH]:
            score += 1

        return max(0.0, min(10.0, score))
    
    def _get_acceptable_strategies(self, family: str) -> List[str]:
        """Get acceptable strategies for a family"""
        acceptable_map = {
            StrategyFamily.DIRECTIONAL_LONG_PREMIUM.value: ['bull_call_spread', 'bear_put_spread'],
            StrategyFamily.DEFINED_RISK_BULLISH.value: ['long_call'],
            StrategyFamily.DEFINED_RISK_BEARISH.value: ['long_put'],
            StrategyFamily.LONG_VOLATILITY.value: ['calendar_spread'],
            StrategyFamily.SHORT_VOLATILITY.value: ['calendar_spread'],
            StrategyFamily.NO_TRADE.value: [],
            StrategyFamily.AVOID.value: []
        }
        return acceptable_map.get(family, [])
    
    def _calculate_confidence(self, llm_extraction: Dict[str, Any]) -> float:
        """Calculate overall confidence score"""
        base_confidence = llm_extraction.get('source_trust', 0.5)
        
        # Adjust for clarity
        if llm_extraction['direction_clarity'] == 'clear':
            base_confidence += 0.2
        elif llm_extraction['direction_clarity'] == 'unclear':
            base_confidence -= 0.2
        
        # Adjust for uncertainty
        if llm_extraction['uncertainty'] == 'low':
            base_confidence += 0.1
        elif llm_extraction['uncertainty'] in ['high', 'very_high']:
            base_confidence -= 0.2
        
        # Adjust for freshness
        if llm_extraction['freshness'] == 'breaking':
            base_confidence += 0.1
        elif llm_extraction['freshness'] == 'stale':
            base_confidence -= 0.3
        
        return max(0.0, min(1.0, base_confidence))

    def _format_time_horizon(self, timing: str) -> str:
        """Map timing enum to user-facing time horizon string."""
        mapping = {
            'same_day': 'intraday',
            'next_day': 'next session',
            'next_1_2_sessions': '1-2 sessions',
            'next_week': 'next week',
            'multi_week': 'multi-week',
            'unknown': 'event-driven'
        }
        return mapping.get(timing, timing.replace('_', ' '))


# Made with Bob