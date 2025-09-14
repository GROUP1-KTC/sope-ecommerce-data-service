from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

# Sentiment Analysis Models
class SentimentRequest(BaseModel):
    text: str

class SentimentResponse(BaseModel):
    text: str
    sentiment: str  # 'positive', 'negative', 'neutral'
    confidence: float
    score: float  # -1 to 1

class BatchSentimentRequest(BaseModel):
    texts: List[str]

class BatchSentimentResponse(BaseModel):
    results: List[SentimentResponse]

# Product Models
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    price: float
    brand: Optional[str] = None
    features: Optional[Dict[str, Any]] = None

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    rating: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ProductFilter(BaseModel):
    category: Optional[str] = None
    brand: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_rating: Optional[float] = None
    search_query: Optional[str] = None

class ProductSearchResponse(BaseModel):
    products: List[Product]
    total: int
    page: int
    page_size: int

# Review Models
class ReviewBase(BaseModel):
    product_id: int
    user_id: str
    rating: float
    comment: Optional[str] = None

class ReviewCreate(ReviewBase):
    pass

class Review(ReviewBase):
    id: int
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Recommendation Models
class RecommendationRequest(BaseModel):
    user_id: str
    limit: Optional[int] = 10
    recommendation_type: Optional[str] = "hybrid"  # 'collaborative', 'content_based', 'hybrid'

class RecommendationResponse(BaseModel):
    user_id: str
    recommendations: List[Product]
    scores: List[float]

# Similarity Models
class SimilarityRequest(BaseModel):
    product_id: int
    limit: Optional[int] = 10
    similarity_type: Optional[str] = "content_based"

class SimilarityResponse(BaseModel):
    product_id: int
    similar_products: List[Product]
    similarity_scores: List[float]

# Analytics Models
class UserInteractionRequest(BaseModel):
    user_id: str
    product_id: int
    interaction_type: str  # 'view', 'click', 'purchase', 'add_to_cart'
    value: Optional[float] = 1.0

class AnalyticsResponse(BaseModel):
    metric: str
    value: Any
    timestamp: datetime

class HighBenefitAnalysisRequest(BaseModel):
    user_id: Optional[str] = None
    category: Optional[str] = None
    limit: Optional[int] = 10

class HighBenefitProduct(BaseModel):
    product: Product
    benefit_score: float
    factors: Dict[str, float]  # breakdown of benefit factors

class HighBenefitAnalysisResponse(BaseModel):
    products: List[HighBenefitProduct]
    analysis_type: str
    timestamp: datetime