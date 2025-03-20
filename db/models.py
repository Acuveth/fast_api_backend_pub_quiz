from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text, Enum, Date, Float, desc
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from db.database import Base

class Room(Base):
    __tablename__ = "rooms"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(String)
    
    teams = relationship("TeamRoomParticipation", back_populates="room")
    questions = relationship("Question", back_populates="room")
    settings = relationship("RoomSettings", back_populates="room", uselist=False)

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, unique=True)
    password = Column(String)  # Hashed password
    profile_picture = Column(String, nullable=True)
    slogan = Column(Text, nullable=True)
    total_points = Column(Integer, default=0)
    created_at = Column(String)
    
    room_participations = relationship("TeamRoomParticipation", back_populates="team")
    answers = relationship("Answer", back_populates="team")
    history = relationship("TeamHistory", back_populates="team")

class TeamRoomParticipation(Base):
    __tablename__ = "team_room_participation"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    room_id = Column(String, ForeignKey("rooms.id"))
    points = Column(Integer, default=0)
    joined_at = Column(String)
    
    team = relationship("Team", back_populates="room_participations")
    room = relationship("Room", back_populates="teams")

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String, ForeignKey("rooms.id"))
    text = Column(Text)
    question_type = Column(Enum("MULTIPLE_CHOICE", "TEXT", name="question_type"))
    correct_answer = Column(String)
    points = Column(Integer, default=1)
    time_limit = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=False)
    created_at = Column(String)
    
    room = relationship("Room", back_populates="questions")
    options = relationship("QuestionOption", back_populates="question")
    answers = relationship("Answer", back_populates="question")

class QuestionOption(Base):
    __tablename__ = "question_options"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    option_letter = Column(String(1))
    option_text = Column(String)
    
    question = relationship("Question", back_populates="options")

class Answer(Base):
    __tablename__ = "answers"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    text = Column(String)
    is_correct = Column(Boolean, default=False)
    submitted_at = Column(String)
    
    team = relationship("Team", back_populates="answers")
    question = relationship("Question", back_populates="answers")

class TeamHistory(Base):
    __tablename__ = "team_history"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    room_id = Column(String, ForeignKey("rooms.id"))
    points_earned = Column(Integer, default=0)
    rank = Column(Integer, nullable=True)
    participated_on = Column(Date)
    
    team = relationship("Team", back_populates="history")

class RoomSettings(Base):
    __tablename__ = "room_settings"
    
    room_id = Column(String, ForeignKey("rooms.id"), primary_key=True)
    default_time_per_question = Column(Integer, nullable=True)
    show_leaderboard = Column(Boolean, default=True)
    allow_chat = Column(Boolean, default=True)
    show_team_profiles = Column(Boolean, default=True)
    
    room = relationship("Room", back_populates="settings")

class RoomAdmin(Base):
    __tablename__ = "room_admins"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String, ForeignKey("rooms.id"))
    username = Column(String)
    password = Column(String)  # Hashed password
    created_at = Column(String)