from datetime import timedelta
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_current_user,
)
from app.config import Settings, get_settings
from app.database import get_db
from app.models import Feedback
from app.models import User as UserModel
from app.models import Walk
from app.schemas import Feedback as FeedbackSchema
from app.schemas import Token, User
from app.schemas import Walk as WalkSchema

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@router.post("/auth", tags=["users"])
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Token:
    user = authenticate_user(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, settings=settings)
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me/", response_model=User, tags=["users"])
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    return current_user


@router.get("/me/walks", response_model=List[WalkSchema], tags=["users", "walks"])
async def read_my_walks(
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> List[Walk]:
    """
    Retrieves walks created or owned by the current logged in user.
    """
    walks = (
        db.query(Walk)
        .filter(
            (Walk.creator_id == current_user.id) | (Walk.owner_id == current_user.id)
        )
        .order_by(Walk.walk_date.desc())
        .all()
    )
    return walks


@router.get(
    "/me/feedback", response_model=List[FeedbackSchema], tags=["users", "feedback"]
)
async def read_my_feedback(
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> List[Feedback]:
    """
    Retrieves feedback created or owned by the current logged in user.
    """
    feedback_items = (
        db.query(Feedback)
        .filter(
            (Feedback.creator_id == current_user.id)
            | (Feedback.owner_id == current_user.id)
        )
        .order_by(Feedback.creation_date.desc())
        .all()
    )
    return feedback_items
