import numpy as np
from app.configs.settings import settings
from datetime import datetime, timedelta
import jwt

import cv2
import base64
from typing import List



# util decode
def decode_b64_to_cv2(b64: str):
    # b64 is base64 string without prefix
    data = base64.b64decode(b64)
    arr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img


# blur detector
def variance_of_laplacian(img: np.ndarray) -> float:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


# get embedding from insightface
def get_embedding(img: np.ndarray, fa) -> np.ndarray:
    # insightface expects RGB input for FaceAnalysis.get
    try:
        results = fa.get(np.ascontiguousarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)))
        if not results:
            return None
        # .embedding or .normed_embedding depending on version; prefer .embedding then normalize
        emb = results[0].embedding
        emb = np.array(emb, dtype=np.float32)
        # normalize
        norm = np.linalg.norm(emb)
        if norm == 0:
            return None
        return emb / norm
    except Exception as e:
        print("insightface error:", e)
        return None


# extract landmarks with mediapipe face_mesh (returns Nx3 array)
def extract_landmarks(img: np.ndarray, mp_face_mesh) -> np.ndarray:
    with mp_face_mesh.FaceMesh(
        static_image_mode=True, max_num_faces=1, refine_landmarks=True
    ) as fm:
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        res = fm.process(img_rgb)
        if not res.multi_face_landmarks:
            return None
        lm = res.multi_face_landmarks[0]
        h, w = img.shape[:2]
        pts = []
        for p in lm.landmark:
            pts.append([p.x * w, p.y * h, p.z * w])
        return np.array(pts)


# simple head movement liveness: check nose x shift between center and left/right
def head_movement_liveness(center_land, left_land, right_land, thresh_px=10):
    if center_land is None or left_land is None or right_land is None:
        return False
    # choose nose tip landmark index approximate (Mediapipe FaceMesh nose tip ~ 1)
    nose_idx = 1
    cx = float(center_land[nose_idx][0])
    lx = float(left_land[nose_idx][0])
    rx = float(right_land[nose_idx][0])
    shift_left = abs(cx - lx)
    shift_right = abs(cx - rx)
    return (shift_left > thresh_px) and (shift_right > thresh_px)


# combine embeddings robustly: remove outliers by distance to median before mean
def robust_average_embeddings(embs: List[np.ndarray]) -> np.ndarray:
    if not embs:
        return None
    arr = np.vstack(embs)  # shape (n, d)
    # median embedding
    med = np.median(arr, axis=0)
    # compute distances
    dists = np.linalg.norm(arr - med, axis=1)
    # keep only those within 2*median distance (simple outlier removal)
    med_dist = np.median(dists)
    keep_idx = np.where(dists <= max(2 * med_dist, 1e-6))[0]
    if len(keep_idx) == 0:
        # fallback to mean of all
        return np.mean(arr, axis=0)
    return np.mean(arr[keep_idx], axis=0)


def cosine_similarity(a: np.ndarray, b: np.ndarray):
    a_n = a / np.linalg.norm(a)
    b_n = b / np.linalg.norm(b)
    return float(np.dot(a_n, b_n))


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