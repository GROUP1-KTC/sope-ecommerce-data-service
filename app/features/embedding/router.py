from fastapi import APIRouter, Request
from app.features.embedding.schemas import TextRequest

router = APIRouter(prefix="/embedding", tags=["Embedding"])


@router.post("/embed")
async def embed_text(request: Request, body: TextRequest):
    try:
        lazy_model = request.app.state.models.phobert
        embedding_model = await lazy_model.get()
        return {"embedding": embedding_model.embed(body.text)}
    except Exception as e:
        return {
            "error": "PhoBERTEmbedding model not available, database not ready",
            "details": str(e),
        }
