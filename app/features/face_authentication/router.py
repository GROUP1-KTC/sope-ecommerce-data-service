from app.features.face_authentication.shemas import ImagesPayload
from fastapi import APIRouter, Request

router = APIRouter(prefix="/face", tags=["Face Authentication"])


@router.post("/register")
async def register_face(request: Request, payload: ImagesPayload):
    try:
        lazy_model = request.app.state.models.face_auth

        if lazy_model is None:
            return {"error": "FaceAuth model not initialized"}


        face_service = await lazy_model.get()

        return face_service.register_face(payload.username, payload.images)
    except Exception as e:
        return {"error": str(e)}

@router.post("/verify")
async def verify(request: Request,payload: ImagesPayload):
    try:
        lazy_model = request.app.state.models.face_auth
        if lazy_model is None:
            return {"error": "FaceAuth model not initialized"}
        face_service = await lazy_model.get()
        return face_service.verify_face(payload.username, payload.images)
    except Exception as e:
        return {"error": str(e)}
