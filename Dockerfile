# base image
FROM python:3.12.7-slim

# Set workdir
WORKDIR /app


RUN apt-get update && apt-get install -y --no-install-recommends \
        curl unzip groff less \
        libgl1 libglib2.0-0 libsm6 libxrender1 libxext6 \
        cmake g++ make \
    && rm -rf /var/lib/apt/lists/* \
    # Install AWS CLI v2
    && curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf aws awscliv2.zip

# Copy project
COPY . .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


RUN python -c "from transformers import BlipProcessor, BlipForConditionalGeneration; \
    BlipProcessor.from_pretrained('Salesforce/blip-image-captioning-base', cache_dir='/app/models/blip'); \
    BlipForConditionalGeneration.from_pretrained('Salesforce/blip-image-captioning-base', cache_dir='/app/models/blip')"


RUN python -c "import insightface; \
    insightface.app.FaceAnalysis(allowed_modules=['detection','recognition'], root='/app/models/insightface').prepare(ctx_id=-1, det_size=(640,640))"


COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

# Run service with uvicorn
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
