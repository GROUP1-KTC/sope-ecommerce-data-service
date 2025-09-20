from pydantic import BaseModel, ConfigDict


class TextRequest(BaseModel):
    text: str
    model_config = ConfigDict(extra="forbid")
