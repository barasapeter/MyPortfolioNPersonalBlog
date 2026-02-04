from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.item import Item, ItemCreate, ItemUpdate
from app.models.item import Item as ItemModel

router = APIRouter()

@router.get("/", response_model=List[Item])
def read_items(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve items.
    """
    items = db.query(ItemModel).offset(skip).limit(limit).all()
    return items

@router.post("/", response_model=Item)
def create_item(
    *,
    db: Session = Depends(deps.get_db),
    item_in: ItemCreate,
) -> Any:
    """
    Create new item.
    """
    item = ItemModel(title=item_in.title, description=item_in.description, is_active=item_in.is_active)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
