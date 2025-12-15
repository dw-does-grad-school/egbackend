# app/schemas.py
from typing import List, Optional
from pydantic import BaseModel


class QuizAnswer(BaseModel):
    artwork_id: str
    rating: int  # -1, 0, 1


class TasteQuizRequest(BaseModel):
    # this should match Clerk user ID on the frontend
    user_external_id: str
    display_name: Optional[str] = None
    answers: List[QuizAnswer]


class TasteProfileResponse(BaseModel):
    user_external_id: str
    baseline_vector: Optional[List[float]] = None
    refined_vector: Optional[List[float]] = None
    engagement_score: float
