from transformers import AutoTokenizer, AutoModel
import torch
import os
from app.configs.settings import settings


class PhoBERTEmbedding:
    def __init__(self, model_path: str = None):
        if model_path is None:
            raise ValueError("model_path must be provided")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModel.from_pretrained(model_path)
        self.model.to(self.device)
        self.model.eval()

    @classmethod
    def from_pretrained(cls, model_name: str):
        model_path = os.path.join(settings.model_dir, model_name)
        return cls(model_path)

    def embed(self, text: str):
        inputs = self.tokenizer(
            text, return_tensors="pt", truncation=True, padding=True
        )

        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            embeddings = outputs.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
        return embeddings.tolist() if len(embeddings) > 1 else embeddings[0].tolist()
