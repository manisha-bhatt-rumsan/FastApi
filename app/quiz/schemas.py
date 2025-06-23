from pydantic import BaseModel, validator
from typing import Optional, List, TypedDict
from enum import Enum

class QuestionType(str, Enum):
    MCQ = "mcq"
    FAQ = "faq"
    BOOLEAN = "boolean"

class Question(BaseModel):
    question:str
    type:QuestionType
    choices: List[str]
    correct_answer:str
    explanation:str
    
    @validator('choices', pre=True, check_fields=False)
    def validate_choices(cls, v, values):
        question_type = values.get('type')
        if question_type == 'mcq' and len(v) != 4:
            raise ValueError('mcq must have exactly 4 choices')
        if question_type in ['faq', 'boolean'] and v:
            raise ValueError(f'{question_type} must have empty choices')
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
    # session_id:str
    question:str
    answer:str
    

class AnswerResponse(BaseModel):
    correct:bool
    correct_answer:str
    explanation:str
    
    
class QuestionTypeRequest(BaseModel):
    question_type: str

    @validator('question_type')
    def validate_question_type(cls, v):
        valid_types = ['mcq', 'faq', 'boolean']
        if v not in valid_types:
            raise ValueError(f'Question type must be one of {valid_types}')
        return v
    
class QuizGenerationState(TypedDict):
    # session_id:str
    original_file_name:str
    file_content:bytes
    document_text:str
    text_file_path:str
    uploaded_file_path:str
    questions:List[Question]
    error_message:Optional[str]
    filename:str
    chunks:List[str]
    
