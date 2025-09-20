import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from app.configs.settings import settings


class SentimentAnalyzer:
    def __init__(self, model_path: str = None, labels=None):
        if model_path is None:
            raise ValueError("model_path must be provided")
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path, local_files_only=True
        )
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_path, local_files_only=True
        )
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        self.model.eval()
        self.labels = labels or ["negative", "neutral", "positive"]

    @classmethod
    def from_pretrained(cls, model_name: str, labels=None):
        model_path = os.path.join(settings.model_dir, model_name)
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model {model_name} not found at {model_path}")
        return cls(model_path, labels=labels)

    def predict(self, text: str) -> str:
        inputs = self.tokenizer(
            text, return_tensors="pt", padding=True, truncation=True, max_length=128
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = outputs.logits.softmax(dim=1)
            pred = probs.argmax().item()

        return self.labels[pred]
