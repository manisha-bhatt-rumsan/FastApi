#quiz/schemas.py
from pydantic import BaseModel, field_validator
from typing import Optional, List, TypedDict
from enum import Enum

class QuestionType(str, Enum):
    MCQ = "mcq"
    FAQ = "faq"
    BOOLEAN = "boolean"

class Question(BaseModel):
    question: str
    type: QuestionType
    choices: List[str]
    correct_answer: str
    explanation: str
    
    @field_validator('choices')
    @classmethod
    def validate_choices(cls, v, info):
        # Access other field values using info.data
        question_type = info.data.get('type')
        
        if question_type == QuestionType.MCQ and len(v) != 4:
            raise ValueError('MCQ must have exactly 4 choices')
        if question_type in [QuestionType.FAQ, QuestionType.BOOLEAN] and v:
            raise ValueError(f'{question_type.value} must have empty choices')
        return v
    
    
class UploadResponse(BaseModel):
    message: str
    original_filename: str
    uploaded_file_path: str
    text_file_path: str
    error_message: Optional[str]
    
    
class QuizSessionResponse(BaseModel):
    original_file_name: str
    questions: List[Question]    
    
 
    
class AnswerRequest(BaseModel):
    # session_id: str
    question: str
    answer: str
    

class AnswerResponse(BaseModel):
    correct: bool
    correct_answer: str
    explanation: str
    
    
class QuestionTypeRequest(BaseModel):
    question_type: str

    @field_validator('question_type')
    @classmethod
    def validate_question_type(cls, v):
        valid_types = ['mcq', 'faq', 'boolean']
        if v not in valid_types:
            raise ValueError(f'Question type must be one of {valid_types}')
        return v
    
class QuizGenerationState(TypedDict):
    # session_id: str
    original_file_name: str
    file_content: bytes
    document_text: str
    text_file_path: str
    uploaded_file_path: str
    questions: List[Question]
    error_message: Optional[str]
    filename: str
    chunks: List[str]


class QuizSummary(BaseModel):
    """Basic quiz information for listing"""
    id: int
    title: str
    owner_id: Optional[int] = None

class QuestionDetail(BaseModel):
    """Detailed question information from database"""
    id: int
    question: str
    type: str
    choices: List[str]
    correct_answer: str
    explanation: str

class QuizDetail(BaseModel):
    """Detailed quiz information including questions"""
    id: int
    title: str
    owner_id: Optional[int] = None
    questions: List[QuestionDetail]

class QuizListResponse(BaseModel):
    """Response for listing quizzes"""
    message: str
    quizzes: List[QuizSummary]
    count: int

class QuizDetailResponse(BaseModel):
    """Response for getting quiz details"""
    message: str
    quiz: QuizDetail

class DatabaseHealthResponse(BaseModel):
    """Response for database health check"""
    status: str
    message: str
    quiz_count: Optional[int] = None

class DeleteQuizResponse(BaseModel):
    """Response for quiz deletion"""
    message: str