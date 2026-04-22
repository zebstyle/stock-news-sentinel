"""
Stock News Sentinel - Main Streamlit Application
AI-Powered Stock News Monitoring & Sentiment Analysis
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
from apscheduler.schedulers.background import BackgroundScheduler
import os
import atexit

from utils.config import get_config
from utils.logger import setup_logger
from utils.state_manager import get_state_manager
from agents.news_scraper import NewsScraperAgent
from agents.sentiment_analyzer import SentimentAnalyzerAgent
from agents.options_analyzer import OptionsAnalyzerAgent


# Page configuration
st.set_page_config(
    page_title="Stock News Sentinel",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
    }
    .positive {
        color: #28a745;
        font-weight: bold;
    }
    .negative {
        color: #dc3545;
        font-weight: bold;
    }
    .neutral {
        color: #6c757d;
        font-weight: bold;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
def init_session_state():
    """Initialize Streamlit session state"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        # Determine config path - works both locally and on Streamlit Cloud
        config_path = "config.properties" if os.path.exists("config.properties") else "stock-news-sentinel/config.properties"
        st.session_state.config = get_config(config_path)
        st.session_state.logger = setup_logger(
            log_file=st.session_state.config.log_file,
            log_level=st.session_state.config.log_level,
            log_to_console=st.session_state.config.log_to_console
        )
        st.session_state.state_manager = get_state_manager(st.session_state.config.data_file)
        
        # Initialize agents
        st.session_state.news_scraper = NewsScraperAgent(
            st.session_state.config,
            st.session_state.state_manager
        )
        st.session_state.sentiment_analyzer = SentimentAnalyzerAgent(
            st.session_state.config,
            st.session_state.state_manager
        )
        st.session_state.options_analyzer = OptionsAnalyzerAgent(
            st.session_state.config,
            st.session_state.state_manager
        )
        
        # Scheduler
        st.session_state.scheduler = None
        st.session_state.auto_scan_enabled = False
        
        # Options analysis storage
        if 'options_analyses' not in st.session_state:
            st.session_state.options_analyses = []
        
        st.session_state.logger.info("Application initialized")


def run_full_scan():
    """Run complete news scan, analysis, and alerting"""
    # Reset current scan outputs so stale analyses do not linger in the UI
    st.session_state.options_analyses = []

    with st.spinner("🔍 Scanning news sources..."):
        # Step 1: Scrape news
        scrape_result = st.session_state.news_scraper.run()
        
        if not scrape_result['success']:
            st.error(f"❌ News scraping failed: {scrape_result.get('error', 'Unknown error')}")
            return
        
        articles = scrape_result['articles']
        st.success(f"✅ Found {len(articles)} new articles")
        
        if not articles:
            st.info("No new articles found")
            return
    
    with st.spinner("🧠 Analyzing sentiment..."):
        # Step 2: Analyze sentiment
        analysis_result = st.session_state.sentiment_analyzer.run(articles)
        
        if not analysis_result['success']:
            st.error(f"❌ Sentiment analysis failed: {analysis_result.get('error', 'Unknown error')}")
            return
        
        analyzed_articles = analysis_result['articles']
        alert_articles = analysis_result['alert_articles']
        stats = analysis_result['statistics']
        
        st.success(f"✅ Analyzed {len(analyzed_articles)} articles")
        st.info(f"📊 Positive: {stats['positive']}, Negative: {stats['negative']}, Neutral: {stats['neutral']}")
    
    with st.spinner("📈 Analyzing options implications..."):
        # Step 3: Analyze options
        options_result = st.session_state.options_analyzer.run(analyzed_articles)
        
        if options_result['success']:
            st.session_state.options_analyses = options_result['analyses']
            st.success(f"✅ Generated {len(options_result['analyses'])} consolidated stock analyses")
            if options_result.get('statistics'):
                opt_stats = options_result['statistics']
                st.info(f"📊 Tradable: {opt_stats.get('tradable_count', 0)}, Watch: {opt_stats.get('non_tradable_count', 0)}")
        else:
            st.warning(f"⚠️ Options analysis failed: {options_result.get('error', 'Unknown error')}")


