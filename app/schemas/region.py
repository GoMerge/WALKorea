from pydantic import BaseModel
from typing import Optional, List


class RegionBase(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class RegionCreate(RegionBase):
    pass


class Region(RegionBase):
    id: int
    children: List["Region"] = []

    class Config:
        from_attributes = True

class RegionSearchItem(BaseModel):
    id: int
    code: str
    full_name: str

    class Config:
        from_attributes = True

