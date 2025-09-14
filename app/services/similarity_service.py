from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import numpy as np
import json
from collections import defaultdict

from app.models.database import Product, ProductSimilarity, UserInteraction
from app.models.schemas import Product as ProductSchema, SimilarityResponse

class SimilarityService:
    def __init__(self):
        self.feature_weights = {
            'category': 0.3,
            'brand': 0.2,
            'price': 0.2,
            'features': 0.3
        }
    
    def get_similar_products(
        self, 
        db: Session, 
        product_id: int, 
        limit: int = 10,
        similarity_type: str = "content_based"
    ) -> SimilarityResponse:
        """Get similar products for a given product"""
        
        # First check if we have pre-computed similarities
        cached_similarities = db.query(ProductSimilarity).filter(
            ProductSimilarity.product_id_1 == product_id,
            ProductSimilarity.similarity_type == similarity_type
        ).order_by(ProductSimilarity.similarity_score.desc()).limit(limit).all()
        
        if cached_similarities:
            similar_product_ids = [s.product_id_2 for s in cached_similarities]
            similarity_scores = [s.similarity_score for s in cached_similarities]
        else:
            # Compute similarities on the fly
            if similarity_type == "content_based":
                similar_product_ids, similarity_scores = self._content_based_similarity(db, product_id, limit)
            elif similarity_type == "behavior_based":
                similar_product_ids, similarity_scores = self._behavior_based_similarity(db, product_id, limit)
            else:  # feature_based
                similar_product_ids, similarity_scores = self._feature_based_similarity(db, product_id, limit)
        
        # Get product objects
        similar_products = []
        for pid in similar_product_ids:
            product = db.query(Product).filter(Product.id == pid).first()
            if product:
                similar_products.append(ProductSchema.from_orm(product))
        
        return SimilarityResponse(
            product_id=product_id,
            similar_products=similar_products,
            similarity_scores=similarity_scores
        )
    
    def _content_based_similarity(self, db: Session, product_id: int, limit: int) -> Tuple[List[int], List[float]]:
        """Find similar products based on content features"""
        target_product = db.query(Product).filter(Product.id == product_id).first()
        if not target_product:
            return [], []
        
        # Get all other products
        other_products = db.query(Product).filter(Product.id != product_id).all()
        
        similarities = []
        for product in other_products:
            similarity_score = self._calculate_content_similarity(target_product, product)
            similarities.append((product.id, similarity_score))
        
        # Sort by similarity score and return top results
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_similarities = similarities[:limit]
        
        product_ids = [s[0] for s in top_similarities]
        scores = [s[1] for s in top_similarities]
        
        return product_ids, scores
    
    def _behavior_based_similarity(self, db: Session, product_id: int, limit: int) -> Tuple[List[int], List[float]]:
        """Find similar products based on user behavior patterns"""
        # Get users who interacted with the target product
        target_users = db.query(UserInteraction.user_id).filter(
            UserInteraction.product_id == product_id
        ).distinct().all()
        
        target_user_ids = [u[0] for u in target_users]
        
        if not target_user_ids:
            return [], []
        
        # Find other products these users interacted with
        other_product_interactions = db.query(
            UserInteraction.product_id,
            func.count(UserInteraction.user_id).label('common_users'),
            func.avg(UserInteraction.value).label('avg_interaction')
        ).filter(
            UserInteraction.user_id.in_(target_user_ids),
            UserInteraction.product_id != product_id
        ).group_by(UserInteraction.product_id).all()
        
        # Calculate similarity scores based on common users and interaction strength
        total_target_users = len(target_user_ids)
        similarities = []
        
        for interaction in other_product_interactions:
            # Jaccard similarity with interaction weight
            jaccard_score = interaction.common_users / total_target_users
            interaction_weight = min(interaction.avg_interaction, 5.0) / 5.0  # Normalize to 0-1
            similarity_score = jaccard_score * interaction_weight
            
            similarities.append((interaction.product_id, similarity_score))
        
        # Sort and return top results
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_similarities = similarities[:limit]
        
        product_ids = [s[0] for s in top_similarities]
        scores = [s[1] for s in top_similarities]
        
        return product_ids, scores
    
    def _feature_based_similarity(self, db: Session, product_id: int, limit: int) -> Tuple[List[int], List[float]]:
        """Find similar products based on explicit features"""
        target_product = db.query(Product).filter(Product.id == product_id).first()
        if not target_product:
            return [], []
        
        try:
            target_features = json.loads(target_product.features) if target_product.features else {}
        except (json.JSONDecodeError, TypeError):
            target_features = {}
        
        # Get products with features
        other_products = db.query(Product).filter(
            Product.id != product_id,
            Product.features.isnot(None)
        ).all()
        
        similarities = []
        for product in other_products:
            try:
                product_features = json.loads(product.features) if product.features else {}
                similarity_score = self._calculate_feature_similarity(target_features, product_features)
                similarities.append((product.id, similarity_score))
            except (json.JSONDecodeError, TypeError):
                continue
        
        # Sort and return top results
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_similarities = similarities[:limit]
        
        product_ids = [s[0] for s in top_similarities]
        scores = [s[1] for s in top_similarities]
        
        return product_ids, scores
    
    def _calculate_content_similarity(self, product1: Product, product2: Product) -> float:
        """Calculate similarity between two products based on all content features"""
        similarity_score = 0.0
        
        # Category similarity
        if product1.category and product2.category:
            if product1.category.lower() == product2.category.lower():
                similarity_score += self.feature_weights['category']
        
        # Brand similarity
        if product1.brand and product2.brand:
            if product1.brand.lower() == product2.brand.lower():
                similarity_score += self.feature_weights['brand']
        
        # Price similarity (normalized)
        if product1.price and product2.price:
            price_diff = abs(product1.price - product2.price)
            max_price = max(product1.price, product2.price)
            price_similarity = 1 - (price_diff / max_price) if max_price > 0 else 1
            similarity_score += self.feature_weights['price'] * price_similarity
        
        # Feature similarity
        try:
            features1 = json.loads(product1.features) if product1.features else {}
            features2 = json.loads(product2.features) if product2.features else {}
            feature_similarity = self._calculate_feature_similarity(features1, features2)
            similarity_score += self.feature_weights['features'] * feature_similarity
        except (json.JSONDecodeError, TypeError):
            pass
        
        return similarity_score
    
    def _calculate_feature_similarity(self, features1: Dict, features2: Dict) -> float:
        """Calculate similarity between two feature dictionaries"""
        if not features1 or not features2:
            return 0.0
        
        # Get all unique keys
        all_keys = set(features1.keys()) | set(features2.keys())
        if not all_keys:
            return 0.0
        
        # Calculate Jaccard similarity for matching features
        matching_features = 0
        for key in all_keys:
            if key in features1 and key in features2:
                value1 = str(features1[key]).lower()
                value2 = str(features2[key]).lower()
                if value1 == value2:
                    matching_features += 1
        
        return matching_features / len(all_keys)
    
    def compute_and_store_similarities(self, db: Session, similarity_type: str = "content_based") -> int:
        """Pre-compute and store similarities for all products"""
        products = db.query(Product).all()
        stored_count = 0
        
        for i, product1 in enumerate(products):
            for j, product2 in enumerate(products[i+1:], i+1):
                if similarity_type == "content_based":
                    similarity_score = self._calculate_content_similarity(product1, product2)
                elif similarity_type == "behavior_based":
                    # For batch computation, we'll use a simplified version
                    similarity_score = self._calculate_simple_behavior_similarity(db, product1.id, product2.id)
                else:  # feature_based
                    try:
                        features1 = json.loads(product1.features) if product1.features else {}
                        features2 = json.loads(product2.features) if product2.features else {}
                        similarity_score = self._calculate_feature_similarity(features1, features2)
                    except (json.JSONDecodeError, TypeError):
                        similarity_score = 0.0
                
                if similarity_score > 0.1:  # Only store meaningful similarities
                    # Store both directions
                    similarity1 = ProductSimilarity(
                        product_id_1=product1.id,
                        product_id_2=product2.id,
                        similarity_score=similarity_score,
                        similarity_type=similarity_type
                    )
                    similarity2 = ProductSimilarity(
                        product_id_1=product2.id,
                        product_id_2=product1.id,
                        similarity_score=similarity_score,
                        similarity_type=similarity_type
                    )
                    
                    db.add(similarity1)
                    db.add(similarity2)
                    stored_count += 2
        
        db.commit()
        return stored_count
    
    def _calculate_simple_behavior_similarity(self, db: Session, product_id1: int, product_id2: int) -> float:
        """Simple behavior similarity for batch computation"""
        users1 = set(u[0] for u in db.query(UserInteraction.user_id).filter(
            UserInteraction.product_id == product_id1
        ).distinct().all())
        
        users2 = set(u[0] for u in db.query(UserInteraction.user_id).filter(
            UserInteraction.product_id == product_id2
        ).distinct().all())
        
        if not users1 or not users2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(users1 & users2)
        union = len(users1 | users2)
        
        return intersection / union if union > 0 else 0.0

# Global instance
similarity_service = SimilarityService()