from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from app.features.detect_image.schemas import DetectionResult


router = APIRouter(prefix="/detect", tags=["Image Detection"])


@router.post("/verify", response_model=DetectionResult)
async def verify(request: Request, file: UploadFile = File(...)):
    try:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File is not an image")

        image_bytes = await file.read()

        lazy_model = request.app.state.models.yolo

        model_instance = await lazy_model.get()
        result_dict = model_instance.validate(image_bytes)
        return result_dict

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
