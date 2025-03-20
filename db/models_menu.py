from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from db.database import Base

class MenuCategory(Base):
    __tablename__ = "menu_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    display_order = Column(Integer, default=0)
    created_at = Column(String)
    
    items = relationship("MenuItem", back_populates="category")

class MenuItem(Base):
    __tablename__ = "menu_items"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("menu_categories.id"))
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    image_path = Column(String(255), nullable=True)
    is_available = Column(Boolean, default=True)
    is_popular = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)
    created_at = Column(String)
    
    category = relationship("MenuCategory", back_populates="items")
    options = relationship("MenuItemOption", back_populates="menu_item")

class MenuItemOption(Base):
    __tablename__ = "menu_item_options"
    
    id = Column(Integer, primary_key=True, index=True)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"))
    name = Column(String(100), nullable=False)
    price_addition = Column(Numeric(10, 2), default=0.00)
    created_at = Column(String)
    
    menu_item = relationship("MenuItem", back_populates="options")

class RoomMenuSettings(Base):
    __tablename__ = "room_menu_settings"
    
    room_id = Column(String, ForeignKey("rooms.id"), primary_key=True)
    show_menu = Column(Boolean, default=True)
    menu_description = Column(Text, nullable=True)
    created_at = Column(String)
    
    room = relationship("Room", back_populates="menu_settings")

# Update Room model to include menu_settings relation
from db.models import Room
Room.menu_settings = relationship("RoomMenuSettings", back_populates="room", uselist=False)