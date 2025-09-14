from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.schemas import (
    ProductFilter, 
    ProductSearchResponse, 
    Product as ProductSchema
)
from app.services.product_service import product_service
from app.database.connection import get_db

router = APIRouter()

@router.post("/search", response_model=ProductSearchResponse)
async def search_products(
    filters: ProductFilter,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search and filter products"""
    try:
        return product_service.search_products(db, filters, page, page_size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching products: {str(e)}")

@router.get("/{product_id}", response_model=ProductSchema)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a product by ID"""
    try:
        product = product_service.get_product_by_id(db, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving product: {str(e)}")

@router.get("/category/{category}", response_model=List[ProductSchema])
async def get_products_by_category(
    category: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get products by category"""
    try:
        return product_service.get_products_by_category(db, category, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving products by category: {str(e)}")

@router.get("/trending/", response_model=List[ProductSchema])
async def get_trending_products(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get trending products"""
    try:
        return product_service.get_trending_products(db, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving trending products: {str(e)}")

@router.get("/price-range/", response_model=List[ProductSchema])
async def get_products_by_price_range(
    min_price: float = Query(..., ge=0),
    max_price: float = Query(..., ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get products within a price range"""
    try:
        if min_price > max_price:
            raise HTTPException(status_code=400, detail="min_price must be less than or equal to max_price")
        return product_service.get_products_by_price_range(db, min_price, max_price, limit)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving products by price range: {str(e)}")

@router.get("/top-rated/", response_model=List[ProductSchema])
async def get_top_rated_products(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get top-rated products"""
    try:
        return product_service.get_top_rated_products(db, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving top-rated products: {str(e)}")

@router.post("/search-by-features", response_model=List[ProductSchema])
async def search_products_by_features(
    features: dict,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search products by specific features"""
    try:
        return product_service.search_products_by_features(db, features, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching products by features: {str(e)}")

@router.get("/health")
async def products_health_check():
    """Health check for products service"""
    return {
        "status": "healthy",
        "service": "products"
    }