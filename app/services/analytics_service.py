from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from datetime import datetime, timedelta
import numpy as np

from app.models.database import Product, Review, UserInteraction
from app.models.schemas import (
    Product as ProductSchema, 
    HighBenefitAnalysisResponse, 
    HighBenefitProduct,
    AnalyticsResponse
)

class AnalyticsService:
    def __init__(self):
        self.interaction_weights = {
            'view': 1.0,
            'click': 2.0,
            'add_to_cart': 3.0,
            'purchase': 5.0
        }
        
        self.benefit_factors = {
            'rating': 0.25,
            'review_sentiment': 0.2,
            'popularity': 0.2,
            'engagement': 0.15,
            'price_value': 0.1,
            'trend': 0.1
        }
    
    def analyze_high_benefit_products(
        self, 
        db: Session, 
        user_id: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 10
    ) -> HighBenefitAnalysisResponse:
        """Analyze and return high-benefit products based on multiple factors"""
        
        # Base query
        query = db.query(Product)
        
        # Apply filters
        if category:
            query = query.filter(Product.category.ilike(f"%{category}%"))
        
        products = query.all()
        
        # Calculate benefit scores for each product
        product_benefits = []
        for product in products:
            benefit_score, factors = self._calculate_benefit_score(db, product, user_id)
            if benefit_score > 0:
                product_benefits.append(HighBenefitProduct(
                    product=ProductSchema.from_orm(product),
                    benefit_score=benefit_score,
                    factors=factors
                ))
        
        # Sort by benefit score
        product_benefits.sort(key=lambda x: x.benefit_score, reverse=True)
        
        analysis_type = "personalized" if user_id else "general"
        if category:
            analysis_type += f"_category_{category}"
        
        return HighBenefitAnalysisResponse(
            products=product_benefits[:limit],
            analysis_type=analysis_type,
            timestamp=datetime.utcnow()
        )
    
    def _calculate_benefit_score(self, db: Session, product: Product, user_id: Optional[str] = None) -> tuple[float, Dict[str, float]]:
        """Calculate comprehensive benefit score for a product"""
        factors = {}
        
        # 1. Rating factor
        rating_score = (product.rating or 0) / 5.0
        factors['rating'] = rating_score
        
        # 2. Review sentiment factor
        sentiment_score = self._calculate_sentiment_score(db, product.id)
        factors['review_sentiment'] = sentiment_score
        
        # 3. Popularity factor
        popularity_score = self._calculate_popularity_score(db, product.id)
        factors['popularity'] = popularity_score
        
        # 4. Engagement factor
        engagement_score = self._calculate_engagement_score(db, product.id)
        factors['engagement'] = engagement_score
        
        # 5. Price value factor
        price_value_score = self._calculate_price_value_score(db, product)
        factors['price_value'] = price_value_score
        
        # 6. Trend factor
        trend_score = self._calculate_trend_score(db, product.id)
        factors['trend'] = trend_score
        
        # Calculate weighted benefit score
        benefit_score = sum(
            factors[factor] * weight 
            for factor, weight in self.benefit_factors.items()
        )
        
        # Apply personalization if user_id is provided
        if user_id:
            personalization_boost = self._calculate_personalization_boost(db, product, user_id)
            benefit_score *= (1 + personalization_boost)
            factors['personalization'] = personalization_boost
        
        return benefit_score, factors
    
    def _calculate_sentiment_score(self, db: Session, product_id: int) -> float:
        """Calculate average sentiment score from reviews"""
        reviews = db.query(Review).filter(
            Review.product_id == product_id,
            Review.sentiment_score.isnot(None)
        ).all()
        
        if not reviews:
            return 0.5  # Neutral score if no reviews
        
        avg_sentiment = sum(r.sentiment_score for r in reviews) / len(reviews)
        # Convert from [-1, 1] to [0, 1]
        return (avg_sentiment + 1) / 2
    
    def _calculate_popularity_score(self, db: Session, product_id: int) -> float:
        """Calculate popularity based on interactions and reviews"""
        # Count total interactions
        interaction_count = db.query(func.count(UserInteraction.id)).filter(
            UserInteraction.product_id == product_id
        ).scalar() or 0
        
        # Count reviews
        review_count = db.query(func.count(Review.id)).filter(
            Review.product_id == product_id
        ).scalar() or 0
        
        # Combine counts with logarithmic scaling to prevent dominance
        total_activity = interaction_count + (review_count * 2)  # Reviews weighted more
        
        # Apply log scaling and normalize
        if total_activity > 0:
            log_activity = np.log10(total_activity + 1)
            # Normalize to 0-1 range (assuming max log activity is around 3-4)
            return min(log_activity / 4.0, 1.0)
        
        return 0.0
    
    def _calculate_engagement_score(self, db: Session, product_id: int) -> float:
        """Calculate engagement quality based on interaction types"""
        interactions = db.query(UserInteraction).filter(
            UserInteraction.product_id == product_id
        ).all()
        
        if not interactions:
            return 0.0
        
        # Calculate weighted engagement
        total_weight = 0
        for interaction in interactions:
            weight = self.interaction_weights.get(interaction.interaction_type, 1.0)
            total_weight += weight * interaction.value
        
        # Normalize by number of unique users
        unique_users = len(set(i.user_id for i in interactions))
        if unique_users > 0:
            avg_engagement = total_weight / unique_users
            # Normalize to 0-1 range (assuming max average engagement is around 10)
            return min(avg_engagement / 10.0, 1.0)
        
        return 0.0
    
    def _calculate_price_value_score(self, db: Session, product: Product) -> float:
        """Calculate price-to-value ratio within category"""
        if not product.price or not product.category:
            return 0.5
        
        # Get average price and rating in the same category
        category_stats = db.query(
            func.avg(Product.price).label('avg_price'),
            func.avg(Product.rating).label('avg_rating')
        ).filter(
            Product.category == product.category,
            Product.price.isnot(None),
            Product.rating.isnot(None)
        ).first()
        
        if not category_stats.avg_price or not category_stats.avg_rating:
            return 0.5
        
        # Calculate value score based on price vs rating compared to category average
        price_ratio = product.price / category_stats.avg_price
        rating_ratio = (product.rating or 0) / category_stats.avg_rating
        
        # Good value = high rating, low price relative to category
        if price_ratio > 0:
            value_score = rating_ratio / price_ratio
            # Normalize and cap at 1.0
            return min(value_score / 2.0, 1.0)
        
        return 0.5
    
    def _calculate_trend_score(self, db: Session, product_id: int) -> float:
        """Calculate trending score based on recent activity"""
        # Get interactions from last 30 days
        recent_date = datetime.utcnow() - timedelta(days=30)
        
        recent_interactions = db.query(func.count(UserInteraction.id)).filter(
            UserInteraction.product_id == product_id,
            UserInteraction.created_at >= recent_date
        ).scalar() or 0
        
        # Get interactions from previous 30 days for comparison
        older_date = recent_date - timedelta(days=30)
        
        older_interactions = db.query(func.count(UserInteraction.id)).filter(
            UserInteraction.product_id == product_id,
            UserInteraction.created_at >= older_date,
            UserInteraction.created_at < recent_date
        ).scalar() or 0
        
        # Calculate trend (growth rate)
        if older_interactions > 0:
            growth_rate = (recent_interactions - older_interactions) / older_interactions
            # Normalize growth rate to 0-1 range
            return max(0, min(1, (growth_rate + 1) / 2))
        elif recent_interactions > 0:
            return 0.8  # New product with activity
        
        return 0.1  # No recent activity
    
    def _calculate_personalization_boost(self, db: Session, product: Product, user_id: str) -> float:
        """Calculate personalization boost based on user preferences"""
        user_interactions = db.query(UserInteraction).filter(
            UserInteraction.user_id == user_id
        ).all()
        
        if not user_interactions:
            return 0.0
        
        boost = 0.0
        
        # Category preference boost
        user_categories = {}
        for interaction in user_interactions:
            product_info = db.query(Product).filter(Product.id == interaction.product_id).first()
            if product_info and product_info.category:
                category = product_info.category
                weight = self.interaction_weights.get(interaction.interaction_type, 1.0)
                user_categories[category] = user_categories.get(category, 0) + weight
        
        if product.category in user_categories:
            total_category_weight = sum(user_categories.values())
            category_preference = user_categories[product.category] / total_category_weight
            boost += category_preference * 0.3
        
        # Brand preference boost
        user_brands = {}
        for interaction in user_interactions:
            product_info = db.query(Product).filter(Product.id == interaction.product_id).first()
            if product_info and product_info.brand:
                brand = product_info.brand
                weight = self.interaction_weights.get(interaction.interaction_type, 1.0)
                user_brands[brand] = user_brands.get(brand, 0) + weight
        
        if product.brand and product.brand in user_brands:
            total_brand_weight = sum(user_brands.values())
            brand_preference = user_brands[product.brand] / total_brand_weight
            boost += brand_preference * 0.2
        
        return min(boost, 0.5)  # Cap boost at 50%
    
    def get_category_analytics(self, db: Session, category: str) -> List[AnalyticsResponse]:
        """Get analytics for a specific category"""
        results = []
        
        # Average rating in category
        avg_rating = db.query(func.avg(Product.rating)).filter(
            Product.category.ilike(f"%{category}%"),
            Product.rating.isnot(None)
        ).scalar()
        
        if avg_rating:
            results.append(AnalyticsResponse(
                metric="average_rating",
                value=round(avg_rating, 2),
                timestamp=datetime.utcnow()
            ))
        
        # Total products in category
        product_count = db.query(func.count(Product.id)).filter(
            Product.category.ilike(f"%{category}%")
        ).scalar()
        
        results.append(AnalyticsResponse(
            metric="product_count",
            value=product_count,
            timestamp=datetime.utcnow()
        ))
        
        # Average price in category
        avg_price = db.query(func.avg(Product.price)).filter(
            Product.category.ilike(f"%{category}%"),
            Product.price.isnot(None)
        ).scalar()
        
        if avg_price:
            results.append(AnalyticsResponse(
                metric="average_price",
                value=round(avg_price, 2),
                timestamp=datetime.utcnow()
            ))
        
        return results

# Global instance
analytics_service = AnalyticsService()