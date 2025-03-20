from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from db.database import get_db
from db.models_menu import MenuCategory, MenuItem, MenuItemOption, RoomMenuSettings
from schemas.menu_schema import (
    MenuCategory as MenuCategorySchema,
    MenuItem as MenuItemSchema,
    MenuItemOption as MenuItemOptionSchema,
    MenuItemCreate,
    MenuCategoryCreate,
    MenuOptionCreate,
    MenuResponse,
    RoomMenuSettings as RoomMenuSettingsSchema,
    RoomMenuSettingsCreate
)
from services.menu_service import MenuService

router = APIRouter(
    prefix="/menu",
    tags=["menu"],
    responses={404: {"description": "Not found"}}
)

# Public endpoints for accessing menu
@router.get("/room/{room_id}", response_model=MenuResponse)
async def get_menu_for_room(room_id: str, db: Session = Depends(get_db)):
    """
    Get the menu for a specific room.
    Returns all categories and their menu items.
    """
    # Check if menu is enabled for this room
    room_settings = db.query(RoomMenuSettings).filter(RoomMenuSettings.room_id == room_id).first()
    
    if room_settings is None:
        # Create default settings if not exists
        room_settings = RoomMenuSettings(
            room_id=room_id,
            show_menu=True,
            created_at=datetime.utcnow().isoformat()
        )
        db.add(room_settings)
        db.commit()
        db.refresh(room_settings)
    
    if not room_settings.show_menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu is not available for this room"
        )
    
    # Get all categories with items
    categories = db.query(MenuCategory).order_by(MenuCategory.display_order).all()
    
    # Return categories and items
    return {
        "categories": categories,
        "description": room_settings.menu_description
    }

@router.get("/popular", response_model=List[MenuItemSchema])
async def get_popular_items(db: Session = Depends(get_db)):
    """Get popular menu items"""
    items = db.query(MenuItem).filter(
        MenuItem.is_popular == True,
        MenuItem.is_available == True
    ).order_by(MenuItem.display_order).all()
    
    return items

# ADMIN DASHBOARD ENDPOINTS

# Menu Category routes
@router.get("/categories", response_model=List[MenuCategorySchema])
async def read_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    categories = await MenuService.get_categories(db, skip=skip, limit=limit)
    return categories

@router.get("/categories/{category_id}", response_model=MenuCategorySchema)
async def read_category(category_id: int, db: Session = Depends(get_db)):
    category = await MenuService.get_category(db, category_id=category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.post("/categories", response_model=MenuCategorySchema, status_code=status.HTTP_201_CREATED)
async def create_category(category: MenuCategoryCreate, db: Session = Depends(get_db)):
    try:
        return await MenuService.create_category(db=db, category=category)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/categories/{category_id}", response_model=MenuCategorySchema)
async def update_category(category_id: int, category_data: dict, db: Session = Depends(get_db)):
    updated_category = await MenuService.update_category(db, category_id=category_id, category_data=category_data)
    if updated_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return updated_category

@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: int, db: Session = Depends(get_db)):
    success = await MenuService.delete_category(db, category_id=category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return None

# Menu Item routes
@router.get("/items", response_model=List[MenuItemSchema])
async def read_items(category_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = await MenuService.get_items(db, category_id=category_id, skip=skip, limit=limit)
    return items

@router.get("/items/{item_id}", response_model=MenuItemSchema)
async def read_item(item_id: int, db: Session = Depends(get_db)):
    item = await MenuService.get_item(db, item_id=item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return item

@router.post("/items", response_model=MenuItemSchema, status_code=status.HTTP_201_CREATED)
async def create_item(item: MenuItemCreate, db: Session = Depends(get_db)):
    try:
        return await MenuService.create_item(db=db, item=item)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/items/{item_id}", response_model=MenuItemSchema)
async def update_item(item_id: int, item_data: dict, db: Session = Depends(get_db)):
    updated_item = await MenuService.update_item(db, item_id=item_id, item_data=item_data)
    if updated_item is None:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return updated_item

@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int, db: Session = Depends(get_db)):
    success = await MenuService.delete_item(db, item_id=item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return None

# Menu Item Option routes
@router.get("/options", response_model=List[MenuItemOptionSchema])
async def read_options(item_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    options = await MenuService.get_options(db, item_id=item_id, skip=skip, limit=limit)
    return options

@router.get("/options/{option_id}", response_model=MenuItemOptionSchema)
async def read_option(option_id: int, db: Session = Depends(get_db)):
    option = await MenuService.get_option(db, option_id=option_id)
    if option is None:
        raise HTTPException(status_code=404, detail="Menu option not found")
    return option

@router.post("/items/{item_id}/options", response_model=MenuItemOptionSchema, status_code=status.HTTP_201_CREATED)
async def create_option(item_id: int, option: MenuOptionCreate, db: Session = Depends(get_db)):
    try:
        return await MenuService.create_option(db=db, item_id=item_id, option=option)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/options/{option_id}", response_model=MenuItemOptionSchema)
async def update_option(option_id: int, option_data: dict, db: Session = Depends(get_db)):
    updated_option = await MenuService.update_option(db, option_id=option_id, option_data=option_data)
    if updated_option is None:
        raise HTTPException(status_code=404, detail="Menu option not found")
    return updated_option

@router.delete("/options/{option_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_option(option_id: int, db: Session = Depends(get_db)):
    success = await MenuService.delete_option(db, option_id=option_id)
    if not success:
        raise HTTPException(status_code=404, detail="Menu option not found")
    return None

# Room Menu Settings
@router.get("/settings/{room_id}", response_model=RoomMenuSettingsSchema)
async def get_room_menu_settings(room_id: str, db: Session = Depends(get_db)):
    settings = await MenuService.get_room_menu_settings(db, room_id=room_id)
    if settings is None:
        # Return default settings if none exist
        return RoomMenuSettingsSchema(
            room_id=room_id,
            show_menu=True,
            menu_description=None
        )
    return settings

@router.post("/settings", response_model=RoomMenuSettingsSchema)
async def create_or_update_menu_settings(settings: RoomMenuSettingsCreate, db: Session = Depends(get_db)):
    try:
        return await MenuService.create_or_update_room_menu_settings(db=db, settings=settings)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))