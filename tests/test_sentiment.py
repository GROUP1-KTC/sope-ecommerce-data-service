import pytest
from app.services.sentiment_analysis import sentiment_service

def test_sentiment_analysis_positive():
    """Test positive sentiment analysis"""
    text = "This product is amazing! I love it so much!"
    result = sentiment_service.analyze_sentiment(text)
    
    assert result.sentiment == "positive"
    assert result.score > 0.1
    assert result.confidence > 0.0

def test_sentiment_analysis_negative():
    """Test negative sentiment analysis"""
    text = "This product is terrible and awful. I hate it!"
    result = sentiment_service.analyze_sentiment(text)
    
    assert result.sentiment == "negative"
    assert result.score < -0.1
    assert result.confidence > 0.0

def test_sentiment_analysis_neutral():
    """Test neutral sentiment analysis"""
    text = "This is a product."
    result = sentiment_service.analyze_sentiment(text)
    
    assert result.sentiment in ["neutral", "positive", "negative"]
    assert -1.0 <= result.score <= 1.0

def test_batch_sentiment_analysis():
    """Test batch sentiment analysis"""
    texts = [
        "Great product!",
        "Terrible quality",
        "Average item"
    ]
    results = sentiment_service.analyze_batch_sentiment(texts)
    
    assert len(results) == 3
    assert all(r.sentiment in ["positive", "negative", "neutral"] for r in results)

def test_sentiment_distribution():
    """Test sentiment distribution calculation"""
    texts = [
        "Excellent quality!",
        "Amazing product!",
        "Terrible experience",
        "Just okay"
    ]
    distribution = sentiment_service.get_sentiment_distribution(texts)
    
    assert "positive" in distribution
    assert "negative" in distribution
    assert "neutral" in distribution
    assert sum(distribution.values()) == pytest.approx(1.0, rel=1e-9)