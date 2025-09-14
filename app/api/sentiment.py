from fastapi import APIRouter, HTTPException
from typing import List

from app.models.schemas import (
    SentimentRequest, 
    SentimentResponse, 
    BatchSentimentRequest, 
    BatchSentimentResponse
)
from app.services.sentiment_analysis import sentiment_service

router = APIRouter()

@router.post("/analyze", response_model=SentimentResponse)
async def analyze_sentiment(request: SentimentRequest):
    """Analyze sentiment of a single text"""
    try:
        result = sentiment_service.analyze_sentiment(request.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing sentiment: {str(e)}")

@router.post("/analyze-batch", response_model=BatchSentimentResponse)
async def analyze_batch_sentiment(request: BatchSentimentRequest):
    """Analyze sentiment of multiple texts"""
    try:
        results = sentiment_service.analyze_batch_sentiment(request.texts)
        return BatchSentimentResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing batch sentiment: {str(e)}")

@router.post("/distribution")
async def get_sentiment_distribution(request: BatchSentimentRequest):
    """Get sentiment distribution for a collection of texts"""
    try:
        distribution = sentiment_service.get_sentiment_distribution(request.texts)
        return {
            "distribution": distribution,
            "total_texts": len(request.texts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating distribution: {str(e)}")

@router.get("/health")
async def sentiment_health_check():
    """Health check for sentiment analysis service"""
    try:
        # Test with a simple text
        test_result = sentiment_service.analyze_sentiment("This is a test.")
        return {
            "status": "healthy",
            "service": "sentiment_analysis",
            "test_result": test_result.sentiment
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service unhealthy: {str(e)}")