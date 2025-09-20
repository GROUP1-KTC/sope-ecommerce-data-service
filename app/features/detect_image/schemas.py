from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any


class DetectionResult(BaseModel):
    valid: bool
    detected: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None
    model_config = ConfigDict(extra="forbid")
