from pydantic import BaseModel
from typing import List, Dict, Any

class ProcessResponse(BaseModel):
    message: str

class FilesResponse(BaseModel):
    processed_file_ids: List[str]

class DataResponse(BaseModel):
    deal_id: str
    data: Dict[str, List[Dict[str, Any]]]
