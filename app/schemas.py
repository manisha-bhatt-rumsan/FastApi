from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: str

class User(BaseModel):
    id: int
    name: str
    email: str
    class Config:
        orm_mode = True

class DocumentCreate(BaseModel):
    title: str
    content: str
    owner_id: int

class Document(BaseModel):
    id: int
    title: str
    content: str
    owner_id: int
    class Config:
        orm_mode = True

class QuizCreate(BaseModel):
    title: str
    owner_id: int

class Quiz(BaseModel):
    id: int
    title: str
    owner_id: int
    class Config:
        orm_mode = True

class QuestionCreate(BaseModel):
    text: str
    quiz_id: int

class Question(BaseModel):
    id: int
    text: str
    quiz_id: int
    class Config:
        orm_mode = True