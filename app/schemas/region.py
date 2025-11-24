from pydantic import BaseModel
from typing import Optional, List


class RegionBase(BaseModel):
    code: str
    name: str
    level: int
    parent_id: Optional[int] = None
    full_name: Optional[str] = None


class RegionCreate(RegionBase):
    pass


class Region(RegionBase):
    id: int
    children: List["Region"] = []

    class Config:
        from_attributes = True
