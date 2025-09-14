"""
Database initialization and sample data creation
"""
from sqlalchemy.orm import Session
from app.models.database import Product, Review, UserInteraction
from app.database.connection import engine, Base
import json

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

def create_sample_data(db: Session):
    """Create sample data for testing"""
    # Sample products
    sample_products = [
        {
            "name": "iPhone 15 Pro",
            "description": "Latest iPhone with advanced features",
            "category": "Electronics",
            "price": 999.99,
            "rating": 4.5,
            "brand": "Apple",
            "features": json.dumps({
                "screen_size": "6.1 inch",
                "storage": "128GB",
                "color": "Natural Titanium",
                "camera": "48MP"
            })
        },
        {
            "name": "Samsung Galaxy S24",
            "description": "Flagship Android smartphone",
            "category": "Electronics",
            "price": 899.99,
            "rating": 4.3,
            "brand": "Samsung",
            "features": json.dumps({
                "screen_size": "6.2 inch",
                "storage": "256GB",
                "color": "Phantom Black",
                "camera": "50MP"
            })
        },
        {
            "name": "Nike Air Max 90",
            "description": "Classic running shoes",
            "category": "Shoes",
            "price": 120.0,
            "rating": 4.4,
            "brand": "Nike",
            "features": json.dumps({
                "size": "US 10",
                "color": "White/Black",
                "material": "Leather/Mesh",
                "type": "Running"
            })
        },
        {
            "name": "MacBook Pro 16\"",
            "description": "Professional laptop for creators",
            "category": "Electronics",
            "price": 2499.99,
            "rating": 4.7,
            "brand": "Apple",
            "features": json.dumps({
                "screen_size": "16 inch",
                "processor": "M3 Pro",
                "memory": "18GB",
                "storage": "512GB SSD"
            })
        },
        {
            "name": "Adidas Ultraboost 22",
            "description": "Performance running shoes",
            "category": "Shoes",
            "price": 180.0,
            "rating": 4.2,
            "brand": "Adidas",
            "features": json.dumps({
                "size": "US 9.5",
                "color": "Core Black",
                "technology": "Boost",
                "type": "Running"
            })
        }
    ]
    
    # Create products
    created_products = []
    for product_data in sample_products:
        product = Product(**product_data)
        db.add(product)
        db.flush()  # Get the ID
        created_products.append(product)
    
    # Sample reviews
    sample_reviews = [
        {
            "product_id": created_products[0].id,
            "user_id": "user1",
            "rating": 5.0,
            "comment": "Excellent phone with amazing camera quality!",
            "sentiment_score": 0.8,
            "sentiment_label": "positive"
        },
        {
            "product_id": created_products[0].id,
            "user_id": "user2",
            "rating": 4.0,
            "comment": "Good phone but expensive",
            "sentiment_score": 0.2,
            "sentiment_label": "neutral"
        },
        {
            "product_id": created_products[1].id,
            "user_id": "user3",
            "rating": 4.5,
            "comment": "Great Android alternative to iPhone",
            "sentiment_score": 0.7,
            "sentiment_label": "positive"
        },
        {
            "product_id": created_products[2].id,
            "user_id": "user1",
            "rating": 4.0,
            "comment": "Comfortable shoes for daily wear",
            "sentiment_score": 0.5,
            "sentiment_label": "positive"
        },
        {
            "product_id": created_products[3].id,
            "user_id": "user4",
            "rating": 5.0,
            "comment": "Perfect laptop for professional work",
            "sentiment_score": 0.9,
            "sentiment_label": "positive"
        }
    ]
    
    # Create reviews
    for review_data in sample_reviews:
        review = Review(**review_data)
        db.add(review)
    
    # Sample user interactions
    sample_interactions = [
        {"user_id": "user1", "product_id": created_products[0].id, "interaction_type": "view", "value": 1.0},
        {"user_id": "user1", "product_id": created_products[0].id, "interaction_type": "click", "value": 1.0},
        {"user_id": "user1", "product_id": created_products[2].id, "interaction_type": "purchase", "value": 1.0},
        {"user_id": "user2", "product_id": created_products[0].id, "interaction_type": "view", "value": 1.0},
        {"user_id": "user2", "product_id": created_products[1].id, "interaction_type": "click", "value": 1.0},
        {"user_id": "user3", "product_id": created_products[1].id, "interaction_type": "purchase", "value": 1.0},
        {"user_id": "user4", "product_id": created_products[3].id, "interaction_type": "purchase", "value": 1.0},
    ]
    
    # Create interactions
    for interaction_data in sample_interactions:
        interaction = UserInteraction(**interaction_data)
        db.add(interaction)
    
    # Commit all changes
    db.commit()
    
    return len(created_products), len(sample_reviews), len(sample_interactions)