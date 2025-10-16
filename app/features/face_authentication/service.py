import numpy as np
import os
from app.configs.settings import settings
from insightface.app import FaceAnalysis
from fastapi import HTTPException
from app.features.face_authentication.utils import decode_b64_to_cv2, variance_of_laplacian, get_embedding, extract_landmarks,head_movement_liveness,robust_average_embeddings,cosine_similarity, create_face_auth_token

import mediapipe as mp


class FaceService:
    def __init__(self, collection=None):
        if collection is None:
            raise ValueError("Database collection must be provided for FaceService.")
        self.collection = collection

        MODEL_DIR = os.path.join(settings.model_dir, "insightface_models")

        os.makedirs(MODEL_DIR, exist_ok=True)

        self.model = FaceAnalysis(
    allowed_modules=["detection", "recognition"], root=MODEL_DIR)
        
        self.model.prepare(ctx_id=-1, det_size=(640, 640))

        self.mp_face_mesh = mp.solutions.face_mesh


    @classmethod
    def from_pretrained(cls, collection=None):
        instance = cls(collection=collection)
        return instance


    def register_face(self, username: str, images: dict):
        # validate presence
        for a in ["center", "left", "right", "up", "down"]:
            if a not in images or not isinstance(images[a], list) or len(images[a]) == 0:
                raise HTTPException(status_code=400, detail=f"Missing images for {a}")

        # for each image base64 -> decode -> filter blur -> get embedding
        all_embs = []
        landmarks_sample = {}
        for angle, b64_list in images.items():
            landmarks_sample[angle] = []
            for b64 in b64_list:
                img = decode_b64_to_cv2(b64)
                if img is None:
                    continue
                blur = variance_of_laplacian(img)
                if blur < settings.blur_threshold:
                    # skip blurry
                    continue
                # extract embedding
                emb = get_embedding(img, self.model)
                if emb is None:
                    continue
                all_embs.append(emb)
                # optionally save one landmark sample per angle
                lm = extract_landmarks(img, self.mp_face_mesh)
                if lm is not None:
                    landmarks_sample[angle].append(lm.tolist())

        if not all_embs:
            raise HTTPException(
                status_code=400,
                detail="Không có ảnh hợp lệ (tất cả mờ / không phát hiện khuôn mặt)",
            )

        # robust average embedding
        avg_emb = robust_average_embeddings(all_embs)
        # normalize
        if np.linalg.norm(avg_emb) == 0:
            raise HTTPException(status_code=500, detail="Embedding error")
        avg_emb = (avg_emb / np.linalg.norm(avg_emb)).tolist()

        # store in DB
        self.collection.update_one(
            {"username": username},
            {"$set": {"embedding": avg_emb, "landmarks_sample": landmarks_sample}},
            upsert=True,
        )
        doc = self.collection.find_one({"username": username})
        return {"message": "registered", "id": str(doc["_id"])}

    def verify_face(self, username: str, images: dict):

        doc = self.collection.find_one({"username": username})
        if not doc or "embedding" not in doc:
            return {"match_found": False, "message": "User not registered for face auth"}

        stored_emb = np.array(doc["embedding"], dtype=np.float32)

        # process incoming images same as register: filter blur, get embeddings
        all_embs = []
        landmarks = {}
        for angle, b64_list in images.items():
            landmarks[angle] = []
            for b64 in b64_list:
                img = decode_b64_to_cv2(b64)
                if img is None:
                    continue
                blur = variance_of_laplacian(img)
                if blur < settings.blur_threshold:
                    continue
                emb = get_embedding(img, self.model)
                if emb is None:
                    continue
                all_embs.append(emb)
                lm = extract_landmarks(img, self.mp_face_mesh)
                if lm is not None:
                    landmarks[angle].append(lm)

        if not all_embs:
            return {"match_found": False, "message": "No valid face images provided"}

        avg_emb = robust_average_embeddings(all_embs)
        if avg_emb is None:
            return {"match_found": False, "message": "Embedding compute failed"}

        # similarity (cosine) higher is better (1.0 perfect)
        sim = cosine_similarity(stored_emb, avg_emb)

        # liveness: try head movement check using median landmark per angle
        center_lm = None
        left_lm = None
        right_lm = None
        if landmarks.get("center"):
            center_lm = np.median(np.stack([l for l in landmarks["center"]]), axis=0)  # noqa: E741
        if landmarks.get("left"):
            left_lm = np.median(np.stack([l for l in landmarks["left"]]), axis=0)  # noqa: E741
        if landmarks.get("right"):
            right_lm = np.median(np.stack([l for l in landmarks["right"]]), axis=0)  # noqa: E741

        liveness_ok = head_movement_liveness(center_lm, left_lm, right_lm, thresh_px=8)

        match = (sim >= settings.similarity_threshold) and liveness_ok
    
        if match:
            token_data = {"faceAuthId": str(doc["_id"]), "userId": doc.get("username")}
            face_auth_token = create_face_auth_token(token_data)
            return {
                "match_found": True,
                "face_auth_token": face_auth_token,
                "similarity": float(sim),
                "liveness": liveness_ok
            }
            
                
        return {
            "match_found": False,
            "message": "Not matched",
            "similarity": float(sim),
            "liveness": bool(liveness_ok),
        }
