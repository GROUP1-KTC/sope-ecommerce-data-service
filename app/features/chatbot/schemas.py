from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # Generated if not provided
    user_token: Optional[str] = None  # JWT from frontend
    model_config = ConfigDict(extra="forbid")


class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: Optional[List[Dict[str, Any]]] = None  # RAG sources
    tool_calls: Optional[List[str]] = None  # Tools used
    tool_outputs: Optional[List[Dict[str, Any]]] = None  # Tool outputs
