from apscheduler.schedulers.background import BackgroundScheduler
from app.database import SessionLocal
from app.utils.auth import delete_expired_users

db_session = SessionLocal()

def scheduled_delete():
    delete_expired_users(db_session)

scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_delete, 'interval', days=1)

def start_scheduler():
    scheduler.start()
