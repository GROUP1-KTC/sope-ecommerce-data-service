from contextlib import asynccontextmanager
from types import SimpleNamespace
from app.features.FPGrowth.service import FPGrowthRecommender
from app.features.detect_image.service import YOLOModel
from app.features.embedding.service import PhoBERTEmbedding
from app.features.search_by_image.service import SearchByImageService
from app.features.sentiment.service import SentimentAnalyzer
from app.features.user_cf.service import UserCFRecommender
from app.features.face_authentication.service import FaceService
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.configs.cors import setup_cors
from app.configs.settings import settings
from app.routes import api_router
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.features.content_based.service import ContentRecommender
from app.shares.layzy_model import LazyModel
from app.configs.mongo import collection

from app.configs.database import (
    cleanup_idle_connections,
    init_db_pool,
    close_db_pool,
    get_db_pool,
)


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # STARTUP
        await init_db_pool()

        pool = get_db_pool()

        app.state.models = SimpleNamespace(
            sentiment=LazyModel(
                lambda: SentimentAnalyzer.from_pretrained(
                    "reviews_emotion_model", labels=["negative", "neutral", "positive"]
                )
            ),
            phobert=LazyModel(
                lambda: PhoBERTEmbedding.from_pretrained("phobert_model")
            ),
            yolo=LazyModel(lambda: YOLOModel.from_pretrained("last.pt", min_conf=0.8)),
            fpgrowth=LazyModel(lambda: FPGrowthRecommender.from_pretrained(pool)),
            content_based=LazyModel(
                lambda: ContentRecommender.from_pretrained(
                    model_name="all-MiniLM-L6-v2", pool=pool
                )
            ),
            user_cf=LazyModel(lambda: UserCFRecommender.from_pretrained(pool)),
            face_auth=LazyModel(lambda: FaceService.from_pretrained(collection)),  
            search_by_image=LazyModel(lambda: SearchByImageService.from_pretrained()),      
        )
        yield
        # SHUTDOWN
        await cleanup_idle_connections(pool)
        await close_db_pool()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    setup_cors(app)

    app.include_router(api_router)

    # Root endpoint
    @app.get("/")
    def root():
        return {"message": "AI Service is running 🚀"}

    @app.exception_handler(StarletteHTTPException)
    async def custom_http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ):
        if exc.status_code == 404:
            return JSONResponse(
                status_code=404,
                content={
                    "error": "Not Found",
                    "message": f"Không tìm thấy đường dẫn {request.url.path}",
                    "docs": "/docs",
                },
            )
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.app_port,
        reload=settings.debug,
    )


# uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
# docker build -t your-dockerhub-username/sope-ai-service:latest .
