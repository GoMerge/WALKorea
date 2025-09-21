import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = "202438003@itc.ac.kr"

def send_reset_password_email(to_email: str, token: str):
    reset_link = f"https://yourdomain.com/reset-password?token={token}"
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=to_email,
        subject="[YourApp] 비밀번호 재설정 요청 안내",
        html_content=f"""
        <p>안녕하세요.</p>
        <p>다음 링크를 클릭해서 비밀번호를 재설정하세요:</p>
        <p><a href="{reset_link}">{reset_link}</a></p>
        <p>감사합니다.</p>
        """
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        return response.status_code
    except Exception as e:
        print(f"이메일 발송 실패: {e}")
        return None

def send_account_deletion_email(to_email: str, user_name: str):
    subject = "[YourApp] 회원 탈퇴 안내"
    html_content = f"""
    <p>안녕하세요, {user_name}님.</p>
    <p>회원 탈퇴 처리가 정상적으로 완료되었습니다.</p>
    <p>그동안 서비스를 이용해 주셔서 감사합니다.</p>
    """
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=to_email,
        subject=subject,
        html_content=html_content
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        return response.status_code
    except Exception as e:
        print(f"회원 탈퇴 안내 이메일 발송 실패: {e}")
        return None