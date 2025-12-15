# app/main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from . import schemas, crud, models

# Create tables on startup for now (for dev).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="EchoGallery Taste Backend",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/taste/quiz", response_model=schemas.TasteProfileResponse)
def submit_taste_quiz(
    payload: schemas.TasteQuizRequest,
    db: Session = Depends(get_db),
):
    if not payload.answers:
        raise HTTPException(status_code=400, detail="No answers provided.")

    # Find or create user by external ID (e.g. Clerk ID)
    user = crud.get_or_create_user(
        db, external_id=payload.user_external_id, display_name=payload.display_name
    )

    # Record raw interactions
    crud.record_quiz_interactions(db, user, payload.answers)

    # Update taste profile
    profile = crud.update_taste_profile_from_quiz(db, user, payload.answers)

    return schemas.TasteProfileResponse(
        user_external_id=user.external_id,
        baseline_vector=profile.baseline_vector,
        refined_vector=profile.refined_vector,
        engagement_score=profile.engagement_score,
    )


@app.get("/taste/profile/{user_external_id}", response_model=schemas.TasteProfileResponse)
def get_taste_profile(
    user_external_id: str,
    db: Session = Depends(get_db),
):
    user = (
        db.query(models.User)
        .filter(models.User.external_id == user_external_id)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = user.taste_profile
    if not profile:
        # user exists but has no quiz yet
        return schemas.TasteProfileResponse(
            user_external_id=user.external_id,
            baseline_vector=None,
            refined_vector=None,
            engagement_score=0.0,
        )

    return schemas.TasteProfileResponse(
        user_external_id=user.external_id,
        baseline_vector=profile.baseline_vector,
        refined_vector=profile.refined_vector,
        engagement_score=profile.engagement_score,
    )
