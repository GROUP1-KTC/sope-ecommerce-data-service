from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.schemas import (
    HighBenefitAnalysisRequest,
    HighBenefitAnalysisResponse,
    UserInteractionRequest,
    AnalyticsResponse
)
from app.services.analytics_service import analytics_service
from app.database.connection import get_db

router = APIRouter()

@router.post("/high-benefit", response_model=HighBenefitAnalysisResponse)
async def analyze_high_benefit_products(
    request: HighBenefitAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Analyze and return high-benefit products"""
    try:
        return analytics_service.analyze_high_benefit_products(
            db,
            request.user_id,
            request.category,
            request.limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing high-benefit products: {str(e)}")

@router.get("/high-benefit/", response_model=HighBenefitAnalysisResponse)
async def get_high_benefit_products(
    user_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get high-benefit products with query parameters"""
    try:
        return analytics_service.analyze_high_benefit_products(
            db,
            user_id,
            category,
            limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting high-benefit products: {str(e)}")

@router.get("/category/{category}", response_model=List[AnalyticsResponse])
async def get_category_analytics(
    category: str,
    db: Session = Depends(get_db)
):
    """Get analytics for a specific category"""
    try:
        return analytics_service.get_category_analytics(db, category)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting category analytics: {str(e)}")

@router.post("/user-interaction")
async def record_user_interaction(
    request: UserInteractionRequest,
    db: Session = Depends(get_db)
):
    """Record a user interaction for analytics"""
    try:
        from app.models.database import UserInteraction
        from datetime import datetime
        
        interaction = UserInteraction(
            user_id=request.user_id,
            product_id=request.product_id,
            interaction_type=request.interaction_type,
            value=request.value,
            created_at=datetime.utcnow()
        )
        
        db.add(interaction)
        db.commit()
        
        return {
            "message": "Interaction recorded successfully",
            "interaction_type": request.interaction_type,
            "user_id": request.user_id,
            "product_id": request.product_id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error recording interaction: {str(e)}")

@router.get("/user/{user_id}/profile")
async def get_user_analytics_profile(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get analytics profile for a specific user"""
    try:
        from app.models.database import UserInteraction, Product
        from sqlalchemy import func
        from collections import defaultdict
        
        # Get user interactions
        interactions = db.query(UserInteraction).filter(
            UserInteraction.user_id == user_id
        ).all()
        
        if not interactions:
            return {
                "user_id": user_id,
                "total_interactions": 0,
                "categories": {},
                "brands": {},
                "interaction_types": {}
            }
        
        # Analyze interactions
        categories = defaultdict(int)
        brands = defaultdict(int)
        interaction_types = defaultdict(int)
        
        for interaction in interactions:
            product = db.query(Product).filter(Product.id == interaction.product_id).first()
            if product:
                if product.category:
                    categories[product.category] += 1
                if product.brand:
                    brands[product.brand] += 1
            interaction_types[interaction.interaction_type] += 1
        
        return {
            "user_id": user_id,
            "total_interactions": len(interactions),
            "categories": dict(categories),
            "brands": dict(brands),
            "interaction_types": dict(interaction_types)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user profile: {str(e)}")

@router.get("/health")
async def analytics_health_check():
    """Health check for analytics service"""
    return {
        "status": "healthy",
        "service": "analytics"
    }