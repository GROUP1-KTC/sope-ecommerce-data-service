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

    # JWT
    jwt_private_key: str
    jwt_public_key: str

    # AWS S3
    model_dir: str

    phobert_model_path: str | None = None
    semantic_model_path: str | None = None
    yolo_model_path: str | None = None
    shape_predictor_68_path: str | None = None

    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_default_region: str | None = None

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
