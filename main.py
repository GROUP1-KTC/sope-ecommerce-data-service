from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import sentiment, products, recommendations, similarity, analytics
from app.core.config import settings

app = FastAPI(
    title="SOPE E-commerce Data Service",
    description="Comprehensive data processing service for e-commerce including sentiment analysis, product filtering, recommendations, and analytics",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sentiment.router, prefix="/api/v1/sentiment", tags=["sentiment"])
app.include_router(products.router, prefix="/api/v1/products", tags=["products"])
app.include_router(recommendations.router, prefix="/api/v1/recommendations", tags=["recommendations"])
app.include_router(similarity.router, prefix="/api/v1/similarity", tags=["similarity"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])

@app.get("/")
async def root():
    return {"message": "SOPE E-commerce Data Service", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)