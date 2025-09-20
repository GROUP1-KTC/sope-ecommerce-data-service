from fastapi import APIRouter, Request

router = APIRouter(prefix="/recommend/content", tags=["Content-Based Recommendation"])


@router.get("/product/{product_id}")
async def recommend_content(request: Request, product_id: str, top_n: int = 5):
    try:
        lazy_model = getattr(request.app.state.models, "content_based", None)
        if lazy_model is None:
            return {"error": "ContentRecommender not initialized"}

        recommender_content = await lazy_model.get()
        recs = recommender_content.recommend(product_id, top_n=top_n)
        return {"product_id": product_id, "recommendations": recs}
    except Exception as e:
        return {
            "error": "ContentRecommender not available, database not ready",
            "details": str(e),
        }


@router.post("/")
async def update_similar_products(request: Request, top_n: int = 5):
    try:
        lazy_model = getattr(request.app.state.models, "content_based", None)
        if lazy_model is None:
            return {"error": "ContentRecommender not initialized"}

        recommender_content = await lazy_model.get()

        await recommender_content.update_similar_products_in_db(top_n=top_n)
        return {
            "status": "success",
            "message": "All product recommendations updated in DB.",
        }
    except Exception as e:
        return {
            "error": "ContentRecommender not available, database not ready",
            "details": str(e),
        }
