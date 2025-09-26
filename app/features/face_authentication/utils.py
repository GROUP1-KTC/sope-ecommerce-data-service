import numpy as np
from app.configs.settings import settings
from datetime import datetime, timedelta
import jwt

def shape_to_np(shape, dtype="int"):
    coords = np.zeros((68, 2), dtype=dtype)
    for i in range(68):
        coords[i] = (shape.part(i).x, shape.part(i).y)
    return coords


def crop_face(frame, rect):
    x, y, w, h = rect.left(), rect.top(), rect.width(), rect.height()
    return frame[y : y + h, x : x + w]


def calculate_distances(landmarks):
    distances = []
    num_points = landmarks.shape[0]
    for i in range(num_points):
        for j in range(i + 1, num_points):
            distances.append(np.linalg.norm(landmarks[i] - landmarks[j]))
    return [distances]


def compare_landmarks(landmarks, stored_landmarks):
    dist_threshold = 200
    distances = calculate_distances(landmarks)
    dist_diff = np.linalg.norm(np.array(distances) - np.array(stored_landmarks))
    return dist_diff < dist_threshold, dist_diff


def load_landmarks_data(username: str, collection):
    doc = collection.find_one({"username": username})
    if doc and "landmarks" in doc:
        return doc["landmarks"]
    return []



ACCESS_TOKEN_EXPIRE_MINUTES = 5

def format_rsa_key(raw_key: str, key_type: str = "PRIVATE") -> str:
    header = f"-----BEGIN {key_type} KEY-----\n"
    footer = f"\n-----END {key_type} KEY-----"
    key_body = "\n".join(raw_key[i : i + 64] for i in range(0, len(raw_key), 64))
    return header + key_body + footer



PRIVATE_KEY_RAW = settings.jwt_private_key
PRIVATE_KEY = format_rsa_key(PRIVATE_KEY_RAW, "PRIVATE")


def create_face_auth_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    token = jwt.encode(to_encode, PRIVATE_KEY, algorithm="RS256")
    return token