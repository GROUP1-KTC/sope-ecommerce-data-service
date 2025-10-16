

from fastapi import FastAPI, File, UploadFile, APIRouter, Request
from fastapi.responses import JSONResponse
from PIL import Image
from io import BytesIO

router = APIRouter(prefix="/search_by_image", tags=["Search By Image"])

@router.post("/caption")
async def generate_caption(request: Request, file: UploadFile = File(...)):
    try:
        lazy_model = request.app.state.models.search_by_image
        if lazy_model is None:
            return JSONResponse(status_code=503, content={"error": "SearchByImageService model not initialized"})
        search_by_image_service = await lazy_model.get()
        
        image = await file.read()
        
        image = Image.open(BytesIO(image)).convert("RGB")
        
        caption = await search_by_image_service.generate_caption(image)
        return JSONResponse({
            "filename": file.filename,
            "caption": caption
        })
    
    except Exception as e:
        return JSONResponse(
            {"error": str(e)},
            status_code=500
        )