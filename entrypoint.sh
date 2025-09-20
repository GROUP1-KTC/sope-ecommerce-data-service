#!/bin/bash
set -e

# Load environment variables from .env file if it exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

MODEL_DIR="/app/models"

# create model directory if not exists
mkdir -p $MODEL_DIR

# List of models
declare -A MODELS
MODELS=( 
  ["phobert_model"]=$PHOBERT_MODEL_PATH
  ["semantic_model"]=$SEMANTIC_MODEL_PATH
  ["yolo_model"]=$YOLO_MODEL_PATH
)

for model in "${!MODELS[@]}"; do
  TARGET_DIR="$MODEL_DIR/$model"
  if [ ! -d "$TARGET_DIR" ]; then
    echo "Downloading $model..."
    aws s3 cp --recursive "${MODELS[$model]}" "$TARGET_DIR"
  else
    echo "$model already exists, skip download."
  fi
done

# Run app
exec "$@"
