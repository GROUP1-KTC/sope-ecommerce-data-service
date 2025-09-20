from ultralytics import YOLO
from PIL import Image
import io
import os
from app.configs.settings import settings


class YOLOModel:
    def __init__(self, model_path: str = None, min_conf=0.8):
        if model_path is None:
            raise ValueError("model path must be provided")
        self.model = YOLO(model_path)
        self.min_conf = min_conf

    @classmethod
    def from_pretrained(cls, model_name: str = "last.pt", min_conf: float = 0.8):
        model_path = os.path.join(settings.model_dir, model_name)

        return cls(model_path, min_conf)

    def validate(self, image_file: bytes):
        img = Image.open(io.BytesIO(image_file)).convert("RGB")
        results = self.model(img)
        boxes = results[0].boxes

        if not boxes:
            return {"valid": True}

        best_box = max(boxes, key=lambda b: float(b.conf))
        cls_name = results[0].names[int(best_box.cls)]
        conf = float(best_box.conf)

        if conf >= self.min_conf:
            return {
                "valid": False,
                "reason": f"Invalid image content detected - {cls_name}",
                "detected": {"class": cls_name, "confidence": conf},
            }
        return {"valid": True}
