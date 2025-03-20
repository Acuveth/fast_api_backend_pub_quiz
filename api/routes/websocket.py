from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
import json
from typing import List, Dict, Any
from datetime import datetime

from db.database import get_db
from db.models import Room, Team, Question, Answer, TeamRoomParticipation, QuestionOption
from services.websocket import ConnectionManager

router = APIRouter(tags=["websocket"])
manager = ConnectionManager()

@router.websocket("/ws/{room_id}/{team_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    room_id: str, 
    team_id: int, 
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for connecting teams to a room.
    
    - Verifies room and team existence
    - Handles team chat messages
    - Receives and processes quiz questions and answers
    """
    # Verify room and team
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Check if team is participating in this room
    participation = db.query(TeamRoomParticipation).filter(
        TeamRoomParticipation.team_id == team_id,
        TeamRoomParticipation.room_id == room_id
    ).first()
    
    if not participation:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    await manager.connect(websocket, room_id)
    
    try:
        # Send team profile and points information
        await websocket.send_json({
            "type": "team_info",
            "team_id": team.id,
            "team_name": team.name,
            "profile_picture": team.profile_picture,
            "slogan": team.slogan,
            "room_points": participation.points,
            "total_points": team.total_points
        })
        
        # Announce team joined
        await manager.broadcast_json(
            {
                "type": "system_message",
                "message": f"Team {team.name} joined the room!"
            },
            room_id
        )
        
        # Send leaderboard data
        await send_leaderboard(db, room_id, websocket)
        
        # Send active question if any
        active_question = db.query(Question).filter(
            Question.room_id == room_id,
            Question.is_active == True
        ).first()
        
        if active_question:
            await send_question(websocket, active_question, db)
        
        # Listen for messages
        while True:
            data = await websocket.receive_text()
            # Process message (chat or answer)
            try:
                message_data = json.loads(data)
                
                if message_data.get("type") == "chat":
                    # Broadcast chat message to all teams in the room
                    await manager.broadcast_json(
                        {
                            "type": "chat",
                            "team_id": team.id,
                            "team_name": team.name,
                            "profile_picture": team.profile_picture,
                            "message": message_data.get("message", "")
                        },
                        room_id
                    )
                elif message_data.get("type") == "answer":
                    # Process answer to question
                    await process_answer(
                        db, 
                        team, 
                        participation,
                        message_data, 
                        websocket, 
                        room_id
                    )
            except json.JSONDecodeError:
                # If not JSON, treat as plain chat message
                await manager.broadcast_json(
                    {
                        "type": "chat",
                        "team_id": team.id,
                        "team_name": team.name,
                        "profile_picture": team.profile_picture,
                        "message": data
                    },
                    room_id
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        await manager.broadcast_json(
            {
                "type": "system_message",
                "message": f"Team {team.name} left the room!"
            },
            room_id
        )

async def send_question(websocket: WebSocket, question: Question, db: Session):
    """Format and send a question to the client"""
    question_data = {
        "type": "question",
        "id": question.id,
        "text": question.text,
        "question_type": question.question_type,
        "points": question.points,
        "time_limit": question.time_limit
    }
    
    # Add options for multiple choice questions
    if question.question_type == "MULTIPLE_CHOICE":
        options = db.query(QuestionOption).filter(
            QuestionOption.question_id == question.id
        ).all()
        
        question_data["options"] = [
            {"letter": opt.option_letter, "text": opt.option_text}
            for opt in options
        ]
    
    await websocket.send_json(question_data)

async def process_answer(
    db: Session, 
    team: Team, 
    participation: TeamRoomParticipation,
    message_data: Dict[str, Any], 
    websocket: WebSocket, 
    room_id: str
):
    """Process a team's answer to a question"""
    question_id = message_data.get("question_id")
    answer_text = message_data.get("answer", "")
    
    question = db.query(Question).filter(
        Question.id == question_id,
        Question.room_id == room_id,
        Question.is_active == True
    ).first()
    
    if question:
        # Check if team already answered
        existing_answer = db.query(Answer).filter(
            Answer.team_id == team.id,
            Answer.question_id == question.id
        ).first()
        
        is_correct = False
        if question.question_type == "MULTIPLE_CHOICE":
            # For multiple choice, compare the letter (A, B, C, D)
            is_correct = answer_text.upper() == question.correct_answer.upper()
        else:
            # For text answers, do case insensitive comparison
            is_correct = answer_text.lower() == question.correct_answer.lower()
        
        if existing_answer:
            # Update existing answer
            existing_answer.text = answer_text
            existing_answer.is_correct = is_correct
            db.commit()
        else:
            # Create new answer
            new_answer = Answer(
                team_id=team.id,
                question_id=question.id,
                text=answer_text,
                is_correct=is_correct,
                submitted_at=datetime.utcnow().isoformat()
            )
            db.add(new_answer)
            db.commit()
            
        # If correct, update team points
        if is_correct:
            # Update points in team_room_participation
            participation.points += question.points
            
            # Also update total_points in team
            team.total_points += question.points
            
            db.commit()
            
            await websocket.send_json({
                "type": "answer_result",
                "correct": True,
                "points_earned": question.points,
                "total_points": participation.points
            })
            
            # Update leaderboard for all clients
            await broadcast_leaderboard(db, room_id)
        else:
            # For wrong answers, include the correct answer
            correct_answer = question.correct_answer
            if question.question_type == "MULTIPLE_CHOICE":
                # For multiple choice, get the full text of the correct option
                correct_option = db.query(QuestionOption).filter(
                    QuestionOption.question_id == question.id,
                    QuestionOption.option_letter == question.correct_answer
                ).first()
                
                correct_answer_text = f"{correct_option.option_letter}: {correct_option.option_text}" if correct_option else question.correct_answer
            else:
                correct_answer_text = question.correct_answer
                
            await websocket.send_json({
                "type": "answer_result",
                "correct": False,
                "correct_answer": correct_answer_text
            })

async def send_leaderboard(db: Session, room_id: str, websocket: WebSocket):
    """Send leaderboard data to a specific client"""
    # Get team rankings for this room
    team_rankings = db.query(
        Team.id,
        Team.name,
        Team.profile_picture,
        Team.slogan,
        TeamRoomParticipation.points
    ).join(
        TeamRoomParticipation, 
        Team.id == TeamRoomParticipation.team_id
    ).filter(
        TeamRoomParticipation.room_id == room_id
    ).order_by(
        desc(TeamRoomParticipation.points)
    ).all()
    
    # Format leaderboard data
    leaderboard = []
    for rank, (team_id, team_name, profile_pic, slogan, points) in enumerate(team_rankings, 1):
        leaderboard.append({
            "rank": rank,
            "team_id": team_id,
            "team_name": team_name,
            "profile_picture": profile_pic,
            "slogan": slogan,
            "points": points
        })
    
    await websocket.send_json({
        "type": "leaderboard",
        "leaderboard": leaderboard
    })

async def broadcast_leaderboard(db: Session, room_id: str):
    """Broadcast updated leaderboard to all clients in a room"""
    # Get team rankings for this room
    team_rankings = db.query(
        Team.id,
        Team.name,
        Team.profile_picture,
        Team.slogan,
        TeamRoomParticipation.points
    ).join(
        TeamRoomParticipation, 
        Team.id == TeamRoomParticipation.team_id
    ).filter(
        TeamRoomParticipation.room_id == room_id
    ).order_by(
        desc(TeamRoomParticipation.points)
    ).all()
    
    # Format leaderboard data
    leaderboard = []
    for rank, (team_id, team_name, profile_pic, slogan, points) in enumerate(team_rankings, 1):
        leaderboard.append({
            "rank": rank,
            "team_id": team_id,
            "team_name": team_name,
            "profile_picture": profile_pic,
            "slogan": slogan,
            "points": points
        })
    
    # Broadcast to all connected clients in the room
    await manager.broadcast_json(
        {
            "type": "leaderboard_update",
            "leaderboard": leaderboard
        },
        room_id
    )