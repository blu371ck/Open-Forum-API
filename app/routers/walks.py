from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.auth import get_current_active_user
from app.database import get_db
from app.models import User as UserModel
from app.models import UserRole
from app.models import Walk as WalkModel
from app.schemas import StatusResponse
from app.schemas import Walk as WalkSchema
from app.schemas import WalkCreate, WalkUpdate

router = APIRouter(
    prefix="/walks", tags=["walks"], responses={404: {"description": "Not found"}}
)


@router.post(
    "/", response_model=WalkSchema, status_code=status.HTTP_201_CREATED, tags=["walks"]
)
async def create_new_walk(
    walk_data: WalkCreate,
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> WalkModel:
    """
    Creates a new walk.
    """
    new_walk = WalkModel(
        **walk_data.model_dump(), creator_id=current_user.id, owner_id=current_user.id
    )
    db.add(new_walk)
    db.commit()
    db.refresh(new_walk)
    return new_walk


@router.get("/{walk_id}", response_model=WalkSchema, tags=["walks"])
async def get_specific_walk(
    walk_id: Annotated[int, Path(title="The ID of the walk to retrieve.", gt=0)],
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> WalkModel:
    """
    Retrieves a specific walk by ID. Requires authentication.
    """
    walk = db.query(WalkModel).filter(WalkModel.id == walk_id).first()

    if walk is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Walk with ID {walk_id} not found",
        )

    return walk


@router.patch(
    "/{walk_id}/archive",
    status_code=status.HTTP_200_OK,
    tags=["walks"],
    response_model=StatusResponse,
)
async def archive_walk(
    walk_id: Annotated[int, Path(title="The ID of the walk to archive.", gt=0)],
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> StatusResponse:
    """
    Archives a specific walk by ID. Requires authentication.
    """
    walk = db.query(WalkModel).filter(WalkModel.id == walk_id).first()
    if walk is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Walk not found"
        )

    is_admin = current_user.role == UserRole.DEVELOPER
    is_creator_or_owner = (
        walk.creator_id == current_user.id or walk.owner_id == current_user.id
    )
    if not (is_creator_or_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to archive this walk",
        )

    if walk.is_archived:
        return StatusResponse(status="success", message="Walk already archived")

    walk.is_archived = True
    db.commit()
    return StatusResponse(status="success", message="Walk archived successfully")


@router.put("/{walk_id}", response_model=WalkSchema, tags=["walks"])
async def update_walk(
    walk_id: Annotated[int, Path(title="The ID of the walk to update.", gt=0)],
    walk_update_data: WalkUpdate,
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> WalkModel:
    """
    Updates an exist walk and returns that walk.
    """
    db_walk = db.query(WalkModel).filter(WalkModel.id == walk_id).first()

    if db_walk is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Walk not found"
        )

    is_admin = current_user.role == UserRole.DEVELOPER
    is_creator_or_owner = (
        db_walk.creator_id == current_user.id or db_walk.owner_id == current_user.id
    )
    if not (is_creator_or_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this walk",
        )

    update_data = walk_update_data.model_dump(exclude_unset=True)

    if "owner_id" in update_data:
        new_owner_id = update_data["owner_id"]
        owner_exists = db.query(UserModel).filter(UserModel.id == new_owner_id).first()
        if not owner_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with owner_id {new_owner_id} does not exist.",
            )

    for key, value in update_data.items():
        setattr(db_walk, key, value)

    db.commit()
    db.refresh(db_walk)
    return db_walk
