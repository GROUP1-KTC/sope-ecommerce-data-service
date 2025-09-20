# base image
FROM python:3.12.7-slim

# Set workdir
WORKDIR /app

# Copy project
COPY . .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


RUN chmod +x /entrypoint.sh

# Run service with uvicorn
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
