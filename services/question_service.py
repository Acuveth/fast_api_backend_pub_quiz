from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from db.models import Question, QuestionOption
from schemas.question_schema import QuestionCreate, QuestionOption as QuestionOptionSchema
from datetime import datetime

class QuestionService:
    @staticmethod
    async def get_questions(db: Session, room_id: Optional[str] = None, skip: int = 0, limit: int = 100):
        query = db.query(Question)
        if room_id:
            query = query.filter(Question.room_id == room_id)
        return query.order_by(Question.id).offset(skip).limit(limit).all()

    @staticmethod
    async def get_question(db: Session, question_id: int):
        return db.query(Question).filter(Question.id == question_id).first()

    @staticmethod
    async def create_question(db: Session, question: QuestionCreate):
        current_time = datetime.utcnow().isoformat()
        db_question = Question(
            room_id=question.room_id,
            text=question.text,
            question_type=question.question_type,
            correct_answer=question.correct_answer,
            points=question.points,
            time_limit=question.time_limit,
            is_active=question.is_active,
            created_at=current_time
        )
        db.add(db_question)
        db.flush()

        if question.options and question.question_type == "MULTIPLE_CHOICE":
            for option in question.options:
                db_option = QuestionOption(
                    question_id=db_question.id,
                    option_letter=option.option_letter,
                    option_text=option.option_text
                )
                db.add(db_option)

        try:
            db.commit()
            db.refresh(db_question)
            return db_question
        except SQLAlchemyError as e:
            db.rollback()
            raise e

    @staticmethod
    async def update_question(db: Session, question_id: int, question_data: dict):
        db_question = db.query(Question).filter(Question.id == question_id).first()
        if not db_question:
            return None

        for key, value in question_data.items():
            if key != "options" and hasattr(db_question, key):
                setattr(db_question, key, value)

        if "options" in question_data and db_question.question_type == "MULTIPLE_CHOICE":
            # Delete existing options
            db.query(QuestionOption).filter(QuestionOption.question_id == question_id).delete()
            
            # Add new options
            for option in question_data["options"]:
                db_option = QuestionOption(
                    question_id=db_question.id,
                    option_letter=option["option_letter"],
                    option_text=option["option_text"]
                )
                db.add(db_option)

        try:
            db.commit()
            db.refresh(db_question)
            return db_question
        except SQLAlchemyError as e:
            db.rollback()
            raise e

    @staticmethod
    async def delete_question(db: Session, question_id: int):
        db_question = db.query(Question).filter(Question.id == question_id).first()
        if not db_question:
            return False
        
        db.delete(db_question)
        try:
            db.commit()
            return True
        except SQLAlchemyError:
            db.rollback()
            return False

    @staticmethod
    async def set_question_active(db: Session, question_id: int, is_active: bool):
        """Sets a question as active or inactive. Only one question can be active at a time per room."""
        db_question = db.query(Question).filter(Question.id == question_id).first()
        if not db_question:
            return None
        
        # If activating, deactivate all other questions in the same room
        if is_active:
            db.query(Question).filter(
                Question.room_id == db_question.room_id,
                Question.id != question_id
            ).update({"is_active": False})
        
        db_question.is_active = is_active
        
        try:
            db.commit()
            db.refresh(db_question)
            return db_question
        except SQLAlchemyError as e:
            db.rollback()
            raise e