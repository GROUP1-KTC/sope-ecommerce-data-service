from fastapi import APIRouter, Request

router = APIRouter(prefix="/recommend/users", tags=["UserCF Recommender"])


@router.post("/")
async def update_user_recommendations(request: Request, top_n: int = 5):
    try:
        lazy_model = request.app.state.models.user_cf
        if lazy_model is None:
            return {"error": "UserCFRecommender model not initialized"}

        recommender_user_cf = await lazy_model.get()
        await recommender_user_cf.update_suggested_products_for_all_users(top_n=top_n)

        return {
            "status": "success",
            "message": "Updated suggested products for all users.",
        }

    except Exception as e:
        return {
            "error": "UserCFRecommender not available, database not ready",
            "details": str(e),
        }


@router.get("/{user_id}")
async def recommend_user(request: Request, user_id: str, top_n: int = 5):
    try:
        lazy_model = request.app.state.models.user_cf
        if lazy_model is None:
            return {"error": "UserCFRecommender model not initialized"}

        recommender_user_cf = await lazy_model.get()

        recs = await recommender_user_cf.recommend_products(user_id, top_n=top_n)

        return {"user_id": user_id, "recommendations": recs}

    except Exception as e:
        return {
            "error": "UserCFRecommender not available, database not ready",
            "details": str(e),
        }
