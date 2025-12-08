from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.utils.auth import get_current_user
from app.models.user import User
from app.schemas.comments import CommentCreate, CommentOut
from app.services import comments

router = APIRouter(prefix="/places", tags=["comments"])

@router.get("/{place_id}/comments", response_model=List[CommentOut])
async def read_place_comments(
    place_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """댓글 목록 조회"""
    c = comments.get_place_comments(db, place_id, skip=skip, limit=limit)
    return c

@router.post("/{place_id}/comments", response_model=dict)
async def create_comment(
    place_id: int,
    comment_in: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """댓글 작성"""
    if len(comment_in.content.strip()) < 2:
        raise HTTPException(status_code=400, detail="댓글은 2자 이상 작성해주세요")
    
    comment = comments.create_place_comment(
        db, place_id, current_user.id, comment_in.content
    )
    return {"message": "댓글 등록 성공", "comment_id": comment.id}

@router.delete("/{place_id}/comments/{comment_id}", response_model=dict)
async def delete_comment(
    place_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """댓글 삭제"""
    if comments.delete_place_comment(db, comment_id, current_user.id):
        return {"message": "댓글 삭제 성공"}
    raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다")
