from pydantic import BaseModel
from typing import List, Optional

class QuestionOptionBase(BaseModel):
    option_letter: str
    option_text: str

class QuestionOptionCreate(QuestionOptionBase):
    pass

class QuestionOption(QuestionOptionBase):
    id: int
    question_id: int

    class Config:
        orm_mode = True

class OptionResponse(QuestionOption):
    pass

class OptionBulkRequest(BaseModel):
    options: List[QuestionOptionCreate]

class QuestionBase(BaseModel):
    room_id: str
    text: str
    question_type: str  # 'MULTIPLE_CHOICE' or 'TEXT'
    correct_answer: str
    points: int = 1
    time_limit: Optional[int] = None
    is_active: bool = False

class QuestionCreate(QuestionBase):
    options: Optional[List[QuestionOptionCreate]] = None

class Question(QuestionBase):
    id: int
    options: Optional[List[QuestionOption]] = None

    class Config:
        orm_mode = True