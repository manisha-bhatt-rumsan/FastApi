from pydantic import BaseModel
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
    