from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from app.configs.settings import settings


def setup_cors(app: FastAPI):
    """Cấu hình CORS cho FastAPI app."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
