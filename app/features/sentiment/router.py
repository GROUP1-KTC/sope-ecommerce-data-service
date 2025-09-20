from app.features.sentiment.schemas import TextRequest
from fastapi import APIRouter, Request


router = APIRouter(prefix="/sentiment", tags=["Sentiment"])


@router.post("/")
async def analyze_sentiment(request: Request, body: TextRequest):
    lazy_model = request.app.state.models.sentiment
    sentiment_model = await lazy_model.get()
    prediction = sentiment_model.predict(body.text)
    return {"text": body.text, "prediction": prediction}
