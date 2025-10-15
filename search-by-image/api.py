from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import torch
import io

app = FastAPI(title="Image Caption API", version="1.0")

# --- Load model & processor 1 lần khi khởi động server ---
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)


@app.post("/api/v1/caption")
async def generate_caption(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        inputs = processor(image, return_tensors="pt").to(device)

        out = model.generate(**inputs, max_length=50)
        caption = processor.decode(out[0], skip_special_tokens=True)

        return JSONResponse({
            "filename": file.filename,
            "caption": caption
        })

    except Exception as e:
        return JSONResponse(
            {"error": str(e)},
            status_code=500
        )