def scheduled_scan():
    """Scheduled scan function for background execution"""
    try:
        st.session_state.logger.info("Running scheduled scan...")
        
        # Run scraper
        scrape_result = st.session_state.news_scraper.run()
        if scrape_result['success'] and scrape_result['articles']:
            # Run analyzer
            analysis_result = st.session_state.sentiment_analyzer.run(scrape_result['articles'])
            if analysis_result['success']:
                # Replace options analyses with latest consolidated results only
                options_result = st.session_state.options_analyzer.run(analysis_result['articles'])
                if options_result.get('success'):
                    st.session_state.options_analyses = options_result.get('analyses', [])
        
        st.session_state.logger.info("Scheduled scan completed")
    except Exception as e:
        st.session_state.logger.error(f"Error in scheduled scan: {e}", exc_info=True)


def main():
    """Main application"""
    init_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">📈 Stock News Sentinel</h1>', unsafe_allow_html=True)
    st.markdown("**AI-Powered Stock News Monitoring & Sentiment Analysis**")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Display monitored stocks
        st.subheader("📊 Monitored Stocks")
        stocks = st.session_state.config.stocks
        st.write(", ".join(stocks))
        
        # Display news sources
        st.subheader("📰 News Sources")
        for source in st.session_state.config.news_sources:
            st.write(f"• {source}")
        
        st.divider()
        
        # Manual scan button
        st.subheader("🔍 Manual Scan")
        if st.button("🚀 Run Scan Now", type="primary"):
            run_full_scan()
        
        st.divider()
        
        # Auto-scan settings
        st.subheader("⏰ Auto-Scan")
        auto_scan = st.checkbox(
            "Enable Auto-Scan",
            value=st.session_state.auto_scan_enabled,
            help=f"Automatically scan every {st.session_state.config.check_interval_minutes} minutes"
        )
        
        if auto_scan != st.session_state.auto_scan_enabled:
            st.session_state.auto_scan_enabled = auto_scan
            
            if auto_scan:
                # Start scheduler
                if st.session_state.scheduler is None:
                    st.session_state.scheduler = BackgroundScheduler()
                    st.session_state.scheduler.add_job(
                        scheduled_scan,
                        'interval',
                        minutes=st.session_state.config.check_interval_minutes
                    )
                    st.session_state.scheduler.start()
                    atexit.register(lambda: st.session_state.scheduler.shutdown())
                st.success("✅ Auto-scan enabled")
            else:
                # Stop scheduler
                if st.session_state.scheduler:
                    st.session_state.scheduler.shutdown()
                    st.session_state.scheduler = None
                st.info("Auto-scan disabled")
        
    
    # Main content
    tabs = st.tabs(["📊 Dashboard", "📰 Recent Articles", "💹 Options Analysis", "📈 Statistics", "⚙️ Settings"])
    
    # Dashboard Tab
    with tabs[0]:
        st.header("Dashboard")
        
        # Get statistics
        stats = st.session_state.state_manager.get_stats()
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Articles", stats.get('total_articles', 0))
        
        with col2:
            st.metric("Positive", stats.get('positive_articles', 0), delta_color="normal")
        
        with col3:
            st.metric("Negative", stats.get('negative_articles', 0), delta_color="inverse")
        
        with col4:
            st.metric("Options Analyses", len(st.session_state.options_analyses) if hasattr(st.session_state, 'options_analyses') else 0)
        
        st.divider()
        
        # Last scan info
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Last Scan")
            last_scan = stats.get('last_scan')
            if last_scan:
                st.write(f"🕐 {last_scan}")
            else:
                st.write("No scans yet")
        
        with col2:
            st.subheader("Total Scans")
            st.write(f"🔄 {stats.get('scan_count', 0)} scans")
        
        st.divider()
        
        # Recent articles by stock
        st.subheader("📊 Articles by Stock")
        
        articles_by_stock = {}
        all_articles = st.session_state.state_manager.get_all_articles()
        
        for article in all_articles.values():
            stock = article.get('stock', 'Unknown')
            if stock not in articles_by_stock:
                articles_by_stock[stock] = {'positive': 0, 'negative': 0, 'neutral': 0}
            
            sentiment = article.get('sentiment_label', 'neutral')
            articles_by_stock[stock][sentiment] += 1
        
        if articles_by_stock:
            df = pd.DataFrame(articles_by_stock).T
            st.bar_chart(df)
        else:
            st.info("No articles analyzed yet")
    
    # Recent Articles Tab
    with tabs[1]:
        st.header("Recent Articles")
        
        # Filters
        col1, col2 = st.columns(2)
        
        with col1:
            filter_stock = st.selectbox(
                "Filter by Stock",
                ["All"] + st.session_state.config.stocks
            )
        
        with col2:
            filter_sentiment = st.selectbox(
                "Filter by Sentiment",
                ["All", "Positive", "Negative", "Neutral"]
            )
        
        # Get articles
        articles = st.session_state.state_manager.get_recent_articles(50)
        
        # Apply filters
        if filter_stock != "All":
            articles = [a for a in articles if a.get('stock', '').upper() == filter_stock.upper()]
        
        if filter_sentiment != "All":
            articles = [a for a in articles if a.get('sentiment_label', '').lower() == filter_sentiment.lower()]
        
        # Display articles
        if articles:
            for article in articles:
                with st.expander(f"**{article.get('stock', 'Unknown')}** - {article.get('title', 'No title')}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        sentiment = article.get('sentiment_label', 'neutral')
                        sentiment_class = sentiment if sentiment in ['positive', 'negative', 'neutral'] else 'neutral'
                        st.markdown(f"**Sentiment:** <span class='{sentiment_class}'>{sentiment.upper()}</span>", unsafe_allow_html=True)
                    
                    with col2:
                        st.write(f"**Score:** {article.get('sentiment_score', 0):.2f}")
                    
                    with col3:
                        st.write(f"**Confidence:** {article.get('confidence', 0):.1%}")
                    
                    st.write(f"**Impact:** {article.get('impact_description', 'N/A')}")
                    st.write(f"**URL:** {article.get('url', 'N/A')}")
                    st.write(f"**Analyzed:** {article.get('analyzed_at', 'N/A')}")
        else:
            st.info("No articles found matching the filters")
    
    # Options Analysis Tab
    with tabs[2]:
        st.header("💹 Options Analysis")
        
        if not st.session_state.options_analyses:
            st.info("No options analyses available. Run a scan to generate options recommendations.")
        else:
            analyses = sorted(
                st.session_state.options_analyses,
                key=lambda a: (
                    a.get('scores', {}).get('tradability_score', 0),
                    a.get('confidence', 0),
                    a.get('ticker', '')
                ),
                reverse=True
            )

            # Summary metrics
            st.subheader("Summary")
            col1, col2, col3, col4 = st.columns(4)
            
            total_analyses = len(analyses)
            tradable = sum(1 for a in analyses 
                          if a.get('scores', {}).get('tradability_score', 0) >= 5)
            bullish = sum(1 for a in analyses 
                         if a.get('news_classification', {}).get('bias') == 'bullish')
            bearish = sum(1 for a in analyses 
                         if a.get('news_classification', {}).get('bias') == 'bearish')
            
            with col1:
                st.metric("Total Analyses", total_analyses)
            with col2:
                st.metric("Tradable", tradable)
            with col3:
                st.metric("Bullish", bullish)
            with col4:
                st.metric("Bearish", bearish)
            
            st.divider()
            
            # Filters
            col1, col2, col3 = st.columns(3)
            
            with col1:
                filter_ticker = st.selectbox(
                    "Filter by Ticker",
                    ["All"] + sorted(list(set(a.get('ticker', 'Unknown') for a in analyses)))
                )
            
            with col2:
                filter_tradability = st.selectbox(
                    "Filter by Tradability",
                    ["All", "Highly Tradable (8+)", "Tradable (5-7)", "Watch Only (3-4)", "Avoid (<3)"]
                )
            
            with col3:
                filter_bias = st.selectbox(
                    "Filter by Bias",
                    ["All", "Bullish", "Bearish", "Neutral", "Binary"]
                )
            
            # Apply filters
            filtered_analyses = analyses
            
            if filter_ticker != "All":
                filtered_analyses = [a for a in filtered_analyses if a.get('ticker') == filter_ticker]
            
            if filter_tradability != "All":
                if "Highly Tradable" in filter_tradability:
                    filtered_analyses = [a for a in filtered_analyses 
                                       if a.get('scores', {}).get('tradability_score', 0) >= 8]
                elif "Tradable" in filter_tradability:
                    filtered_analyses = [a for a in filtered_analyses 
                                       if 5 <= a.get('scores', {}).get('tradability_score', 0) < 8]
                elif "Watch Only" in filter_tradability:
                    filtered_analyses = [a for a in filtered_analyses 
                                       if 3 <= a.get('scores', {}).get('tradability_score', 0) < 5]
                elif "Avoid" in filter_tradability:
                    filtered_analyses = [a for a in filtered_analyses 
                                       if a.get('scores', {}).get('tradability_score', 0) < 3]
            
            if filter_bias != "All":
                filtered_analyses = [a for a in filtered_analyses 
                                   if a.get('news_classification', {}).get('bias', '').lower() == filter_bias.lower()]
            
            st.divider()
            
            # Display analyses
            if filtered_analyses:
                for analysis in filtered_analyses:
                    ticker = analysis.get('ticker', 'Unknown')
                    headline = analysis.get('headline_assessment', 'No assessment')
                    scores = analysis.get('scores', {})
                    tradability = scores.get('tradability_score', 0)
                    
                    # Color code by tradability
                    if tradability >= 8:
                        color = "🟢"
                    elif tradability >= 5:
                        color = "🟡"
                    elif tradability >= 3:
                        color = "🟠"
                    else:
                        color = "🔴"
                    
                    with st.expander(f"{color} **{ticker}** - {headline}"):
                        # News Classification
                        st.subheader("📰 News Classification")
                        news_class = analysis.get('news_classification', {})
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Event:** {news_class.get('event_type', 'N/A').replace('_', ' ').title()}")
                        with col2:
                            bias = news_class.get('bias', 'neutral')
                            bias_class = 'positive' if bias == 'bullish' else ('negative' if bias == 'bearish' else 'neutral')
                            st.markdown(f"**Bias:** <span class='{bias_class}'>{bias.upper()}</span>", unsafe_allow_html=True)
                        with col3:
                            st.write(f"**Strength:** {news_class.get('strength', 0)}/5")
                        
                        st.divider()
                        
                        # Spot & Vol Forecast
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("📊 Spot Forecast")
                            spot = analysis.get('spot_forecast', {})
                            st.write(f"**Direction:** {spot.get('direction', 'N/A').upper()}")
                            st.write(f"**Expected Move:** {spot.get('expected_move_pct', spot.get('move_pct_range', 'N/A'))}%")
                            st.write(f"**Timing:** {spot.get('timing', 'N/A').replace('_', ' ').title()}")

                            market_data = analysis.get('market_data', {})
                            if market_data:
                                st.write(f"**Current Price:** {market_data.get('current_price', 'N/A')}")
                                st.write(f"**Day Change:** {market_data.get('day_change_pct', 'N/A')}%")
                                st.write(f"**Price Source:** {market_data.get('source_label', market_data.get('source', 'N/A'))}")
                                st.write(f"**Fresh Data:** {'Yes' if market_data.get('is_fresh') else 'No'}")
                                if not market_data.get('trade_allowed', True):
                                    st.warning(
                                        f"Trade blocked due to price mismatch. API price: {market_data.get('current_price', 'N/A')}, "
                                        f"Article price: {market_data.get('article_price', 'N/A')}, "
                                        f"Deviation: {market_data.get('price_deviation_pct', 'N/A')}%"
                                    )
                        
                        with col2:
                            st.subheader("📈 Volatility Forecast")
                            vol = analysis.get('vol_forecast', {})
                            st.write(f"**IV Direction:** {vol.get('iv_direction', 'N/A').upper()}")
                            st.write(f"**IV Intensity:** {vol.get('iv_intensity', 'N/A').replace('_', ' ').title()}")
                            st.write(f"**Gap Risk:** {vol.get('gap_risk', 'N/A').upper()}")

                            market_data = analysis.get('market_data', {})
                            if market_data:
                                st.write(f"**Volatility Context:** {market_data.get('volatility_context', 'N/A').title()}")
                                st.write(f"**Last Updated:** {market_data.get('last_updated', 'N/A')}")
                                if market_data.get('symbol'):
                                    st.write(f"**Market Symbol:** {market_data.get('symbol')}")
                        
                        st.divider()

                        trade_setup = analysis.get('trade_setup', {})
                        if trade_setup:
                            st.subheader("🎯 Trade Setup")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.write(f"**Entry Range:** {trade_setup.get('entry_range', trade_setup.get('entry_price_range', 'N/A'))}")
                                st.write(f"**Ideal Entry:** {trade_setup.get('ideal_entry', 'N/A')}")
                            with col2:
                                st.write(f"**Stop Loss:** {trade_setup.get('stop_loss', 'N/A')}")
                                st.write(f"**Target 1:** {trade_setup.get('target_1', 'N/A')}")
                            with col3:
                                st.write(f"**Target 2:** {trade_setup.get('target_2', 'N/A')}")
                                st.write(f"**Risk/Reward:** {trade_setup.get('risk_reward', trade_setup.get('risk_reward_ratio', 'N/A'))}")
                            st.write(f"**Time Horizon:** {trade_setup.get('time_horizon', 'N/A')}")
                            st.divider()
                        
                        # Strategy Recommendation
                        st.subheader("💡 Strategy Recommendation")
                        strategy = analysis.get('strategy_view', {})
                        
                        st.write(f"**Best Family:** {strategy.get('best_family', 'N/A').replace('_', ' ').title()}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**✅ Preferred Strategies:**")
                            for strat in strategy.get('preferred', []):
                                st.write(f"  • {strat.replace('_', ' ').title()}")
                        
                        with col2:
                            st.write("**❌ Avoid Strategies:**")
                            for strat in strategy.get('avoid', []):
                                st.write(f"  • {strat.replace('_', ' ').title()}")
                        
                        st.info(f"**Why:** {strategy.get('why', 'N/A')}")
                        
                        consolidated = analysis.get('consolidated_view', {})
                        if consolidated:
                            st.subheader("🧠 Consolidated View")
                            st.write(f"**Headline:** {consolidated.get('headline', 'N/A')}")
                            st.write(f"**Action:** {consolidated.get('action', 'N/A')}")
                            st.write(f"**Conviction:** {consolidated.get('conviction', 'N/A')}")
                            st.write(f"**What To Do:** {consolidated.get('what_to_do', 'N/A')}")
                            st.write(f"**What To Avoid:** {consolidated.get('what_to_avoid', 'N/A')}")
                            st.write(f"**Key Reason:** {consolidated.get('key_reason', 'N/A')}")
                        
                        st.divider()
                        
                        # Scores
                        st.subheader("📊 Scores")
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            spot_score = scores.get('spot_direction_score', 0)
                            st.metric("Spot Direction", f"{spot_score:+.1f}", help="Range: -5 (bearish) to +5 (bullish)")
                        
                        with col2:
                            vol_score = scores.get('volatility_score', 0)
                            st.metric("Volatility", f"{vol_score:+.1f}", help="Range: -5 (compression) to +5 (expansion)")
                        
                        with col3:
                            trade_score = scores.get('tradability_score', 0)
                            st.metric("Tradability", f"{trade_score:.1f}/10", help="Higher = more tradable")
                        
                        with col4:
                            premium_score = scores.get('premium_edge_score', 0)
                            st.metric("Premium Edge", f"{premium_score:+.1f}", help="Range: -5 (sell) to +5 (buy)")
                        
                        # Score Interpretations
                        score_interp = analysis.get('score_interpretations', {})
                        if score_interp:
                            st.write("**Interpretations:**")
                            for key, value in score_interp.items():
                                st.write(f"  • {key.replace('_', ' ').title()}: {value}")
                        
                        st.divider()
                        
                        # Additional Info
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Confidence:** {analysis.get('confidence', 0):.1%}")
                            st.write(f"**Key Risks:** {', '.join(analysis.get('key_risks', []))}")
                        
                        with col2:
                            st.write(f"**Article:** [{analysis.get('article_title', 'View Article')[:50]}...]({analysis.get('article_url', '#')})")
                            st.write(f"**Analyzed:** {analysis.get('analyzed_at', 'N/A')}")
            else:
                st.info("No analyses match the selected filters")
    
    # Statistics Tab
    with tabs[3]:
        st.header("Statistics")
        
        stats = st.session_state.state_manager.get_stats()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Sentiment Distribution")
            sentiment_data = {
                'Positive': stats.get('positive_articles', 0),
                'Negative': stats.get('negative_articles', 0),
                'Neutral': stats.get('neutral_articles', 0)
            }
            st.bar_chart(sentiment_data)
        
        with col2:
            st.subheader("Activity Summary")
            st.metric("Total Scans", stats.get('scan_count', 0))
            st.metric("Total Articles", stats.get('total_articles', 0))
            st.metric("Options Analyses", len(st.session_state.options_analyses) if hasattr(st.session_state, 'options_analyses') else 0)
        
        st.divider()
        
        # Agent status
        st.subheader("Agent Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**News Scraper Agent**")
            scraper_status = st.session_state.news_scraper.get_status()
            st.json(scraper_status)
        
        with col2:
            st.write("**Sentiment Analyzer Agent**")
            analyzer_status = st.session_state.sentiment_analyzer.get_status()
            st.json(analyzer_status)
        
        with col3:
            st.write("**Options Analyzer Agent**")
            options_status = st.session_state.options_analyzer.get_status()
            st.json(options_status)
    
    # Settings Tab
    with tabs[4]:
        st.header("Settings")
        
        st.subheader("Configuration")
        
        config_data = {
            "Stocks": ", ".join(st.session_state.config.stocks),
            "News Sources": len(st.session_state.config.news_sources),
            "Check Interval": f"{st.session_state.config.check_interval_minutes} minutes",
            "Sentiment Threshold": st.session_state.config.sentiment_threshold,
            "Confidence Threshold": st.session_state.config.confidence_threshold,
            "Primary Model": st.session_state.config.primary_sentiment_model
        }
        
        for key, value in config_data.items():
            st.write(f"**{key}:** {value}")
        
        st.divider()
        
        st.subheader("Data Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Clear All Data", type="secondary"):
                if st.checkbox("Confirm clear all data"):
                    st.session_state.state_manager.clear_all()
                    st.session_state.options_analyses = []
                    st.success("All data cleared")
                    st.rerun()
        
        with col2:
            retention_days = st.number_input(
                "History Retention (days)",
                min_value=1,
                max_value=365,
                value=st.session_state.config.history_retention_days
            )
            if st.button("🧹 Cleanup Old Articles"):
                st.session_state.state_manager.cleanup_old_articles(retention_days)
                st.success(f"Cleaned up articles older than {retention_days} days")
                st.rerun()


if __name__ == "__main__":
    main()


