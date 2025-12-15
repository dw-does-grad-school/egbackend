# app/crud.py
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from . import models, schemas

import numpy as np


def get_or_create_user(
    db: Session, external_id: str, display_name: Optional[str] = None
) -> models.User:
    user = (
        db.query(models.User).filter(models.User.external_id == external_id).first()
    )
    if user:
        return user

    user = models.User(external_id=external_id, display_name=display_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def record_quiz_interactions(
    db: Session, user: models.User, answers: List[schemas.QuizAnswer]
) -> None:
    for ans in answers:
        interaction = models.UserArtworkInteraction(
            user_id=user.id,
            artwork_id=ans.artwork_id,
            rating=ans.rating,
            source="quiz",
            viewed_at=datetime.utcnow(),
        )
        db.add(interaction)
    db.commit()


def compute_baseline_vector_stub(
    answers: List[schemas.QuizAnswer],
) -> Optional[List[float]]:
    """
    TODO: Replace this with real CLIP / embedding-based computation.

    For now we just create a tiny fake "vector" where:
    - one dimension = count of likes
    - one dimension = count of dislikes
    - one dimension = total answers
    and then pad to 8 dims for demo. In practice you'd return 512-dim CLIP vector.
    """
    if not answers:
        return None

    likes = sum(1 for a in answers if a.rating == 1)
    dislikes = sum(1 for a in answers if a.rating == -1)
    total = len(answers)

    vec = np.array([likes, dislikes, total] + [0.0] * 5, dtype=float)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm

    return vec.tolist()


def update_taste_profile_from_quiz(
    db: Session, user: models.User, answers: List[schemas.QuizAnswer]
) -> models.UserTasteProfile:
    # Get or create taste profile
    profile = (
        db.query(models.UserTasteProfile)
        .filter(models.UserTasteProfile.user_id == user.id)
        .first()
    )

    new_baseline = compute_baseline_vector_stub(answers)

    if profile is None:
        profile = models.UserTasteProfile(
            user_id=user.id,
            baseline_vector=new_baseline,
            refined_vector=new_baseline,
            engagement_score=_compute_engagement_from_answers(answers),
        )
        db.add(profile)
    else:
        # Blend new info into refined vector
        alpha = 0.1  # learning rate; tweak as needed
        if profile.refined_vector is None and new_baseline is not None:
            profile.refined_vector = new_baseline
        elif profile.refined_vector is not None and new_baseline is not None:
            old_vec = np.array(profile.refined_vector, dtype=float)
            new_vec = np.array(new_baseline, dtype=float)
            refined = (1 - alpha) * old_vec + alpha * new_vec
            # normalize
            norm = np.linalg.norm(refined)
            if norm > 0:
                refined = refined / norm
            profile.refined_vector = refined.tolist()

        # engagement accumulates over time
        profile.engagement_score += _compute_engagement_from_answers(answers)

    db.commit()
    db.refresh(profile)
    return profile


def _compute_engagement_from_answers(answers: List[schemas.QuizAnswer]) -> float:
    """
    Simple engagement scoring:
    - like = +1
    - neutral = 0
    - dislike = +0.2 (still an opinion)
    """
    score = 0.0
    for a in answers:
        if a.rating == 1:
            score += 1.0
        elif a.rating == -1:
            score += 0.2
    return score
