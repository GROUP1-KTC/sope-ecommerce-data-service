#!/usr/bin/env python3
"""
Simple test script to verify the basic application structure
"""
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_basic_imports():
    """Test that we can import the main components"""
    try:
        # Test sentiment analysis
        from app.services.sentiment_analysis import SentimentAnalysisService
        sentiment_service = SentimentAnalysisService()
        print("✅ Sentiment analysis service imported successfully")
        
        # Test basic sentiment analysis without NLTK dependencies
        result = sentiment_service._keyword_sentiment_score("This is amazing and excellent!")
        print(f"✅ Keyword sentiment score: {result}")
        
        # Test models
        from app.models.schemas import SentimentRequest, ProductFilter
        print("✅ Pydantic models imported successfully")
        
        # Test config
        from app.core.config import Settings
        settings = Settings()
        print(f"✅ Configuration loaded: {settings.API_HOST}:{settings.API_PORT}")
        
        print("\n🎉 All basic components are working correctly!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_basic_imports()
    sys.exit(0 if success else 1)