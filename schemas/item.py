from typing import Optional
from pydantic import BaseModel

class ItemBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = True

class ItemCreate(ItemBase):
    title: str

class ItemUpdate(ItemBase):
    pass

class Item(ItemBase):
    id: int

    class Config:
        from_attributes = True
