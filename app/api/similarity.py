from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from app.models.schemas import SimilarityRequest, SimilarityResponse
from app.services.similarity_service import similarity_service
from app.database.connection import get_db

router = APIRouter()

@router.post("/", response_model=SimilarityResponse)
async def get_similar_products(
    request: SimilarityRequest,
    db: Session = Depends(get_db)
):
    """Get similar products for a given product"""
    try:
        return similarity_service.get_similar_products(
            db,
            request.product_id,
            request.limit,
            request.similarity_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting similar products: {str(e)}")

@router.get("/product/{product_id}", response_model=SimilarityResponse)
async def get_product_similarities(
    product_id: int,
    limit: int = Query(10, ge=1, le=50),
    similarity_type: str = Query("content_based", regex="^(content_based|behavior_based|feature_based)$"),
    db: Session = Depends(get_db)
):
    """Get similar products for a specific product ID"""
    try:
        return similarity_service.get_similar_products(
            db,
            product_id,
            limit,
            similarity_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting product similarities: {str(e)}")

@router.post("/compute-similarities")
async def compute_similarities(
    similarity_type: str = Query("content_based", regex="^(content_based|behavior_based|feature_based)$"),
    db: Session = Depends(get_db)
):
    """Pre-compute and store similarities for all products"""
    try:
        stored_count = similarity_service.compute_and_store_similarities(db, similarity_type)
        return {
            "message": f"Computed and stored {stored_count} similarities",
            "similarity_type": similarity_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing similarities: {str(e)}")

@router.get("/health")
async def similarity_health_check():
    """Health check for similarity service"""
    return {
        "status": "healthy",
        "service": "similarity"
    }