# Options Analysis Module - Documentation

## Overview

The Options Analysis module analyzes news events and produces decision-ready trading outputs with a strict separation of concerns:

1. **LLM Extraction Layer**: classification only
2. **Market Data Enrichment Layer**: current spot context
3. **Deterministic Rules Engine**: strategy, trade levels, and final action
4. **Scoring Layer**: quantitative tradability and volatility signals
5. **Consolidation Layer**: final action-oriented summary

This preserves the core design principle:

- **LLM → classification only**
- **Rules engine → trading decisions + price levels**

## Updated Architecture

```text
Stage A: Input
    Ticker + news

Stage B: LLM Classification
    Event, bias, move, IV

Stage C: Market Data Fetch / Enrichment
    Current price
    Last updated
    Day change
    Volatility context

Stage D: Rules Engine
    Spot view
    Vol view
    Strategy view
    Entry / exit levels

Stage E: Consolidation Layer
    Final action
    Trade plan
    Summary
```

## Output Layers

### 1. Market Data Layer

```json
{
  "market_data": {
    "current_price": 2850.50,
    "last_updated": "2026-04-16T10:32:00+05:30",
    "day_change_pct": 1.2,
    "volatility_context": "moderate"
  }
}
```

Purpose:
- make the analysis actionable in current market context
- support entry, stop-loss, and target calculations
- keep output production-friendly even if news classification is unchanged

### 2. Trade Setup Layer

```json
{
  "trade_setup": {
    "entry_price_range": "2820 - 2860",
    "ideal_entry": 2840,
    "stop_loss": 2775,
    "target_1": 2920,
    "target_2": 2980,
    "time_horizon": "1-2 sessions",
    "risk_reward_ratio": "1:2.3"
  }
}
```

Purpose:
- convert directional view into execution-ready levels
- avoid vague analysis without a plan
- enforce deterministic price logic outside the LLM

### 3. Consolidated Analysis Layer

```json
{
  "consolidated_view": {
    "headline": "Bullish setup with controlled risk; better via spreads than naked calls",
    "action": "BUY_WITH_SPREAD",
    "conviction": "HIGH",
    "what_to_do": "Enter near 2840 with defined risk; prefer bull call spread over naked calls",
    "what_to_avoid": "OTM weekly call buying due to IV crush risk",
    "key_reason": "Bullish momentum + moderate IV compression reduces upside from pure premium buying"
  }
}
```

Purpose:
- merge classification, market data, and strategy logic into one decision
- provide clean downstream action for UI, APIs, or alerts
- reduce ambiguity between bullish analysis and tradable setups

## Full Final Output

```json
{
  "ticker": "RELIANCE",
  "market_data": {
    "current_price": 2850.50
  },
  "headline_assessment": "Bullish but not ideal for naked call buying",
  "spot_forecast": {
    "direction": "up",
    "expected_move_pct": "2-4",
    "timing": "next_1_2_sessions"
  },
  "trade_setup": {
    "entry_price_range": "2820 - 2860",
    "stop_loss": 2775,
    "target_1": 2920,
    "target_2": 2980
  },
  "strategy_view": {
    "best_family": "defined_risk_bullish",
    "preferred": ["bull_call_spread", "short_put"],
    "avoid": ["otm_weekly_call_buy"]
  },
  "consolidated_view": {
    "action": "BUY_WITH_SPREAD",
    "conviction": "HIGH"
  },
  "scores": {
    "spot_direction_score": 4,
    "volatility_score": -1,
    "tradability_score": 8,
    "premium_edge_score": 1
  }
}
```

## Rule Logic

### Bullish Case

If:
- `bias = bullish`
- `move >= medium`

Then:
- `Entry = current_price * (0.995 to 1.01)`
- `Stop Loss = current_price * (0.97 to 0.985)`
- `Target 1 = current_price * (1 + move_low%)`
- `Target 2 = current_price * (1 + move_high%)`

Implementation notes:
- entry range is near current price with a small 0.5% to 1% buffer
- stop loss is placed below price to respect support / expected move failure
- target 1 uses lower expected move bound
- target 2 uses upper expected move bound

### Bearish Case

Then:
- entry remains near current price
- stop loss is placed above price, approximately 2%
- targets are derived from the expected downside move range

### Binary Case

Then:
- no directional entry
- provide only:
  - upper breakout
  - lower breakdown

## Consolidated Decision Engine

Signals are translated into a single action:

| Condition | Action |
|---|---|
| Strong bullish + good tradability | BUY |
| Bullish but IV risk | BUY_WITH_SPREAD |
| Bearish strong | SELL |
| Binary high uncertainty | WAIT |
| Low impact / poor setup | NO_TRADE |

### Action Meanings

