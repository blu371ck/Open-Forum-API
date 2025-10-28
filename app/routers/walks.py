from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.auth import get_current_active_user
from app.database import get_db
from app.models import User as UserModel
from app.models import Walk as WalkModel
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


@router.delete("/{walk_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["walks"])
async def delete_walk(
    walk_id: Annotated[int, Path(title="The ID of the walk to delete.", gt=0)],
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> None:
    """
    Deletes a specific walk by ID. Requires authentication.
    """
    walk = db.query(WalkModel).filter_by(id=walk_id).first()

    if walk is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Walk with ID {walk_id} not found",
        )

    db.delete(walk)
    db.commit()


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

    if db_walk.creator_id != current_user.id and db_walk.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this walk.",
        )

    update_data = walk_update_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_walk, key, value)

    db.commit()
    db.refresh(db_walk)
    return db_walk
