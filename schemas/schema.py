from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from enum import Enum

# Enum for question types
class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    TEXT = "TEXT"

# Request models
class LoginRequest(BaseModel):
    room_id: str
    team_name: str
    password: str

class TeamProfileUpdate(BaseModel):
    profile_picture: Optional[str] = None
    slogan: Optional[str] = None

class QuestionOptionSchema(BaseModel):
    option_letter: str
    option_text: str
    
    class Config:
        orm_mode = True

class QuestionCreate(BaseModel):
    text: str
    question_type: QuestionType
    correct_answer: str
    points: int = 1
    time_limit: Optional[int] = None
    options: Optional[List[QuestionOptionSchema]] = None  # For multiple choice questions

class AnswerSubmit(BaseModel):
    question_id: int
    answer: str  # Either text answer or option letter (A, B, C, D)

# Response models
class TeamBase(BaseModel):
    id: int
    name: str
    profile_picture: Optional[str] = None
    slogan: Optional[str] = None
    
    class Config:
        orm_mode = True

class TeamDetail(TeamBase):
    total_points: int
    
    class Config:
        orm_mode = True

class TeamRoomStats(BaseModel):
    room_id: str
    room_name: str
    points: int
    
    class Config:
        orm_mode = True

class TeamWithRoomStats(TeamDetail):
    room_stats: List[TeamRoomStats]
    
    class Config:
        orm_mode = True

class RoomDetail(BaseModel):
    id: str
    name: str
    is_active: bool
    
    class Config:
        orm_mode = True

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    team: TeamDetail
    room: RoomDetail
    
    class Config:
        orm_mode = True

class QuestionResponse(BaseModel):
    id: int
    text: str
    question_type: QuestionType
    points: int
    time_limit: Optional[int] = None
    options: Optional[List[QuestionOptionSchema]] = None  # For multiple choice questions
    
    class Config:
        orm_mode = True

class AnswerResult(BaseModel):
    correct: bool
    points_earned: Optional[int] = None
    correct_answer: Optional[str] = None  # Only provided when the answer is wrong
    total_points: Optional[int] = None
    
    class Config:
        orm_mode = True

class LeaderboardEntry(BaseModel):
    team_id: int
    team_name: str
    profile_picture: Optional[str] = None
    slogan: Optional[str] = None
    points: int
    rank: int
    
    class Config:
        orm_mode = True

class RoomLeaderboard(BaseModel):
    room_id: str
    room_name: str
    teams: List[LeaderboardEntry]
    
    class Config:
        orm_mode = True

# WebSocket message models
class ChatMessage(BaseModel):
    type: str = "chat"
    message: str

class AnswerMessage(BaseModel):
    type: str = "answer"
    question_id: int
    answer: str

class SystemMessage(BaseModel):
    type: str = "system_message"
    message: str

class QuestionMessage(BaseModel):
    type: str = "question"
    id: int
    text: str
    question_type: QuestionType
    points: int
    time_limit: Optional[int] = None
    options: Optional[List[Dict[str, str]]] = None  # For multiple choice questions

class AnswerResultMessage(BaseModel):
    type: str = "answer_result"
    correct: bool
    points_earned: Optional[int] = None
    correct_answer: Optional[str] = None  # Only provided when incorrect
    total_points: Optional[int] = None

class LeaderboardUpdateMessage(BaseModel):
    type: str = "leaderboard_update"
    leaderboard: List[Dict[str, Any]]