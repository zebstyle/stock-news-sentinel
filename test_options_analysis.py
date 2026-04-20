"""
Test script for Options Analysis module
Tests the complete pipeline with sample data
"""

import sys
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, '.')

from services.options_extractor import OptionsFeatureExtractor
from services.options_rules_engine import OptionsRulesEngine
from services.options_scoring import OptionsScoring


def create_sample_articles():
    """Create sample articles with sentiment analysis"""
    return [
        {
            'id': '1',
            'stock': 'RELIANCE',
            'company_name': 'Reliance Industries',
            'title': 'Reliance Industries beats Q4 earnings estimates, raises guidance',
            'text': 'Reliance Industries reported strong quarterly results beating analyst estimates. The company also raised its full-year guidance citing strong demand.',
            'url': 'https://example.com/reliance-earnings',
            'source': 'Economic Times',
            'published_at': datetime.now().isoformat(),
            'sentiment_score': 0.85,
            'sentiment_label': 'positive',
            'confidence': 0.92,
            'impact': 'high',
            'impact_description': 'Strong positive impact expected',
            'current_price': 2850.50
        },
        {
            'id': '2',
            'stock': 'INFY',
            'company_name': 'Infosys',
            'title': 'Infosys faces regulatory probe over accounting practices',
            'text': 'Regulatory authorities have initiated an investigation into Infosys accounting practices following whistleblower complaints.',
            'url': 'https://example.com/infy-probe',
            'source': 'Bloomberg',
            'published_at': datetime.now().isoformat(),
            'sentiment_score': -0.78,
            'sentiment_label': 'negative',
            'confidence': 0.88,
            'impact': 'high',
            'impact_description': 'Significant negative impact expected',
            'current_price': 1490.25
        },
        {
            'id': '3',
            'stock': 'TCS',
            'company_name': 'Tata Consultancy Services',
            'title': 'TCS announces routine quarterly filing',
            'text': 'TCS submitted its routine quarterly compliance filing with the stock exchange.',
            'url': 'https://example.com/tcs-filing',
            'source': 'Moneycontrol',
            'published_at': datetime.now().isoformat(),
            'sentiment_score': 0.05,
            'sentiment_label': 'neutral',
            'confidence': 0.65,
            'impact': 'low',
            'impact_description': 'Minimal impact expected',
            'current_price': 3925.10
        },
        {
            'id': '4',
            'stock': 'HDFC',
            'company_name': 'HDFC Bank',
            'title': 'HDFC Bank receives regulatory approval for new branch expansion',
            'text': 'HDFC Bank received approval from RBI to open 500 new branches across India, marking a major expansion.',
            'url': 'https://example.com/hdfc-approval',
            'source': 'Reuters',
            'published_at': datetime.now().isoformat(),
            'sentiment_score': 0.72,
            'sentiment_label': 'positive',
            'confidence': 0.85,
            'impact': 'medium',
            'impact_description': 'Moderate positive impact',
            'current_price': 1688.40
        }
    ]


def build_market_data(article, llm_extraction):
    """Mirror analyzer market-data enrichment for rules-engine tests."""
    explicit_price = (
        article.get('current_price')
        or article.get('market_price')
        or article.get('ltp')
        or article.get('price')
    )

    move_low = float(llm_extraction.get('expected_spot_move_pct_low', 0.0))
    move_high = float(llm_extraction.get('expected_spot_move_pct_high', 0.0))
    avg_move = (move_low + move_high) / 2.0
    sentiment_score = abs(float(article.get('sentiment_score', 0.0)))

    if explicit_price is not None:
        current_price = round(float(explicit_price), 2)
    else:
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

    return {
        'current_price': current_price,
        'last_updated': datetime.now().astimezone().isoformat(),
        'day_change_pct': day_change_pct,
        'volatility_context': volatility_context
    }


def test_feature_extraction():
    """Test the feature extraction layer"""
    print("\n" + "="*80)
    print("TEST 1: Feature Extraction Layer")
    print("="*80)
    
    extractor = OptionsFeatureExtractor()
    articles = create_sample_articles()
    
    for article in articles:
        print(f"\n--- Testing: {article['stock']} ---")
        print(f"Title: {article['title'][:60]}...")
        print(f"Sentiment: {article['sentiment_label']} ({article['sentiment_score']:.2f})")
        
        features = extractor.extract_features(article)
        
        print(f"\nExtracted Features:")
        print(f"  Event Type: {features['event_type']}")
        print(f"  Bias: {features['bias']} (Strength: {features['bias_strength']}/5)")
        print(f"  Expected Move: {features['expected_spot_move_bucket']} ({features['expected_spot_move_pct_low']}-{features['expected_spot_move_pct_high']}%)")
        print(f"  Timing: {features['expected_move_timing']}")
        print(f"  IV Reaction: {features['iv_reaction_post_event']}")
        print(f"  Gap Risk: {features['gap_risk']}")
        print(f"  Uncertainty: {features['uncertainty']}")
        print(f"  Key Risks: {', '.join(features['key_risks'])}")
    
    return True


