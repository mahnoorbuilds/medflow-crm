import datetime as dt

from sqlalchemy import Boolean, Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

import os

# Fetch from environment (Vercel Postgres or custom DATABASE_URL) or fallback to SQLite
# Vercel provides POSTGRES_URL_NON_POOLING and POSTGRES_URL
postgres_url = os.getenv("POSTGRES_URL_NON_POOLING", os.getenv("POSTGRES_URL", os.getenv("DATABASE_URL")))
# Vercel functions are read-only except for /tmp
DATABASE_URL = postgres_url if postgres_url else "sqlite:////tmp/appointments_db.db"

# Fix for some cloud providers that give 'postgres://' instead of 'postgresql://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite requires check_same_thread=False, PostgreSQL does not
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    patient_name = Column(String, index=True)
    reason = Column(String, nullable=True)
    start_time = Column(DateTime, index=True)
    canceled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#init_db()