from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.comments import Comment
from app.models.places import Place
from app.models.user import User
from app.schemas.comments import CommentCreate, CommentOut
from typing import List

def get_place_comments(db: Session, place_id: int, skip: int = 0, limit: int = 50):
    place = db.query(Place).filter(Place.contentid == place_id).first()
    if not place:
        return []  # 존재하지 않는 장소면 빈 리스트
    comments = (
        db.query(Comment, User.nickname)
        .join(User, User.id == Comment.user_id)
        .filter(Comment.place_id == place.id)  # id로 조회
        .order_by(desc(Comment.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )
    result = [
        {
            "id": c.Comment.id,
            "user_id": c.Comment.user_id,
            "nickname": c.nickname,
            "content": c.Comment.content,
            "created_at": c.Comment.created_at
        }
        for c in comments
    ]
    return [CommentOut(**r) for r in result]


def create_place_comment(db: Session, place_id: int, user_id: int, content: str) -> Comment:
    """댓글 생성"""
    # 장소 존재 확인
    place = db.query(Place).filter(Place.contentid == place_id).first()
    if not place:
        raise ValueError("존재하지 않는 장소입니다")
    
    comment = Comment(
        place_id=place.id,
        user_id=user_id,
        content=content
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment

def delete_place_comment(db: Session, comment_id: int, user_id: int) -> bool:
    """댓글 삭제 (본인만)"""
    comment = db.query(Comment).filter(
        Comment.id == comment_id,
        Comment.user_id == user_id
    ).first()
    
    if not comment:
        return False
    
    db.delete(comment)
    db.commit()
    return True