def test_rules_engine():
    """Test the rules engine"""
    print("\n" + "="*80)
    print("TEST 2: Rules Engine")
    print("="*80)
    
    extractor = OptionsFeatureExtractor()
    rules_engine = OptionsRulesEngine()
    articles = create_sample_articles()
    
    for article in articles:
        print(f"\n--- Testing: {article['stock']} ---")
        
        # Extract features
        llm_extraction = extractor.extract_features(article)
        market_data = build_market_data(article, llm_extraction)
        
        # Apply rules
        options_impact = rules_engine.apply_rules(llm_extraction, market_data)
        
        option_view = options_impact['option_view']
        
        print(f"\nOptions Impact:")
        print(f"  Market Data: price={market_data['current_price']} change={market_data['day_change_pct']}% context={market_data['volatility_context']}")
        print(f"  Spot View: {option_view['spot_view']['direction']} ({option_view['spot_view']['expected_move_pct']}%)")
        print(f"  Vol View: IV {option_view['vol_view']['iv_direction']}")
        print(f"  Best Strategy Family: {option_view['strategy_preference']['best_trade_family']}")
        print(f"  Preferred Strategies: {', '.join(option_view['strategy_preference']['preferred'][:3])}")
        print(f"  Avoid: {', '.join(option_view['strategy_preference']['avoid'][:2])}")
        print(f"  Confidence: {option_view['confidence']:.2%}")
        print(f"  Trade Setup: {json.dumps(option_view['trade_setup'], indent=2)}")
        print(f"  Consolidated View: {json.dumps(option_view['consolidated_view'], indent=2)}")
        print(f"  Summary: {option_view['summary']}")
    
    return True


def test_scoring():
    """Test the scoring module"""
    print("\n" + "="*80)
    print("TEST 3: Scoring Module")
    print("="*80)
    
    extractor = OptionsFeatureExtractor()
    scoring = OptionsScoring()
    articles = create_sample_articles()
    
    for article in articles:
        print(f"\n--- Testing: {article['stock']} ---")
        
        # Extract features
        llm_extraction = extractor.extract_features(article)
        
        # Calculate scores
        scores = scoring.calculate_all_scores(llm_extraction)
        interpretations = scoring.interpret_scores(scores)
        
        print(f"\nScores:")
        print(f"  Spot Direction: {scores['spot_direction_score']:+.1f}/5 - {interpretations['spot_direction']}")
        print(f"  Volatility: {scores['volatility_score']:+.1f}/5 - {interpretations['volatility']}")
        print(f"  Tradability: {scores['tradability_score']:.1f}/10 - {interpretations['tradability']}")
        print(f"  Premium Edge: {scores['premium_edge_score']:+.1f}/5 - {interpretations['premium_edge']}")
    
    return True


def test_complete_pipeline():
    """Test the complete pipeline"""
    print("\n" + "="*80)
    print("TEST 4: Complete Pipeline")
    print("="*80)
    
    from agents.options_analyzer import OptionsAnalyzerAgent
    from utils.config import Config
    from utils.state_manager import StateManager
    
    config = Config("stock-news-sentinel/config.properties")
    state_manager = StateManager("test_data.json")
    
    # Initialize analyzer
    analyzer = OptionsAnalyzerAgent(config, state_manager)
    
    # Get sample articles
    articles = create_sample_articles()
    
    # Run analysis
    result = analyzer.run(articles)
    
    print(f"\nPipeline Result:")
    print(f"  Success: {result['success']}")
    print(f"  Analyses Generated: {result['count']}")
    print(f"  Duration: {result.get('duration', 0):.2f}s")
    
    if result.get('statistics'):
        stats = result['statistics']
        print(f"\nStatistics:")
        print(f"  Total Analyzed: {stats['total_analyzed']}")
        print(f"  By Bias: {stats['by_bias']}")
        print(f"  Tradable: {stats['tradable_count']}")
        print(f"  Non-Tradable: {stats['non_tradable_count']}")
        print(f"  Average Scores: {stats['average_scores']}")
    
    # Display sample analysis
    if result['analyses']:
        print(f"\n--- Sample Analysis: {result['analyses'][0]['ticker']} ---")
        analysis = result['analyses'][0]
        print(f"Headline: {analysis['headline_assessment']}")
        print(f"Market Data: {json.dumps(analysis['market_data'], indent=2)}")
        print(f"Spot Forecast: {json.dumps(analysis['spot_forecast'], indent=2)}")
        print(f"Trade Setup: {json.dumps(analysis['trade_setup'], indent=2)}")
        print(f"Consolidated View: {json.dumps(analysis['consolidated_view'], indent=2)}")
        print(f"Best Strategy: {analysis['strategy_view']['best_family']}")
        print(f"Preferred: {', '.join(analysis['strategy_view']['preferred'])}")
        print(f"Tradability: {analysis['scores']['tradability_score']:.1f}/10")
    
    return True


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("OPTIONS ANALYSIS MODULE - TEST SUITE")
    print("="*80)
    
    tests = [
        ("Feature Extraction", test_feature_extraction),
        ("Rules Engine", test_rules_engine),
        ("Scoring Module", test_scoring),
        ("Complete Pipeline", test_complete_pipeline)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, "PASSED" if success else "FAILED"))
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((test_name, "ERROR"))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, status in results:
        symbol = "[PASS]" if status == "PASSED" else "[FAIL]"
        print(f"{symbol} {test_name}: {status}")
    
    passed = sum(1 for _, status in results if status == "PASSED")
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n*** All tests passed successfully! ***")
        return 0
    else:
        print("\n*** Some tests failed. Please review the output above. ***")
        return 1


if __name__ == "__main__":
    exit(main())


# Made with Bob