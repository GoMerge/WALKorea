from urllib.parse import quote_plus
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()  # .env 파일 로드

DB_PORT = os.getenv("DB_PORT", "3306")          # 기본 3306, 없으면 기본값 사용
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")  # 없으면 localhost 기본값

MYSQL_PASSWORD_ENCODED = quote_plus(os.getenv("MYSQL_PASSWORD"))
DATABASE_URL = f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{MYSQL_PASSWORD_ENCODED}@{os.getenv('MYSQL_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('MYSQL_DATABASE')}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()