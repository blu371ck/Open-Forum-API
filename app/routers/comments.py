from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.auth import get_current_active_user
from app.database import get_db
from app.models import Comment as CommentModel
from app.models import Feedback as FeedbackModel
from app.models import User as UserModel
from app.models import UserRole
from app.schemas import Comment as CommentSchema
from app.schemas import CommentCreate, CommentUpdate

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post(
    "/feedback/{feedback_id}/comments",
    response_model=CommentSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_new_comment(
    feedback_id: Annotated[
        int, Path(title="The ID of the feedback to comment on.", gt=0)
    ],
    comment_data: CommentCreate,
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> CommentModel:
    """
    Creates a new comment on a specific feedback item.
    """

    feedback = (
        db.query(FeedbackModel)
        .filter(FeedbackModel.id == feedback_id, FeedbackModel.is_archived == False)
        .first()
    )

    if feedback is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active feedback with ID {feedback_id} not found.",
        )

    new_comment = CommentModel(
        text=comment_data.text, feedback_id=feedback_id, author_id=current_user.id
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment


@router.put("/{comment_id}", response_model=CommentSchema)
async def update_comment(
    comment_id: Annotated[int, Path(title="The ID of the comment to udpate.", gt=0)],
    comment_data: CommentUpdate,
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> CommentModel:
    """
    Updates an existing comment. Only the author can update their own comments.
    """

    db_comment = db.query(CommentModel).filter(CommentModel.id == comment_id).first()

    if db_comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )

    # Authorization: Only the author can update
    if db_comment.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this comment",
        )

    # Check if parent feedback is archived
    if db_comment.feedback.is_archived:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify comments on an archived feedback item",
        )

    db_comment.text = comment_data.text
    db.commit()
    db.refresh(db_comment)
    return db_comment


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: Annotated[int, Path(title="The ID of the comment to archive.", gt=0)],
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> None:
    """
    Deletes a comment. Only the author or a Developer can delete.
    """

    db_comment = db.query(CommentModel).filter(CommentModel.id == comment_id).first()

    if db_comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )

    # Authorization: Author or developer (in the event the author is malicious or outside of org)
    is_author = db_comment.author_id == current_user.id
    is_developer = current_user.role == UserRole.DEVELOPER

    if not (is_author or is_developer):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this comment",
        )

    db.delete(db_comment)
    db.commit()
    return None
