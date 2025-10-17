#!/bin/bash
set -e

# Load environment variables from .env file if it exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

MODEL_DIR="/app/models"

# create model directory if not exists
mkdir -p $MODEL_DIR

# -------------------------------
# Download Phobert model (folder)
# -------------------------------
if [ -n "$PHOBERT_MODEL_PATH" ]; then
    PHOBERT_TARGET="$MODEL_DIR/phobert_model"
    if [ ! -d "$PHOBERT_TARGET" ]; then
        echo "Downloading phobert_model..."
        aws s3 cp --recursive "$PHOBERT_MODEL_PATH" "$PHOBERT_TARGET"
    else
        echo "phobert_model already exists, skip download."
    fi
fi

# -------------------------------
# Download Semantic model (folder)
# -------------------------------
if [ -n "$SEMANTIC_MODEL_PATH" ]; then
    SEMANTIC_TARGET="$MODEL_DIR/reviews_emotion_model"
    if [ ! -d "$SEMANTIC_TARGET" ]; then
        echo "Downloading semantic_model..."
        aws s3 cp --recursive "$SEMANTIC_MODEL_PATH" "$SEMANTIC_TARGET"
    else
        echo "semantic_model already exists, skip download."
    fi
fi

# -------------------------------
# Download YOLO model (single file)
# -------------------------------
if [ -n "$YOLO_MODEL_PATH" ]; then
    YOLO_FILE="$MODEL_DIR/last.pt"
    if [ ! -f "$YOLO_FILE" ]; then
        echo "Downloading YOLO model..."
        aws s3 cp "$YOLO_MODEL_PATH" "$YOLO_FILE"
    else
        echo "YOLO model already exists, skip download."
    fi
fi


# -------------------------------
# Download BLIP model
# -------------------------------

BLIP_TARGET="$MODEL_DIR/blip"
if [ ! -d "$BLIP_TARGET" ]; then
    echo "Downloading BLIP model..."
    python -c "
from transformers import BlipProcessor, BlipForConditionalGeneration
p = BlipProcessor.from_pretrained('Salesforce/blip-image-captioning-base', cache_dir='$BLIP_TARGET')
m = BlipForConditionalGeneration.from_pretrained('Salesforce/blip-image-captioning-base', cache_dir='$BLIP_TARGET')
p.save_pretrained('$BLIP_TARGET')
m.save_pretrained('$BLIP_TARGET')
"
else
    echo "BLIP model already exists, skip download."
fi



# -------------------------------
# Download InsightFace model
# -------------------------------
INSIGHTFACE_TARGET="$MODEL_DIR/insightface"
if [ ! -d "$INSIGHTFACE_TARGET" ]; then
    echo "Downloading InsightFace model..."
    python -c "
import insightface
insightface.app.FaceAnalysis(
    allowed_modules=['detection', 'recognition'],
    root='$INSIGHTFACE_TARGET'
).prepare(ctx_id=-1, det_size=(640,640))
"
else
    echo "InsightFace model already exists, skip download."
fi




# Run app
exec "$@"
