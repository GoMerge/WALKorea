from pydantic import BaseModel
from typing import Optional, List

class PlaceResponse(BaseModel):
    content_id: str
    title: str
    addr1: Optional[str]
    overview: Optional[str]

    class Config:
        orm_mode = True

class PlaceDetailResponse(BaseModel):
    place_id: str
    detail_json: dict

    class Config:
        orm_mode = True
