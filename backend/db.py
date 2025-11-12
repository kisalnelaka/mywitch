import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

DB_PATH = os.getenv("DB_PATH", "/data/db.sqlite")
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class QueryLog(Base):
    __tablename__ = "query_logs"
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    latency = Column(Float, nullable=False)
    answer_tokens = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class IngestLog(Base):
    __tablename__ = "ingest_logs"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    chunks = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_session():
    return SessionLocal()
