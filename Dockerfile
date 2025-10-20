# # base image
# FROM python:3.12.7-slim

# # Set workdir
# WORKDIR /app


# RUN apt-get update && apt-get install -y --no-install-recommends \
#         curl unzip groff less \
#         libgl1 libglib2.0-0 libsm6 libxrender1 libxext6 \
#         cmake g++ make \
#     && rm -rf /var/lib/apt/lists/* \
#     # Install AWS CLI v2
#     && curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
#     && unzip awscliv2.zip \
#     && ./aws/install \
#     && rm -rf aws awscliv2.zip

# # Copy project
# COPY . .

# # Install dependencies
# RUN pip install --no-cache-dir --upgrade pip \
#     && pip install --no-cache-dir -r requirements.txt


# COPY entrypoint.sh /entrypoint.sh

# RUN chmod +x /entrypoint.sh

# # Run service with uvicorn
# ENTRYPOINT ["/entrypoint.sh"]
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]





# ========== BUILD STAGE ==========
FROM python:3.12.7-slim AS builder

WORKDIR /app

# Cài tool build & AWS CLI (builder only)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl unzip groff less \
        libgl1 libglib2.0-0 libsm6 libxrender1 libxext6 \
        cmake g++ make \
    && curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf aws awscliv2.zip \
    && rm -rf /var/lib/apt/lists/*

# Cài Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ project
COPY . .

# ========== FINAL STAGE ==========
FROM python:3.12.7-slim

WORKDIR /app

# Install system lib runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 libglib2.0-0 libsm6 libxrender1 libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Copy AWS CLI from builder
COPY --from=builder /usr/local/aws-cli /usr/local/aws-cli
COPY --from=builder /usr/local/bin/aws /usr/local/bin/aws

# Copy Python env & source
COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app

# Entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
