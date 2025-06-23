from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: str

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    class Config:
        orm_mode = True

class DocumentCreate(BaseModel):
    id = Column(Integer, primary_key=True, index=True)
    title: str
    file_path = Column(String, nullable=False) 
    owner_id: int

class DocumentOut(BaseModel):
    id: int
    title: str
    content: str
    owner_id: int
    class Config:
        orm_mode = True

class QuizCreate(BaseModel):
    title: str
    owner_id: int

class QuizOut(BaseModel):
    id: int
    title: str
    owner_id: int
    class Config:
        orm_mode = True

class QuestionCreate(BaseModel):
    text: str
    quiz_id: int

class QuestionOut(BaseModel):
    id: int
    text: str
    quiz_id: int
    class Config:
        orm_mode = True