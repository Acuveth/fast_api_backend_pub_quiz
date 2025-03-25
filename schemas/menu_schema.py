from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal

# Menu Item Option Schema
class MenuItemOptionBase(BaseModel):
    name: str
    price_addition: Decimal = Decimal('0.00')

class MenuItemOptionCreate(MenuItemOptionBase):
    pass

class MenuItemOption(MenuItemOptionBase):
    id: int
    menu_item_id: int
    
    class Config:
        orm_mode = True

# Menu Item Schema
class MenuItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    image_path: Optional[str] = None
    is_available: bool = True
    is_popular: bool = False
    display_order: int = 0

class MenuItemCreate(MenuItemBase):
    category_id: int
    options: Optional[List[MenuItemOptionCreate]] = None

class MenuItem(MenuItemBase):
    id: int
    category_id: int
    options: List[MenuItemOption] = []
    
    class Config:
        orm_mode = True

class MenuItemResponse(MenuItem):
    pass

# Menu Category Schema
class MenuCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    display_order: int = 0

class MenuCategoryCreate(MenuCategoryBase):
    pass

class MenuCategory(MenuCategoryBase):
    id: int
    items: List[MenuItem] = []
    
    class Config:
        orm_mode = True

# Room Menu Settings Schema
class RoomMenuSettingsBase(BaseModel):
    show_menu: bool = True
    menu_description: Optional[str] = None

class RoomMenuSettingsCreate(RoomMenuSettingsBase):
    room_id: str

class RoomMenuSettings(RoomMenuSettingsBase):
    room_id: str
    
    class Config:
        orm_mode = True

# Menu Response Schema - for frontend
class MenuResponse(BaseModel):
    categories: List[MenuCategory]
    description: Optional[str] = None