"""
Standard enums for options analysis
"""

from enum import Enum


class EventType(str, Enum):
    """Standard event types"""
    EARNINGS_BEAT = "earnings_beat"
    EARNINGS_MISS = "earnings_miss"
    GUIDANCE_RAISE = "guidance_raise"
    GUIDANCE_CUT = "guidance_cut"
    LARGE_ORDER_WIN = "large_order_win"
    ORDER_LOSS_OR_CANCEL = "order_loss_or_cancel"
    REGULATORY_APPROVAL = "regulatory_approval"
    REGULATORY_ACTION = "regulatory_action"
    MANAGEMENT_EXIT = "management_exit"
    PROMOTER_BUYING = "promoter_buying"
    PROMOTER_SELLING = "promoter_selling"
    STAKE_SALE_OR_BLOCK_DEAL = "stake_sale_or_block_deal"
    DEBT_STRESS = "debt_stress"
    LITIGATION_POSITIVE = "litigation_positive"
    LITIGATION_NEGATIVE = "litigation_negative"
    MNA_POSITIVE = "mna_positive"
    MNA_NEGATIVE = "mna_negative"
    DEMERGER_RESTRUCTURING = "demerger_restructuring"
    CAPEX_EXPANSION = "capex_expansion"
    OPERATIONAL_DISRUPTION = "operational_disruption"
    FRAUD_OR_GOVERNANCE = "fraud_or_governance"
    MACRO_SECTOR_POSITIVE = "macro_sector_positive"
    MACRO_SECTOR_NEGATIVE = "macro_sector_negative"
    RUMOR_UNVERIFIED = "rumor_unverified"
    ROUTINE_FILING = "routine_filing"
    PRODUCT_LAUNCH_POSITIVE = "product_launch_positive"
    PRODUCT_ISSUE_NEGATIVE = "product_issue_negative"
    ANALYST_UPGRADE = "analyst_upgrade"
    ANALYST_DOWNGRADE = "analyst_downgrade"


class Bias(str, Enum):
    """Directional bias"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    MIXED = "mixed"
    BINARY = "binary"


class MoveBucket(str, Enum):
    """Expected move magnitude"""
    VERY_LOW = "very_low"  # <1%
    LOW = "low"  # 1-2%
    MEDIUM = "medium"  # 2-4%
    HIGH = "high"  # 4-7%
    EXTREME = "extreme"  # >7%


class Timing(str, Enum):
    """Expected move timing"""
    SAME_DAY = "same_day"
    NEXT_DAY = "next_day"
    NEXT_1_2_SESSIONS = "next_1_2_sessions"
    NEXT_WEEK = "next_week"
    MULTI_WEEK = "multi_week"
    UNKNOWN = "unknown"


class IVReaction(str, Enum):
    """Implied volatility reaction"""
    STRONG_INCREASE = "strong_increase"
    MODERATE_INCREASE = "moderate_increase"
    MILD_INCREASE = "mild_increase"
    FLAT = "flat"
    MILD_DECREASE = "mild_decrease"
    MODERATE_DECREASE = "moderate_decrease"
    STRONG_DECREASE = "strong_decrease"
    NOT_APPLICABLE = "not_applicable"


class RealizedVsImplied(str, Enum):
    """Realized vs implied volatility hint"""
    ABOVE_IMPLIED = "above_implied"
    NEAR_IMPLIED = "near_implied"
    BELOW_IMPLIED = "below_implied"
    UNKNOWN = "unknown"


class GapRisk(str, Enum):
    """Gap risk level"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class Freshness(str, Enum):
    """News freshness"""
    BREAKING = "breaking"
    RECENT = "recent"
    STALE = "stale"


class Novelty(str, Enum):
    """Information novelty"""
    NEW_INFORMATION = "new_information"
    ALREADY_KNOWN = "already_known"
    RUMOR = "rumor"


class DirectionClarity(str, Enum):
    """Direction clarity"""
    CLEAR = "clear"
    MODERATE = "moderate"
    UNCLEAR = "unclear"


class ImpactPersistence(str, Enum):
    """Impact persistence"""
    INTRADAY = "intraday"
    SHORT_TERM_PERSISTENT = "short_term_persistent"
    MEDIUM_TERM = "medium_term"
    LONG_TERM = "long_term"


class Uncertainty(str, Enum):
    """Uncertainty level"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class StrategyFamily(str, Enum):
    """Strategy family"""
    DIRECTIONAL_LONG_PREMIUM = "directional_long_premium"
    DEFINED_RISK_BULLISH = "defined_risk_bullish"
    DEFINED_RISK_BEARISH = "defined_risk_bearish"
    LONG_VOLATILITY = "long_volatility"
    SHORT_VOLATILITY = "short_volatility"
    NO_TRADE = "no_trade"
    AVOID = "avoid"


# Move bucket to percentage mapping
MOVE_BUCKET_RANGES = {
    MoveBucket.VERY_LOW: (0.0, 1.0),
    MoveBucket.LOW: (1.0, 2.0),
    MoveBucket.MEDIUM: (2.0, 4.0),
    MoveBucket.HIGH: (4.0, 7.0),
    MoveBucket.EXTREME: (7.0, 15.0)
}


# Made with Bob