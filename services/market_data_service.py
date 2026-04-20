"""
Market data service for stock-news-sentinel.
Fetches live equity quote data using Alpha Vantage and normalizes it for the rules engine.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import requests

from utils.logger import LoggerMixin
from utils.config import Config


class MarketDataService(LoggerMixin):
    """Fetch live market data for equities using Alpha Vantage."""

    SYMBOL_ALIASES = {
        "RELIANCE": "RELIANCE.BSE",
        "VEDL": "VEDL.BSE",
        "VEDANTA": "VEDL.BSE",
        "WIPRO": "WIPRO.BSE",
        "INFY": "INFY.BSE",
        "TCS": "TCS.BSE",
        "HDFC": "HDFCBANK.BSE",
        "HDFCBANK": "HDFCBANK.BSE",
        "ICICIBANK": "ICICIBANK.BSE",
        "SBIN": "SBIN.BSE",
        "LT": "LT.BSE",
        "BHARTIARTL": "BHARTIARTL.BSE",
        "ITC": "ITC.BSE",
        "COAL INDIA": "COALINDIA.BSE",
        "COALINDIA": "COALINDIA.BSE",
        "BHARAT RASAYAN": "BHARATRAS.BSE",
        "APEX FOOD": "APEX.BSE"
    }

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.config.user_agent,
            "Accept": "application/json"
        })

    def _normalize_symbol(self, ticker: str) -> str:
        """Map app ticker name to Alpha Vantage symbol."""
        normalized = ticker.strip().upper()
        return self.SYMBOL_ALIASES.get(normalized, normalized.replace(" ", "") + ".BSE")

    def _build_quote_params(self, ticker: str) -> Dict[str, str]:
        """Build Alpha Vantage quote request params."""
        return {
            "function": "GLOBAL_QUOTE",
            "symbol": self._normalize_symbol(ticker),
            "apikey": self.config.alpha_vantage_key or ""
        }

    def _get_volatility_context(self, day_change_pct: float) -> str:
        """Convert day move into volatility context bucket."""
        abs_move = abs(day_change_pct)
        if abs_move < 1:
            return "low"
        if abs_move <= 3:
            return "moderate"
        return "high"

    def get_quote(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Fetch raw quote data from Alpha Vantage."""
        if not self.config.alpha_vantage_key:
            self.logger.warning("Alpha Vantage API key not configured")
            return None

        try:
            response = self.session.get(
                self.BASE_URL,
                params=self._build_quote_params(ticker),
                timeout=self.config.request_timeout
            )
            response.raise_for_status()
            data = response.json()

            if "Note" in data:
                self.logger.warning(f"Alpha Vantage rate limit message for {ticker}: {data['Note']}")
                return None

            if "Error Message" in data:
                self.logger.warning(f"Alpha Vantage symbol lookup failed for {ticker}: {data['Error Message']}")
                return None

            quote = data.get("Global Quote", {})
            if quote and quote.get("05. price"):
                return quote

            normalized_symbol = self._normalize_symbol(ticker)
            if ticker.strip().upper() != normalized_symbol.upper():
                fallback_response = self.session.get(
                    self.BASE_URL,
                    params={
                        "function": "GLOBAL_QUOTE",
                        "symbol": normalized_symbol,
                        "apikey": self.config.alpha_vantage_key or ""
                    },
                    timeout=self.config.request_timeout
                )
                fallback_response.raise_for_status()
                fallback_data = fallback_response.json()

                if "Note" in fallback_data:
                    self.logger.warning(f"Alpha Vantage rate limit message for {ticker}: {fallback_data['Note']}")
                    return None

                if "Error Message" in fallback_data:
                    self.logger.warning(f"Alpha Vantage symbol lookup failed for {ticker}: {fallback_data['Error Message']}")
                    return None

                fallback_quote = fallback_data.get("Global Quote", {})
                if fallback_quote and fallback_quote.get("05. price"):
                    self.logger.info(f"Resolved {ticker} via normalized symbol {normalized_symbol}")
                    return fallback_quote

            self.logger.warning(f"No Alpha Vantage quote returned for {ticker}")
            return None
        except Exception as e:
            self.logger.warning(f"Failed to fetch Alpha Vantage market quote for {ticker}: {e}")
            return None

    def get_market_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Fetch normalized market data for a ticker."""
        self.logger.info(f"Fetching market data for ticker: {ticker}")
        quote = self.get_quote(ticker)
        if not quote:
            self.logger.warning(f"No quote data returned for {ticker}")
            return None

        current_price_raw = quote.get("05. price")
        day_change_pct_raw = quote.get("10. change percent", "0%")
        symbol = quote.get("01. symbol", self._normalize_symbol(ticker))
        last_trading_day = quote.get("07. latest trading day")

        self.logger.info(f"Raw quote data for {ticker}: price={current_price_raw}, symbol={symbol}, trading_day={last_trading_day}")

        if not current_price_raw:
            self.logger.warning(f"No price field in quote for {ticker}")
            return None

        try:
            current_price = round(float(str(current_price_raw).replace(",", "")), 2)
            self.logger.info(f"Successfully parsed price for {ticker}: {current_price}")
        except Exception as e:
            self.logger.warning(f"Invalid Alpha Vantage price for {ticker}: {current_price_raw}, error: {e}")
            return None

        try:
            day_change_pct = round(float(str(day_change_pct_raw).replace("%", "").replace(",", "")), 2)
        except Exception:
            day_change_pct = 0.0

        if last_trading_day:
            last_updated = f"{last_trading_day}T15:30:00+05:30"
            is_fresh = last_trading_day == datetime.now().astimezone().date().isoformat()
        else:
            last_updated = datetime.now().astimezone().isoformat()
            is_fresh = False

        market_data = {
            "current_price": current_price,
            "last_updated": last_updated,
            "day_change_pct": day_change_pct,
            "volatility_context": self._get_volatility_context(day_change_pct),
            "symbol": symbol,
            "source": "alpha_vantage",
            "source_label": "Alpha Vantage",
            "is_fresh": is_fresh,
            "trade_allowed": True,
            "price_deviation_pct": 0.0
        }
        
        self.logger.info(f"Returning market data for {ticker}: {market_data}")
        return market_data


# Made with Bob