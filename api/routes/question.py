from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session
from db.database import get_db
from schemas.question_schema import Question, QuestionCreate, QuestionOption, OptionResponse, OptionBulkRequest
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

@router.post("/options/bulk/{question_id}", response_model=List[OptionResponse])
async def bulk_create_or_update_options(question_id: int, request: OptionBulkRequest, db: Session = Depends(get_db)):
    """
    Create or update multiple options for a question at once.
    """
    from db.models import Question as QuestionModel, QuestionOption
    
    # Check if the question exists and is multiple choice
    question = db.query(QuestionModel).filter(QuestionModel.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    if question.question_type != "MULTIPLE_CHOICE":
        raise HTTPException(status_code=400, detail="Options can only be added to multiple choice questions")
    
    # Delete existing options
    db.query(QuestionOption).filter(QuestionOption.question_id == question_id).delete()
    
    # Create new options
    db_options = []
    for option_data in request.options:
        db_option = QuestionOption(
            question_id=question_id,
            option_letter=option_data.option_letter,
            option_text=option_data.option_text
        )
        db.add(db_option)
        db_options.append(db_option)
    
    db.commit()
    
    # Refresh all options to get their IDs
    for db_option in db_options:
        db.refresh(db_option)
    
    return db_options