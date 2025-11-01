from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.auth import get_current_active_user
from app.database import get_db
from app.models import Feedback as FeedbackModel
from app.models import Tag as TagModel
from app.models import User as UserModel
from app.models import UserRole
from app.models import Walk as WalkModel
from app.schemas import Feedback as FeedbackSchema
from app.schemas import FeedbackCreate, FeedbackUpdate, StatusResponse

router = APIRouter(
    prefix="/feedback", tags=["feedback"], responses={404: {"description": "Not found"}}
)


@router.post(
    "/",
    response_model=FeedbackSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["feedback"],
)
async def create_new_feedback(
    feedback_data: FeedbackCreate,
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> FeedbackModel:
    """
    Creates new feedback. The creator_id is always set up to the logged-in user. The
    is_anonymous flag determines if the creator's name is hidden.
    """
    feedback_dict = feedback_data.model_dump(exclude={"tags_id"})
    tag_ids = feedback_data.tags_id

    walk = (
        db.query(WalkModel)
        .filter(WalkModel.id == feedback_data.walk_id, WalkModel.is_archived == False)
        .first()
    )

    if walk is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active walk with ID {feedback_data.walk_id} not found.",
        )

    new_feedback = FeedbackModel(**feedback_dict, creator_id=current_user.id)

    if tag_ids:
        tags = db.query(TagModel).filter(TagModel.id.in_(tag_ids)).all()
        if len(tags) != len(set(tag_ids)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more provided tag IDs are invalid.",
            )
        new_feedback.tags = tags

    db.add(new_feedback)
    db.commit()
    db.refresh(new_feedback)
    return new_feedback


@router.get("/{feedback_id}", response_model=FeedbackSchema, tags=["feedback"])
async def get_specific_feedback(
    feedback_id: Annotated[
        int, Path(title="The ID of the feedback to retrieve.", gt=0)
    ],
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> FeedbackModel:
    """
    Retrieves a specific feedback by ID. Requires authentication.
    """
    feedback = (
        db.query(FeedbackModel)
        .filter(FeedbackModel.id == feedback_id, FeedbackModel.is_archived == False)
        .first()
    )

    if feedback is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback with ID {feedback_id} not found",
        )

    return feedback


@router.patch(
    "/{feedback_id}/archive",
    status_code=status.HTTP_200_OK,
    tags=["feedback"],
    response_model=StatusResponse,
)
async def archive_feedback(
    feedback_id: Annotated[int, Path(title="The ID of the feedback to archive.", gt=0)],
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> StatusResponse:
    """
    Archives a specific feedback by ID. Requires authentication.
    """
    feedback = db.query(FeedbackModel).filter(FeedbackModel.id == feedback_id).first()
    if feedback is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found"
        )

    is_admin = current_user.role == UserRole.DEVELOPER
    is_creator_or_owner = (
        feedback.creator_id == current_user.id or feedback.owner_id == current_user.id
    )
    if not (is_creator_or_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to archive this feedback",
        )

    if feedback.is_archived:
        return StatusResponse(status="success", message="Feedback already archived")

    feedback.is_archived = True
    db.commit()
    return StatusResponse(status="success", message="Feedback archived successfully")


@router.put("/{feedback_id}", response_model=FeedbackSchema, tags=["feedback"])
async def update_feedback(
    feedback_id: Annotated[int, Path(title="The ID of the feedback to update.", gt=0)],
    feedback_update_data: FeedbackUpdate,
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> FeedbackModel:
    """
    Updates an existing feedback and returns that feedback.
    """
    db_feedback = (
        db.query(FeedbackModel).filter(FeedbackModel.id == feedback_id).first()
    )

    if db_feedback is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found"
        )

    if db_feedback.is_archived:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify archived feedback.",
        )

    is_admin = current_user.role in (
        UserRole.MANAGER,
        UserRole.EXECUTIVE,
        UserRole.DEVELOPER,
    )
    is_owner = db_feedback.owner_id == current_user.id

    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this feedback",
        )

    update_data = feedback_update_data.model_dump(exclude_unset=True)

    if "owner_id" in update_data:
        new_owner_id = update_data["owner_id"]
        owner_exists = db.query(UserModel).filter(UserModel.id == new_owner_id).first()
        if not owner_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with owner_id {new_owner_id} does not exist.",
            )

    for key, value in update_data.items():
        setattr(db_feedback, key, value)

    db.commit()
    db.refresh(db_feedback)
    return db_feedback
