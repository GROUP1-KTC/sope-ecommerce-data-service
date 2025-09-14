from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from app.models.schemas import RecommendationRequest, RecommendationResponse
from app.services.recommendation_service import recommendation_service
from app.database.connection import get_db

router = APIRouter()

@router.post("/", response_model=RecommendationResponse)
async def get_recommendations(
    request: RecommendationRequest,
    db: Session = Depends(get_db)
):
    """Get product recommendations for a user"""
    try:
        return recommendation_service.get_recommendations(
            db, 
            request.user_id, 
            request.limit, 
            request.recommendation_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")

@router.get("/user/{user_id}", response_model=RecommendationResponse)
async def get_user_recommendations(
    user_id: str,
    limit: int = Query(10, ge=1, le=50),
    recommendation_type: str = Query("hybrid", regex="^(collaborative|content_based|hybrid)$"),
    db: Session = Depends(get_db)
):
    """Get recommendations for a specific user"""
    try:
        return recommendation_service.get_recommendations(
            db, 
            user_id, 
            limit, 
            recommendation_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user recommendations: {str(e)}")

@router.get("/health")
async def recommendations_health_check():
    """Health check for recommendations service"""
    return {
        "status": "healthy",
        "service": "recommendations"
    }