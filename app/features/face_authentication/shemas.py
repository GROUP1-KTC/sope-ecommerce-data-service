from pydantic import BaseModel
from typing import Dict, List


class ImagesPayload(BaseModel):
    username: str
    images: Dict[str, List[str]] 

