from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.sql_db import Base

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)  # unique string like UUID
    created_at = Column(DateTime, default=datetime.utcnow)

    scores = relationship("QuizScore", back_populates="user_session")
    weaknesses = relationship("UserWeakness", back_populates="user_session")


class QuizScore(Base):
    __tablename__ = "quiz_scores"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("user_sessions.id"))
    topic = Column(String, index=True)
    score = Column(Float)
    total_questions = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    user_session = relationship("UserSession", back_populates="scores")


class UserWeakness(Base):
    __tablename__ = "user_weakness"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("user_sessions.id"))
    topic = Column(String, index=True)
    severity = Column(Float) # calculated based on poor quiz performance
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user_session = relationship("UserSession", back_populates="weaknesses")
