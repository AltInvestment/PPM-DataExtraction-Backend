from pydantic import BaseModel, Field
from typing import List, Dict, Any


class ProcessResponse(BaseModel):
    message: str = Field(
        ..., description="A message indicating the result of the processing request."
    )


class FilesResponse(BaseModel):
    processed_file_ids: List[str] = Field(
        ..., description="A list of processed file IDs."
    )


class DataResponse(BaseModel):
    deal_id: str = Field(..., description="The Deal_ID associated with the data.")
    data: Dict[str, List[Dict[str, Any]]] = Field(
        ...,
        description="A dictionary containing data from all sheets related to the Deal_ID.",
    )


class DealIDsResponse(BaseModel):
    deal_ids: List[str] = Field(
        ..., description="A list of all unique Deal_IDs from the Google Sheet."
    )
