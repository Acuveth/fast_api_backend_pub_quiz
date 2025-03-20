from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
import os
from typing import Optional

from config import settings
from db.database import get_db
from db.models import Room, Team, TeamRoomParticipation
from schemas.schema import LoginRequest, LoginResponse, TeamProfileUpdate, TeamDetail
from api.auth import verify_password, get_password_hash, create_access_token, get_current_team_id

router = APIRouter(tags=["authentication"])

@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Login endpoint for teams to join a quiz room.
    
    - Checks if the room ID exists in the database
    - Checks if a team with the given name exists globally
    - If the team exists, verifies password and adds team to room if not already participating
    - If not, creates a new team and adds it to the room
    - Returns a JWT token for authentication and the team data
    """
    # Check if room exists
    room = db.query(Room).filter(Room.id == login_data.room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found. Please check the Room ID.",
        )
    
    # Check if team exists globally
    team = db.query(Team).filter(
        Team.name == login_data.team_name
    ).first()
    
    if team:
        # Verify password for existing team
        if not verify_password(login_data.password, team.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password for the existing team.",
            )
        
        # Check if team is already participating in this room
        participation = db.query(TeamRoomParticipation).filter(
            TeamRoomParticipation.team_id == team.id,
            TeamRoomParticipation.room_id == room.id
        ).first()
        
        if not participation:
            # Add team to room if not already participating
            participation = TeamRoomParticipation(
                team_id=team.id,
                room_id=room.id,
                joined_at=datetime.utcnow().isoformat()
            )
            db.add(participation)
            db.commit()
    else:
        # Create new team if it doesn't exist
        hashed_password = get_password_hash(login_data.password)
        team = Team(
            name=login_data.team_name,
            password=hashed_password,
            total_points=0,
            created_at=datetime.utcnow().isoformat()
        )
        db.add(team)
        db.commit()
        db.refresh(team)
        
        # Add new team to the room
        participation = TeamRoomParticipation(
            team_id=team.id,
            room_id=room.id,
            joined_at=datetime.utcnow().isoformat()
        )
        db.add(participation)
        db.commit()
    
    # Generate JWT token for authentication
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(team.id), "room": room.id, "team": team.name},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "team": team,
        "room": room
    }

@router.put("/teams/profile", response_model=TeamDetail)
async def update_team_profile(
    profile_data: TeamProfileUpdate,
    db: Session = Depends(get_db),
    team_id: int = Depends(get_current_team_id)
):
    """Update team profile information (slogan)"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if profile_data.slogan is not None:
        team.slogan = profile_data.slogan
    
    db.commit()
    db.refresh(team)
    
    return team

@router.post("/teams/profile-picture", response_model=TeamDetail)
async def upload_profile_picture(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    team_id: int = Depends(get_current_team_id)
):
    """Upload team profile picture"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Validate file is an image
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400, 
            detail="File must be an image"
        )
    
    # Create profiles directory if it doesn't exist
    os.makedirs("static/profiles", exist_ok=True)
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"team_{team_id}_{datetime.utcnow().timestamp()}{file_extension}"
    file_path = f"static/profiles/{filename}"
    
    # Save file
    with open(file_path, "wb") as f:
        contents = await file.read()
        f.write(contents)
    
    # Update team profile_picture
    team.profile_picture = f"/profiles/{filename}"
    db.commit()
    db.refresh(team)
    
    return team