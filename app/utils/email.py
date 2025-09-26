import os, smtplib, random
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()  # .env 파일 로드

SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")

def generate_code(length: int = 6) -> str:
    """6자리 인증 코드 생성"""
    return "".join(str(random.randint(0, 9)) for _ in range(length))

def send_email_code_smtp(to_email: str, code: str):
    """Gmail SMTP로 인증 코드 발송"""
    msg = MIMEText(f"WALKorea 인증 코드: {code}")
    msg["Subject"] = "WALKorea 인증 코드"
    msg["From"] = SMTP_USER
    msg["To"] = to_email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, [to_email], msg.as_string())
    except Exception as e:
        print(f"[메일 발송 실패] {e}")
        raise ValueError("이메일 발송 실패")