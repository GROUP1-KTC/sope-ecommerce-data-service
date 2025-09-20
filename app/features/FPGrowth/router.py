from fastapi import APIRouter, Request

router = APIRouter(prefix="/recommend/fpgrowth", tags=["FPGrowth Recommendation"])


@router.get("/product/{product_id}")
async def recommend_fpg(request: Request, product_id: str, top_n: int = 5):
    try:
        lazy_model = request.app.state.models.fpgrowth
        if lazy_model is None:
            return {"error": "FPGrowthRecommender model not initialized"}
        recommender_fpg = await lazy_model.get()
        recs = await recommender_fpg.recommend(product_id, top_n=top_n)
        return {"product_id": product_id, "recommendations": recs}
    except Exception as e:
        return {
            "error": "FPGrowthRecommender not available, database not ready",
            "details": str(e),
        }


@router.post("/")
async def update_suggested_products(
    request: Request,
    top_n: int = 5,
    min_support: float = 0.05,
    min_confidence: float = 0.2,
):
    try:
        lazy_model = request.app.state.models.fpgrowth
        if lazy_model is None:
            return {"error": "FPGrowthRecommender model not initialized"}

        recommender_fpg = await lazy_model.get()

        await recommender_fpg.update_suggested_products_in_db(
            top_n=top_n, min_support=min_support, min_confidence=min_confidence
        )
        return {"status": "success", "message": "Updated all suggested products in DB."}
    except Exception as e:
        return {
            "error": "FPGrowthRecommender not available, database not ready",
            "details": str(e),
        }
