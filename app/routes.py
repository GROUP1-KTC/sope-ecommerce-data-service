from fastapi import APIRouter
from app.features.detect_image.router import router as detect_image_router
from app.features.embedding.router import router as embedding_router
from app.features.FPGrowth.router import router as fpgrowth_router
from app.features.content_based.router import router as content_based_router
from app.features.user_cf.router import router as user_cf_router
from app.features.sentiment.router import router as sentiment_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(detect_image_router)
api_router.include_router(embedding_router)
api_router.include_router(fpgrowth_router)
api_router.include_router(content_based_router)
api_router.include_router(user_cf_router)
api_router.include_router(sentiment_router)
