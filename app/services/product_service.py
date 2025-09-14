from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import json
from app.models.database import Product, Review
from app.models.schemas import ProductFilter, Product as ProductSchema, ProductSearchResponse

class ProductService:
    def __init__(self):
        pass
    
    def search_products(
        self, 
        db: Session, 
        filters: ProductFilter, 
        page: int = 1, 
        page_size: int = 20
    ) -> ProductSearchResponse:
        """Search and filter products based on criteria"""
        query = db.query(Product)
        
        # Apply filters
        conditions = []
        
        if filters.category:
            conditions.append(Product.category.ilike(f"%{filters.category}%"))
        
        if filters.brand:
            conditions.append(Product.brand.ilike(f"%{filters.brand}%"))
        
        if filters.min_price is not None:
            conditions.append(Product.price >= filters.min_price)
        
        if filters.max_price is not None:
            conditions.append(Product.price <= filters.max_price)
        
        if filters.min_rating is not None:
            conditions.append(Product.rating >= filters.min_rating)
        
        if filters.search_query:
            search_condition = or_(
                Product.name.ilike(f"%{filters.search_query}%"),
                Product.description.ilike(f"%{filters.search_query}%"),
                Product.brand.ilike(f"%{filters.search_query}%")
            )
            conditions.append(search_condition)
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        products = query.offset(offset).limit(page_size).all()
        
        return ProductSearchResponse(
            products=[ProductSchema.from_orm(p) for p in products],
            total=total,
            page=page,
            page_size=page_size
        )
    
    def get_product_by_id(self, db: Session, product_id: int) -> Optional[ProductSchema]:
        """Get a product by its ID"""
        product = db.query(Product).filter(Product.id == product_id).first()
        return ProductSchema.from_orm(product) if product else None
    
    def get_products_by_category(self, db: Session, category: str, limit: int = 20) -> List[ProductSchema]:
        """Get products by category"""
        products = db.query(Product).filter(
            Product.category.ilike(f"%{category}%")
        ).limit(limit).all()
        
        return [ProductSchema.from_orm(p) for p in products]
    
    def get_trending_products(self, db: Session, limit: int = 10) -> List[ProductSchema]:
        """Get trending products based on ratings and recent reviews"""
        # This is a simplified version - in a real system, you might consider
        # factors like recent sales, views, ratings, etc.
        subquery = db.query(
            Review.product_id,
            func.count(Review.id).label('review_count'),
            func.avg(Review.rating).label('avg_rating')
        ).filter(
            Review.created_at >= func.now() - func.interval('30 days')
        ).group_by(Review.product_id).subquery()
        
        products = db.query(Product).join(
            subquery, Product.id == subquery.c.product_id
        ).filter(
            subquery.c.review_count >= 5,
            subquery.c.avg_rating >= 4.0
        ).order_by(
            subquery.c.avg_rating.desc(),
            subquery.c.review_count.desc()
        ).limit(limit).all()
        
        return [ProductSchema.from_orm(p) for p in products]
    
    def get_products_by_price_range(
        self, 
        db: Session, 
        min_price: float, 
        max_price: float, 
        limit: int = 20
    ) -> List[ProductSchema]:
        """Get products within a specific price range"""
        products = db.query(Product).filter(
            Product.price.between(min_price, max_price)
        ).order_by(Product.rating.desc()).limit(limit).all()
        
        return [ProductSchema.from_orm(p) for p in products]
    
    def get_top_rated_products(self, db: Session, limit: int = 10) -> List[ProductSchema]:
        """Get top-rated products"""
        products = db.query(Product).filter(
            Product.rating.isnot(None)
        ).order_by(Product.rating.desc()).limit(limit).all()
        
        return [ProductSchema.from_orm(p) for p in products]
    
    def search_products_by_features(
        self, 
        db: Session, 
        required_features: Dict[str, Any], 
        limit: int = 20
    ) -> List[ProductSchema]:
        """Search products by specific features"""
        # This is a simplified implementation
        # In a real system, you might want to use a more sophisticated
        # feature matching algorithm or a dedicated search engine
        products = db.query(Product).filter(
            Product.features.isnot(None)
        ).all()
        
        matching_products = []
        for product in products:
            try:
                product_features = json.loads(product.features) if product.features else {}
                matches = all(
                    feature in product_features and 
                    str(product_features[feature]).lower() == str(value).lower()
                    for feature, value in required_features.items()
                )
                if matches:
                    matching_products.append(product)
                    if len(matching_products) >= limit:
                        break
            except (json.JSONDecodeError, TypeError):
                continue
        
        return [ProductSchema.from_orm(p) for p in matching_products]

# Global instance
product_service = ProductService()