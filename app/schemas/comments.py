from pydantic import BaseModel
from datetime import datetime

class CommentCreate(BaseModel):
    content: str

class CommentOut(BaseModel):
    id: int
    content: str
    nickname: str
    created_at: datetime
    user_id: int
    
    class Config:
        from_attributes = True
        orm_mode = True