
from transformers import BlipProcessor, BlipForConditionalGeneration
import torch
import os
from app.configs.settings import settings


class SearchByImageService:

    def __init__(self):
        MODEL_DIR = os.path.join(settings.model_dir, "blip")

        
        self.processor = BlipProcessor.from_pretrained(MODEL_DIR)
        self.model = BlipForConditionalGeneration.from_pretrained(MODEL_DIR)

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)

    @classmethod
    async def from_pretrained(cls):
        return cls()
    

    async def generate_caption(self, image):
        inputs = self.processor(image, return_tensors="pt").to(self.device)

        out = self.model.generate(**inputs, max_length=50)
        caption = self.processor.decode(out[0], skip_special_tokens=True)

        return caption