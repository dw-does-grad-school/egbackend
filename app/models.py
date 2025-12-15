# app/models.py
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # External ID from Clerk or other auth provider
    external_id = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    taste_profile = relationship(
        "UserTasteProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    interactions = relationship(
        "UserArtworkInteraction",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserTasteProfile(Base):
    __tablename__ = "user_taste_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    # Store vectors as JSON (e.g. list[float]); later you can move to Postgres ARRAY if desired.
    baseline_vector = Column(JSON, nullable=True)
    refined_vector = Column(JSON, nullable=True)
    engagement_score = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="taste_profile")


class UserArtworkInteraction(Base):
    __tablename__ = "user_artwork_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    artwork_id = Column(String, index=True)
    rating = Column(Integer)  # -1 dislike, 0 neutral, 1 like
    source = Column(String, default="quiz")  # "quiz" | "feed" | "museum" ...
    dwell_time = Column(Float, nullable=True)  # seconds
    viewed_at = Column(DateTime, default=datetime.utcnow)
    extra = Column(JSON, nullable=True)  # free-form metadata

    user = relationship("User", back_populates="interactions")
