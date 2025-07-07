# app/quiz/schemas.py
from pydantic import BaseModel, field_validator, ValidationInfo, Field
from typing import Optional, List, TypedDict
from enum import Enum

class QuestionType(str, Enum):
    MCQ = "mcq"
    FAQ = "faq"
    BOOLEAN = "boolean"
    
class DifficultyLevel(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"

class QuestionCount(int, Enum):
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5    

class Question(BaseModel):
    question: str
    type: QuestionType
    choices: List[str] = []
    correct_answer: str
    explanation: str
    difficulty: str
    
    @field_validator('difficulty', mode='before')
    @classmethod
    def set_default_difficulty(cls, v, info: ValidationInfo):
        if v is None:
            return info.context.get('default_difficulty') 
        return v
    
    @field_validator('choices')
    @classmethod
    def validate_choices(cls, v: List[str], info: ValidationInfo):
        question_type = info.data.get('type')
        if not isinstance(question_type, QuestionType):
            raise ValueError(f"Invalid question type: {question_type}. Must be a QuestionType enum.")
        
        if question_type == QuestionType.MCQ:
            if len(v) != 4:
                raise ValueError('MCQ must have exactly 4 choices')
            if not all(isinstance(choice, str) and choice.strip() for choice in v):
                raise ValueError('MCQ choices must be non-empty strings')
        elif question_type in [QuestionType.FAQ, QuestionType.BOOLEAN]:
            if v:
                raise ValueError(f'{question_type.value} must have empty choices')
        return v

class UploadResponse(BaseModel):
    message: str
    original_filename: str
    uploaded_file_path: Optional[str] = None
    text_file_path: Optional[str] = None
    error_message: Optional[str] = None
    document_id: Optional[str] = None

class QuizSessionResponse(BaseModel):
    quiz_id: int  
    original_filename: str
    questions: List[Question]

class SubmittedAnswer(BaseModel):
    question_id: int = Field(..., gt=0)  
    submitted_answer: str = Field(..., max_length=600) 

class AnswerRequest(BaseModel):
    quiz_id: int = Field(..., gt=0)  
    answers: List[SubmittedAnswer] = Field(..., min_items=1) 

class AnswerResult(BaseModel):
    question_id: int
    is_correct: bool
    submitted_answer: str
    correct_answer: str
    explanation: Optional[str] = None 

class AnswerResponse(BaseModel):
    results: List[AnswerResult]
    quiz_completed: bool = False
    score_so_far: int
    remaining: int
    message: str = "Answers processed successfully"

class QuestionTypeRequest(BaseModel):
    question_type: str

    @field_validator('question_type')
    @classmethod
    def validate_question_type(cls, v):
        valid_types = ['mcq', 'faq', 'boolean']
        if v not in valid_types:
            raise ValueError(f'Question type must be one of {valid_types}')
        return v

class QuizSummary(BaseModel):
    id: int
    title: str
    owner_id: Optional[int] = None

class QuestionDetail(BaseModel):
    id: int
    question: str
    type: str
    choices: List[str]
    correct_answer: str
    explanation: str

class QuizDetail(BaseModel):
    id: int
    title: str
    owner_id: Optional[int] = None
    questions: List[QuestionDetail]

class QuizListResponse(BaseModel):
    message: str
    quizzes: List[QuizSummary]
    count: int

class QuizDetailResponse(BaseModel):
    message: str
    quiz: QuizDetail

class DatabaseHealthResponse(BaseModel):
    status: str
    message: str
    quiz_count: Optional[int] = None

class DeleteQuizResponse(BaseModel):
    message: str

class QuizGenerationState(TypedDict):
    original_file_name: str
    file_content: bytes
    document_text: str
    text_file_path: str
    uploaded_file_path: str
    questions: List[Question]
    error_message: Optional[str]
    filename: str
    chunks: List[str]