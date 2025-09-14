from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    category = Column(String, index=True)
    price = Column(Float)
    rating = Column(Float)
    brand = Column(String, index=True)
    features = Column(Text)  # JSON string of features
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    reviews = relationship("Review", back_populates="product")
    recommendations = relationship("Recommendation", back_populates="product")

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    user_id = Column(String, index=True)
    rating = Column(Float)
    comment = Column(Text)
    sentiment_score = Column(Float)  # -1 to 1, negative to positive
    sentiment_label = Column(String)  # 'positive', 'negative', 'neutral'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="reviews")

class Recommendation(Base):
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    score = Column(Float)
    recommendation_type = Column(String)  # 'collaborative', 'content_based', 'hybrid'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="recommendations")

class UserInteraction(Base):
    __tablename__ = "user_interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    interaction_type = Column(String)  # 'view', 'click', 'purchase', 'add_to_cart'
    value = Column(Float, default=1.0)  # interaction weight
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ProductSimilarity(Base):
    __tablename__ = "product_similarities"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id_1 = Column(Integer, ForeignKey("products.id"))
    product_id_2 = Column(Integer, ForeignKey("products.id"))
    similarity_score = Column(Float)
    similarity_type = Column(String)  # 'feature_based', 'behavior_based', 'content_based'
    created_at = Column(DateTime(timezone=True), server_default=func.now())