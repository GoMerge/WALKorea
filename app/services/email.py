from fastapi import HTTPException
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.utils.email import send_email_code_smtp
import random

email_code_cache = {}

class EmailService:
    def generate_code(self, length: int = 6) -> str:
        return "".join([str(random.randint(0, 9)) for _ in range(length)])

    def send_code(self, email: str) -> str:
        """이메일 인증 코드 생성 + 메일 발송"""
        code = self.generate_code()
        expires_at = datetime.utcnow() + timedelta(minutes=5)  # datetime 객체
        email_code_cache[email] = (code, expires_at)

        # 실제 이메일 발송 함수
        send_email_code_smtp(email, code)
        return code

    def verify_code(self, email: str, code: str) -> bool:
        """이메일 인증 코드 검증"""
        record = email_code_cache.get(email)
        if not record:
            raise HTTPException(status_code=400, detail="인증 코드가 발송되지 않았습니다.")
        saved_code, expires_at = record

        # datetime 비교
        if not isinstance(expires_at, datetime):
            raise HTTPException(status_code=500, detail="인증 코드 만료 시간이 잘못되었습니다.")

        if expires_at < datetime.utcnow():
            del email_code_cache[email]
            raise HTTPException(status_code=400, detail="인증 코드가 만료되었습니다.")
        if saved_code != code:
            raise HTTPException(status_code=400, detail="잘못된 인증 코드입니다.")

        # 검증 성공 시 삭제
        del email_code_cache[email]
        return True

# 전역 인스턴스
email_service = EmailService()