from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import numpy as np
from collections import defaultdict
import json

from app.models.database import Product, Review, UserInteraction, Recommendation
from app.models.schemas import Product as ProductSchema, RecommendationResponse

class RecommendationService:
    def __init__(self):
        self.interaction_weights = {
            'view': 1.0,
            'click': 2.0,
            'add_to_cart': 3.0,
            'purchase': 5.0
        }
    
    def get_recommendations(
        self, 
        db: Session, 
        user_id: str, 
        limit: int = 10,
        recommendation_type: str = "hybrid"
    ) -> RecommendationResponse:
        """Get product recommendations for a user"""
        
        if recommendation_type == "collaborative":
            recommendations = self._collaborative_filtering(db, user_id, limit)
        elif recommendation_type == "content_based":
            recommendations = self._content_based_filtering(db, user_id, limit)
        else:  # hybrid
            recommendations = self._hybrid_filtering(db, user_id, limit)
        
        products = []
        scores = []
        
        for product_id, score in recommendations:
            product = db.query(Product).filter(Product.id == product_id).first()
            if product:
                products.append(ProductSchema.from_orm(product))
                scores.append(score)
        
        return RecommendationResponse(
            user_id=user_id,
            recommendations=products,
            scores=scores
        )
    
    def _collaborative_filtering(self, db: Session, user_id: str, limit: int) -> List[Tuple[int, float]]:
        """Collaborative filtering based on user interactions"""
        # Get user's interaction history
        user_interactions = db.query(UserInteraction).filter(
            UserInteraction.user_id == user_id
        ).all()
        
        if not user_interactions:
            return self._get_popular_products(db, limit)
        
        user_products = {i.product_id: i.value * self.interaction_weights.get(i.interaction_type, 1.0) 
                        for i in user_interactions}
        
        # Find similar users
        similar_users = self._find_similar_users(db, user_id, user_products)
        
        # Get recommendations based on similar users' preferences
        recommendations = defaultdict(float)
        
        for similar_user_id, similarity_score in similar_users[:50]:  # Top 50 similar users
            similar_user_interactions = db.query(UserInteraction).filter(
                UserInteraction.user_id == similar_user_id
            ).all()
            
            for interaction in similar_user_interactions:
                if interaction.product_id not in user_products:  # Don't recommend already interacted products
                    weight = self.interaction_weights.get(interaction.interaction_type, 1.0)
                    recommendations[interaction.product_id] += similarity_score * weight * interaction.value
        
        # Sort by score and return top recommendations
        sorted_recommendations = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
        return sorted_recommendations[:limit]
    
    def _content_based_filtering(self, db: Session, user_id: str, limit: int) -> List[Tuple[int, float]]:
        """Content-based filtering based on product features"""
        # Get user's interaction history
        user_interactions = db.query(UserInteraction).filter(
            UserInteraction.user_id == user_id
        ).all()
        
        if not user_interactions:
            return self._get_popular_products(db, limit)
        
        # Build user profile based on interacted products
        user_profile = self._build_user_profile(db, user_interactions)
        
        # Get all products not interacted with by the user
        interacted_product_ids = {i.product_id for i in user_interactions}
        all_products = db.query(Product).filter(
            ~Product.id.in_(interacted_product_ids)
        ).all()
        
        recommendations = []
        
        for product in all_products:
            similarity_score = self._calculate_content_similarity(product, user_profile)
            recommendations.append((product.id, similarity_score))
        
        # Sort by similarity score
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations[:limit]
    
    def _hybrid_filtering(self, db: Session, user_id: str, limit: int) -> List[Tuple[int, float]]:
        """Hybrid approach combining collaborative and content-based filtering"""
        collaborative_recs = self._collaborative_filtering(db, user_id, limit * 2)
        content_recs = self._content_based_filtering(db, user_id, limit * 2)
        
        # Combine recommendations with weights
        combined_scores = defaultdict(float)
        
        # Weight collaborative filtering more heavily
        for product_id, score in collaborative_recs:
            combined_scores[product_id] += 0.7 * score
        
        # Add content-based scores
        for product_id, score in content_recs:
            combined_scores[product_id] += 0.3 * score
        
        # Sort and return top recommendations
        sorted_recommendations = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_recommendations[:limit]
    
    def _find_similar_users(self, db: Session, user_id: str, user_products: Dict[int, float]) -> List[Tuple[str, float]]:
        """Find users similar to the given user based on interactions"""
        all_users = db.query(UserInteraction.user_id).distinct().all()
        similarities = []
        
        for (other_user_id,) in all_users:
            if other_user_id == user_id:
                continue
            
            other_user_interactions = db.query(UserInteraction).filter(
                UserInteraction.user_id == other_user_id
            ).all()
            
            other_user_products = {i.product_id: i.value * self.interaction_weights.get(i.interaction_type, 1.0) 
                                 for i in other_user_interactions}
            
            similarity = self._calculate_user_similarity(user_products, other_user_products)
            if similarity > 0:
                similarities.append((other_user_id, similarity))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities
    
    def _calculate_user_similarity(self, user1_products: Dict[int, float], user2_products: Dict[int, float]) -> float:
        """Calculate cosine similarity between two users"""
        common_products = set(user1_products.keys()) & set(user2_products.keys())
        
        if not common_products:
            return 0.0
        
        # Calculate cosine similarity
        dot_product = sum(user1_products[p] * user2_products[p] for p in common_products)
        norm1 = np.sqrt(sum(v**2 for v in user1_products.values()))
        norm2 = np.sqrt(sum(v**2 for v in user2_products.values()))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _build_user_profile(self, db: Session, user_interactions: List[UserInteraction]) -> Dict[str, float]:
        """Build user profile based on interaction history"""
        profile = defaultdict(float)
        total_weight = 0
        
        for interaction in user_interactions:
            product = db.query(Product).filter(Product.id == interaction.product_id).first()
            if product:
                weight = self.interaction_weights.get(interaction.interaction_type, 1.0) * interaction.value
                total_weight += weight
                
                # Add category preference
                if product.category:
                    profile[f"category_{product.category}"] += weight
                
                # Add brand preference
                if product.brand:
                    profile[f"brand_{product.brand}"] += weight
                
                # Add price range preference
                if product.price:
                    price_range = self._get_price_range(product.price)
                    profile[f"price_range_{price_range}"] += weight
        
        # Normalize profile
        if total_weight > 0:
            for key in profile:
                profile[key] /= total_weight
        
        return dict(profile)
    
    def _calculate_content_similarity(self, product: Product, user_profile: Dict[str, float]) -> float:
        """Calculate similarity between product and user profile"""
        score = 0.0
        
        # Category similarity
        if product.category:
            category_key = f"category_{product.category}"
            score += user_profile.get(category_key, 0.0) * 0.4
        
        # Brand similarity
        if product.brand:
            brand_key = f"brand_{product.brand}"
            score += user_profile.get(brand_key, 0.0) * 0.3
        
        # Price range similarity
        if product.price:
            price_range = self._get_price_range(product.price)
            price_key = f"price_range_{price_range}"
            score += user_profile.get(price_key, 0.0) * 0.3
        
        return score
    
    def _get_price_range(self, price: float) -> str:
        """Categorize price into ranges"""
        if price < 50:
            return "low"
        elif price < 200:
            return "medium"
        elif price < 500:
            return "high"
        else:
            return "premium"
    
    def _get_popular_products(self, db: Session, limit: int) -> List[Tuple[int, float]]:
        """Get popular products as fallback recommendations"""
        popular_products = db.query(
            Product.id,
            func.coalesce(Product.rating, 0.0).label('rating')
        ).filter(
            Product.rating.isnot(None)
        ).order_by(desc('rating')).limit(limit).all()
        
        return [(p.id, p.rating) for p in popular_products]

# Global instance
recommendation_service = RecommendationService()