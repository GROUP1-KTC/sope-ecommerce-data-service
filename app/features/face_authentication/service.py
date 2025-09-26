import base64
import cv2
import numpy as np
from fastapi.responses import JSONResponse
from bson import ObjectId
import dlib

from app.features.face_authentication.utils import (
   crop_face, shape_to_np,
    calculate_distances, compare_landmarks, create_face_auth_token
)


class FaceService:
    def __init__(self, collection=None):
        if collection is None:
            raise ValueError("Database collection must be provided for FaceService.")
        self.collection = collection

        predictor_path = "shape_predictor_68_face_landmarks.dat"
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(predictor_path)
        self.captured_landmarks = {}

    @classmethod
    def from_pretrained(cls, collection=None):
        instance = cls(collection=collection)
        return instance

    def capture_frame(self, username: str, angle: str, frame_base64: str):
        frame_data = base64.b64decode(frame_base64)
        frame = cv2.imdecode(np.frombuffer(frame_data, np.uint8), cv2.IMREAD_COLOR)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rects = self.detector(gray, 0)
        if len(rects) == 0:
            return JSONResponse({"message": "No face detected"}, status_code=400)

        rect = rects[0]
        cropped_face = crop_face(frame, rect)
        shape = self.predictor(gray, rect)
        landmarks = shape_to_np(shape)

        self.captured_landmarks.setdefault(username, []).append(landmarks)

        _, buffer = cv2.imencode(".jpg", cropped_face)
        face_only = base64.b64encode(buffer).decode("utf-8")

        return JSONResponse({"message": f"Captured {angle} angle", "frame": face_only})

    def save_landmarks(self, username: str):
        if username not in self.captured_landmarks or len(self.captured_landmarks[username]) == 0:
            return JSONResponse(
                {"message": f"No landmarks to save for {username}"}, status_code=400
            )

        avg_landmarks = np.mean(self.captured_landmarks[username], axis=0)
        distances = calculate_distances(avg_landmarks)

        self.collection.update_one(
            {"username": username}, {"$set": {"landmarks": distances}}, upsert=True
        )

        doc = self.collection.find_one({"username": username})
        object_id = str(doc["_id"])

        self.captured_landmarks.pop(username)

        return JSONResponse(
            {"message": f"Landmarks saved for {username} in MongoDB", "idObject": object_id}
        )

    def verify_face(self, faceAuthId: str, frame_bytes: bytes):
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return JSONResponse({"match_found": False, "message": "Invalid image"})

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rects = self.detector(gray, 0)
        if not rects:
            return JSONResponse({"match_found": False, "message": "No face detected"})

        doc = self.collection.find_one({"_id": ObjectId(faceAuthId)})
        if not doc or "landmarks" not in doc:
            return JSONResponse({"match_found": False, "message": "No user data"})

        stored_landmarks_data = doc["landmarks"]

        for rect in rects:
            shape = self.predictor(gray, rect)
            landmarks = shape_to_np(shape)

            for stored_landmarks in stored_landmarks_data:
                is_match, dist_diff = compare_landmarks(landmarks, stored_landmarks)
                if is_match:
                    token_data = {"faceAuthId": str(doc["_id"]), "userId": doc.get("username")}
                    face_auth_token = create_face_auth_token(token_data)
                    return JSONResponse(
                        {"match_found": True,
                         "face_auth_token": face_auth_token,
                         "distance_diff": dist_diff}
                    )

        return JSONResponse({"match_found": False, "message": "Not matched"})
