from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from db.database import get_db
from db.models import Room
from db.models_menu import RoomMenuSettings
from schemas.schema import RoomBase, RoomCreate, RoomResponse, RoomMenuSettingBase, RoomMenuSettingCreate, RoomMenuSettingResponse

router = APIRouter(
    prefix="/api/rooms",
    tags=["rooms"],
    responses={404: {"description": "Not found"}}
)

# Room endpoints
@router.get("/", response_model=List[RoomResponse])
async def get_rooms(db: Session = Depends(get_db)):
    rooms = db.query(Room).all()
    # Convert datetime to string if needed
    for room in rooms:
        if isinstance(room.created_at, datetime):
            room.created_at = room.created_at.isoformat()
    return rooms

def serialize_room(room):
    """Convert SQLAlchemy Room model to a dictionary with proper string dates."""
    room_dict = {
        "id": room.id,
        "name": room.name,
        "is_active": room.is_active,
        "created_at": room.created_at.isoformat() if isinstance(room.created_at, datetime) else room.created_at
    }
    return room_dict

@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(room_id: str, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return serialize_room(room)

@router.post("/", response_model=RoomResponse)
async def create_room(room: RoomCreate, db: Session = Depends(get_db)):
    # Check if room with this ID already exists
    db_room = db.query(Room).filter(Room.id == room.id).first()
    if db_room:
        raise HTTPException(status_code=400, detail="Room with this ID already exists")
    
    # Create new room
    db_room = Room(**room.dict())
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

@router.put("/{room_id}", response_model=RoomResponse)
async def update_room(room_id: str, room_data: RoomCreate, db: Session = Depends(get_db)):
    db_room = db.query(Room).filter(Room.id == room_id).first()
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Update room attributes (except id which is the primary key)
    db_room.name = room_data.name
    db_room.is_active = room_data.is_active
    
    db.commit()
    db.refresh(db_room)
    return db_room

@router.delete("/{room_id}")
async def delete_room(room_id: str, db: Session = Depends(get_db)):
    db_room = db.query(Room).filter(Room.id == room_id).first()
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    db.delete(db_room)
    db.commit()
    return {"message": "Room deleted successfully"}

# Room Menu Settings endpoints
@router.get("/menu-settings", response_model=List[RoomMenuSettingResponse])
async def get_all_room_menu_settings(db: Session = Depends(get_db)):
    return db.query(RoomMenuSettings).all()

@router.get("/menu-settings/{room_id}", response_model=RoomMenuSettingResponse)
async def get_room_menu_settings(room_id: str, db: Session = Depends(get_db)):
    settings = db.query(RoomMenuSettings).filter(RoomMenuSettings.room_id == room_id).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Room menu settings not found")
    return settings

@router.post("/menu-settings", response_model=RoomMenuSettingResponse)
async def create_room_menu_settings(settings: RoomMenuSettingCreate, db: Session = Depends(get_db)):
    # Check if the room exists
    room = db.query(Room).filter(Room.id == settings.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Check if settings already exist for this room
    existing_settings = db.query(RoomMenuSettings).filter(RoomMenuSettings.room_id == settings.room_id).first()
    if existing_settings:
        raise HTTPException(status_code=400, detail="Settings for this room already exist")
    
    # Create new settings
    db_settings = RoomMenuSettings(**settings.dict())
    db.add(db_settings)
    db.commit()
    db.refresh(db_settings)
    return db_settings

@router.put("/menu-settings/{room_id}", response_model=RoomMenuSettingResponse)
async def update_room_menu_settings(room_id: str, settings_data: RoomMenuSettingCreate, db: Session = Depends(get_db)):
    # Check if the room exists
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Check if settings exist
    db_settings = db.query(RoomMenuSettings).filter(RoomMenuSettings.room_id == room_id).first()
    
    if db_settings:
        # Update existing settings
        db_settings.show_menu = settings_data.show_menu
        db_settings.menu_id = settings_data.menu_id
        db_settings.menu_description = settings_data.menu_description
    else:
        # Create new settings if they don't exist
        db_settings = RoomMenuSettings(**settings_data.dict())
        db.add(db_settings)
    
    db.commit()
    db.refresh(db_settings)
    return db_settings

@router.delete("/menu-settings/{room_id}")
async def delete_room_menu_settings(room_id: str, db: Session = Depends(get_db)):
    db_settings = db.query(RoomMenuSettings).filter(RoomMenuSettings.room_id == room_id).first()
    if not db_settings:
        raise HTTPException(status_code=404, detail="Room menu settings not found")
    
    db.delete(db_settings)
    db.commit()
    return {"message": "Room menu settings deleted successfully"}