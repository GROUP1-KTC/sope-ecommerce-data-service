from pydantic_settings import BaseSettings
from typing import List
from pydantic import ConfigDict


class Settings(BaseSettings):
    # App
    app_name: str
    app_port: int
    debug: bool
    allowed_origins: List[str]

    # Database
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_pass: str

    mongo_uri: str | None = None
    db_name_mongo: str | None = None
    collection_name: str | None = None

    # Face Authentication
    similarity_threshold: float | None = 0.6
    blur_threshold: float | None = 20.0

    # JWT
    jwt_private_key: str
    jwt_public_key: str

    # AWS S3
    model_dir: str

    phobert_model_path: str | None = None
    semantic_model_path: str | None = None
    yolo_model_path: str | None = None

    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_default_region: str | None = None

    # Backend API
    backend_api_url: str = "http://localhost:8082/api/v1"

    # Redis Chat Memory
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_pass: str | None = None
    redis_chat_db: int = 1
    chat_memory_ttl: int = 86400  # 24 hours
    max_chat_history_messages: int = 20


    # AWS Bedrock Chatbot
    aws_access_key_id_chatbot: str | None = None
    aws_secret_access_key_chatbot: str | None = None
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    knowledge_base_id: str | None = None
    guardrail_id: str | None = None
    guardrail_version: str = "DRAFT"

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
