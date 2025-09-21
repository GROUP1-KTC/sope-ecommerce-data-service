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

# Run app
exec "$@"
