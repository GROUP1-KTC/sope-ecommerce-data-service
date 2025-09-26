from fastapi import APIRouter, Request, Form, File, UploadFile
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/face", tags=["Face Authentication"])

@router.post("/capture")
async def capture(request: Request):
    try:
        lazy_model = request.app.state.models.face_auth

        if lazy_model is None:
            return {"error": "FaceAuth model not initialized"}

        data = await request.json()

        face_service = await lazy_model.get()

        return face_service.capture_frame(
            username=data["username"],
            angle=data.get("angle", "center"),
            frame_base64=data["frame"]
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@router.post("/save")
async def save_landmarks(request: Request):
    try:
        lazy_model = request.app.state.models.face_auth

        if lazy_model is None:
            return {"error": "FaceAuth model not initialized"}

        data = await request.json()

        face_service = await lazy_model.get()

        return face_service.save_landmarks(data["username"])
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@router.post("/verify")
async def verify(request: Request,faceAuthId: str = Form(...), file: UploadFile = File(...)):
    try:
        lazy_model = request.app.state.models.face_auth
        if lazy_model is None:
            return {"error": "FaceAuth model not initialized"}
        face_service = await lazy_model.get()
        contents = await file.read()
        return face_service.verify_face(faceAuthId, contents)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
