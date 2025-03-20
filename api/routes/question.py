from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session
from db.database import get_db
from schemas.question_schema import Question, QuestionCreate
from services.question_service import QuestionService

router = APIRouter(
    prefix="/questions",
    tags=["questions"],
    responses={404: {"description": "Not found"}}
)

@router.get("/", response_model=List[Question])
async def read_questions(
    room_id: Optional[str] = None, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    Get all questions, optionally filtered by room_id.
    """
    questions = await QuestionService.get_questions(db, room_id=room_id, skip=skip, limit=limit)
    return questions

@router.get("/{question_id}", response_model=Question)
async def read_question(question_id: int, db: Session = Depends(get_db)):
    """
    Get a specific question by ID.
    """
    question = await QuestionService.get_question(db, question_id=question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@router.post("/", response_model=Question, status_code=status.HTTP_201_CREATED)
async def create_question(question: QuestionCreate, db: Session = Depends(get_db)):
    """
    Create a new quiz question.
    """
    try:
        return await QuestionService.create_question(db=db, question=question)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{question_id}", response_model=Question)
async def update_question(question_id: int, question_data: dict, db: Session = Depends(get_db)):
    """
    Update an existing question.
    """
    updated_question = await QuestionService.update_question(db, question_id=question_id, question_data=question_data)
    if updated_question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return updated_question

@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(question_id: int, db: Session = Depends(get_db)):
    """
    Delete a question.
    """
    success = await QuestionService.delete_question(db, question_id=question_id)
    if not success:
        raise HTTPException(status_code=404, detail="Question not found")
    return None

@router.patch("/{question_id}/activate", response_model=Question)
async def activate_question(question_id: int, db: Session = Depends(get_db)):
    """
    Activate a question (make it the current active question).
    Only one question can be active at a time per room.
    """
    updated_question = await QuestionService.set_question_active(db, question_id=question_id, is_active=True)
    if updated_question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return updated_question

@router.patch("/{question_id}/deactivate", response_model=Question)
async def deactivate_question(question_id: int, db: Session = Depends(get_db)):
    """
    Deactivate a question.
    """
    updated_question = await QuestionService.set_question_active(db, question_id=question_id, is_active=False)
    if updated_question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return updated_question