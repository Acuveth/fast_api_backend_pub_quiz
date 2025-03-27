from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from db.models_menu import MenuCategory, MenuItem, MenuItemOption, RoomMenuSettings
from schemas.menu_schema import (
    MenuCategoryCreate, MenuItemCreate, MenuItemOptionCreate, 
    RoomMenuSettingsCreate, MenuResponse
)
from datetime import datetime

class MenuService:
    # Menu Category methods
    @staticmethod
    async def get_categories(db: Session, skip: int = 0, limit: int = 100):
        return db.query(MenuCategory).order_by(MenuCategory.display_order).offset(skip).limit(limit).all()

    @staticmethod
    async def get_category(db: Session, category_id: int):
        return db.query(MenuCategory).filter(MenuCategory.id == category_id).first()

    @staticmethod
    async def create_category(db: Session, category: MenuCategoryCreate):
        current_time = datetime.utcnow().isoformat()
        db_category = MenuCategory(
            name=category.name,
            description=category.description,
            display_order=category.display_order,
            created_at=current_time
        )
        db.add(db_category)
        try:
            db.commit()
            db.refresh(db_category)
            return db_category
        except SQLAlchemyError as e:
            db.rollback()
            raise e

    @staticmethod
    async def update_category(db: Session, category_id: int, category_data: dict):
        db_category = db.query(MenuCategory).filter(MenuCategory.id == category_id).first()
        if not db_category:
            return None

        for key, value in category_data.items():
            if hasattr(db_category, key):
                setattr(db_category, key, value)

        try:
            db.commit()
            db.refresh(db_category)
            return db_category
        except SQLAlchemyError as e:
            db.rollback()
            raise e

    @staticmethod
    async def delete_category(db: Session, category_id: int):
        db_category = db.query(MenuCategory).filter(MenuCategory.id == category_id).first()
        if not db_category:
            return False
        
        db.delete(db_category)
        try:
            db.commit()
            return True
        except SQLAlchemyError:
            db.rollback()
            return False

    # Menu Item methods
    @staticmethod
    async def get_items(db: Session, category_id: Optional[int] = None, skip: int = 0, limit: int = 100):
        query = db.query(MenuItem)
        if category_id is not None:
            query = query.filter(MenuItem.category_id == category_id)
        return query.order_by(MenuItem.category_id, MenuItem.display_order).offset(skip).limit(limit).all()

    @staticmethod
    async def get_item(db: Session, item_id: int):
        return db.query(MenuItem).filter(MenuItem.id == item_id).first()

    @staticmethod
    async def create_item(db: Session, item: MenuItemCreate):
        current_time = datetime.utcnow().isoformat()
        db_item = MenuItem(
            category_id=item.category_id,
            name=item.name,
            description=item.description,
            price=item.price,
            image_path=item.image_path,
            is_available=item.is_available,
            is_popular=item.is_popular,
            display_order=item.display_order,
            created_at=current_time
        )
        db.add(db_item)
        db.flush()

        if item.options:
            for option in item.options:
                db_option = MenuItemOption(
                    menu_item_id=db_item.id,
                    name=option.name,
                    price_addition=option.price_addition,
                    created_at=current_time
                )
                db.add(db_option)

        try:
            db.commit()
            db.refresh(db_item)
            return db_item
        except SQLAlchemyError as e:
            db.rollback()
            raise e

    @staticmethod
    async def update_item(db: Session, item_id: int, item_data: dict):
        db_item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
        if not db_item:
            return None

        for key, value in item_data.items():
            if key != "options" and hasattr(db_item, key):
                setattr(db_item, key, value)

        # Handle options if provided
        if "options" in item_data:
            # Delete existing options and add new ones
            db.query(MenuItemOption).filter(MenuItemOption.menu_item_id == item_id).delete()
            
            current_time = datetime.utcnow().isoformat()
            for option_data in item_data["options"]:
                db_option = MenuItemOption(
                    menu_item_id=db_item.id,
                    name=option_data["name"],
                    price_addition=option_data["price_addition"],
                    created_at=current_time
                )
                db.add(db_option)

        try:
            db.commit()
            db.refresh(db_item)
            return db_item
        except SQLAlchemyError as e:
            db.rollback()
            raise e

    @staticmethod
    async def delete_item(db: Session, item_id: int):
        db_item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
        if not db_item:
            return False
        
        db.delete(db_item)
        try:
            db.commit()
            return True
        except SQLAlchemyError:
            db.rollback()
            return False

    # Menu Item Option methods
    @staticmethod
    async def get_options(db: Session, item_id: Optional[int] = None, skip: int = 0, limit: int = 100):
        query = db.query(MenuItemOption)
        if item_id is not None:
            query = query.filter(MenuItemOption.menu_item_id == item_id)
        return query.offset(skip).limit(limit).all()

    @staticmethod
    async def get_option(db: Session, option_id: int):
        return db.query(MenuItemOption).filter(MenuItemOption.id == option_id).first()

    @staticmethod
    async def create_option(db: Session, item_id: int, option: MenuItemOptionCreate):
        current_time = datetime.utcnow().isoformat()
        db_option = MenuItemOption(
            menu_item_id=item_id,
            name=option.name,
            price_addition=option.price_addition,
            created_at=current_time
        )
        db.add(db_option)
        try:
            db.commit()
            db.refresh(db_option)
            return db_option
        except SQLAlchemyError as e:
            db.rollback()
            raise e

    @staticmethod
    async def update_option(db: Session, option_id: int, option_data: dict):
        db_option = db.query(MenuItemOption).filter(MenuItemOption.id == option_id).first()
        if not db_option:
            return None

        for key, value in option_data.items():
            if hasattr(db_option, key):
                setattr(db_option, key, value)

        try:
            db.commit()
            db.refresh(db_option)
            return db_option
        except SQLAlchemyError as e:
            db.rollback()
            raise e

    @staticmethod
    async def delete_option(db: Session, option_id: int):
        db_option = db.query(MenuItemOption).filter(MenuItemOption.id == option_id).first()
        if not db_option:
            return False
        
        db.delete(db_option)
        try:
            db.commit()
            return True
        except SQLAlchemyError:
            db.rollback()
            return False

    # Room Menu Settings methods
    @staticmethod
    async def get_room_menu_settings(db: Session, room_id: str):
        return db.query(RoomMenuSettings).filter(RoomMenuSettings.room_id == room_id).first()

    @staticmethod
    async def create_or_update_room_menu_settings(db: Session, settings: RoomMenuSettingsCreate):
        current_time = datetime.utcnow().isoformat()
        db_settings = db.query(RoomMenuSettings).filter(RoomMenuSettings.room_id == settings.room_id).first()
        
        if db_settings:
            # Update existing settings
            db_settings.show_menu = settings.show_menu
            db_settings.menu_description = settings.menu_description
        else:
            # Create new settings
            db_settings = RoomMenuSettings(
                room_id=settings.room_id,
                show_menu=settings.show_menu,
                menu_description=settings.menu_description,
                created_at=current_time
            )
            db.add(db_settings)
            
        try:
            db.commit()
            db.refresh(db_settings)
            return db_settings
        except SQLAlchemyError as e:
            db.rollback()
            raise e

    # Get menu for a room (frontend response)
    @staticmethod
    async def get_menu_for_room(db: Session, room_id: str):
        # Get room menu settings
        settings = await MenuService.get_room_menu_settings(db, room_id)
        
        if not settings or not settings.show_menu:
            return None
            
        # Get all categories with their items
        categories = db.query(MenuCategory).order_by(MenuCategory.display_order).all()
        
        # Return a MenuResponse
        return MenuResponse(
            categories=categories,
            description=settings.menu_description if settings else None
        )