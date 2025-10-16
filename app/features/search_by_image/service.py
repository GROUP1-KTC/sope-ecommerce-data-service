
from transformers import BlipProcessor, BlipForConditionalGeneration
import torch
import os
from app.configs.settings import settings


class SearchByImageService:
    MODEL_DIR = os.path.join(settings.model_dir, "Salesforce/blip-image-captioning-base")

    def __init__(self):
        if not os.path.exists(self.MODEL_DIR):
            self.processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base", cache_dir=self.MODEL_DIR)
            self.model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base", cache_dir=self.MODEL_DIR)
        else:
            self.processor = BlipProcessor.from_pretrained(self.MODEL_DIR)
            self.model = BlipForConditionalGeneration.from_pretrained(self.MODEL_DIR)

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