- **BUY**: directional bullish setup is acceptable outright
- **BUY_WITH_SPREAD**: bullish thesis exists, but IV or event risk favors defined-risk structures
- **SELL**: bearish setup with actionable downside positioning
- **WAIT**: binary event or insufficient clarity
- **NO_TRADE**: signal quality too weak or stale

## Current Implementation Notes

### Market Data Enrichment

The analyzer currently supports:
1. direct article-attached prices:
   - `current_price`
   - `market_price`
   - `ltp`
   - `price`
2. deterministic fallback price generation when no live price is attached

This keeps the architecture ready for real market API integration while preserving a working pipeline today.

### Spot View

The rules engine now emits:

```json
{
  "spot_forecast": {
    "direction": "up",
    "expected_move_pct": "2.0-4.0",
    "move_pct_range": "2.0-4.0",
    "timing": "next_1_2_sessions"
  }
}
```

### Strategy View

The strategy section remains deterministic and includes:
- `best_family`
- `preferred`
- `acceptable`
- `avoid`
- `why`

### Trade Setup

For directional setups, the report includes:
- entry range
- ideal entry
- stop loss
- target 1
- target 2
- time horizon
- risk/reward ratio

For binary setups, it includes:
- `upper_breakout`
- `lower_breakdown`

## Programmatic Usage

```python
from agents.options_analyzer import OptionsAnalyzerAgent
from utils.config import get_config
from utils.state_manager import get_state_manager

config = get_config("config.properties")
state_manager = get_state_manager("data/analyzed_articles.json")
options_analyzer = OptionsAnalyzerAgent(config, state_manager)

result = options_analyzer.run(analyzed_articles)

for analysis in result["analyses"]:
    print(analysis["ticker"])
    print(analysis["market_data"])
    print(analysis["trade_setup"])
    print(analysis["consolidated_view"])
```

## Example Output

```json
{
  "ticker": "RELIANCE",
  "market_data": {
    "current_price": 2850.5,
    "last_updated": "2026-04-16T20:58:00+05:30",
    "day_change_pct": 1.7,
    "volatility_context": "moderate"
  },
  "headline_assessment": "Bullish - use defined-risk strategies",
  "news_classification": {
    "event_type": "earnings_beat",
    "bias": "bullish",
    "strength": 3,
    "freshness": "breaking",
    "source_trust": 0.85
  },
  "spot_forecast": {
    "direction": "up",
    "expected_move_pct": "2.0-4.0",
    "move_pct_range": "2.0-4.0",
    "timing": "same_day"
  },
  "trade_setup": {
    "entry_price_range": "2836.25 - 2879.0",
    "ideal_entry": 2844.8,
    "stop_loss": 2773.14,
    "target_1": 2907.51,
    "target_2": 2964.52,
    "time_horizon": "intraday",
    "risk_reward_ratio": "1:0.9"
  },
  "strategy_view": {
    "best_family": "defined_risk_bullish",
    "preferred": ["bull_call_spread", "short_put", "itm_call_buy"],
    "acceptable": ["long_call"],
    "avoid": ["otm_weekly_call_buy"],
    "why": "Bullish direction clear but IV crush risk makes spreads better"
  },
  "consolidated_view": {
    "headline": "Bullish setup with controlled risk; better via spreads than naked calls",
    "action": "BUY_WITH_SPREAD",
    "conviction": "HIGH",
    "what_to_do": "Enter near 2844.8 with defined risk; prefer bull_call_spread, short_put",
    "what_to_avoid": "otm_weekly_call_buy",
    "key_reason": "Bullish direction clear but IV crush risk makes spreads better; volatility context is moderate"
  },
  "scores": {
    "spot_direction_score": 2.55,
    "volatility_score": -3.0,
    "tradability_score": 10.0,
    "premium_edge_score": 1.0
  }
}
```

## Benefits of the Updated Design

- **Actionable**: entry, stop, and target levels are included
- **Decision-ready**: direct action output such as BUY / SELL / WAIT / NO_TRADE
- **Real-time aware**: current price context is part of the analysis
- **Cleaner downstream payload**: easier for UI cards, alerts, and APIs
- **Production-friendly**: deterministic structure with clear layer boundaries

## Limitations

Current limitations still apply:

1. No live broker / exchange market API wired in yet
2. No option-chain-based implied move calculation
3. No position sizing logic
4. No historical backtesting
5. No Greeks or probability-of-profit analytics

## Recommended Next Enhancements

1. Replace fallback market data with live NSE / broker API integration
2. Add breakout-range logic for binary setups in UI
3. Surface final `action` prominently in Streamlit cards
4. Add unit tests for bullish, bearish, and binary trade setup rules
5. Add report export / API mode using the consolidated payload

## Disclaimer

**This tool is for educational and informational purposes only. It does not constitute financial advice. Options trading involves substantial risk and is not suitable for all investors. Always do your own research and consult with a qualified financial advisor before making trading decisions.**

---

Made with Bob