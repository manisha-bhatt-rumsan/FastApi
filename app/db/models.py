# db/models.py
from sqlalchemy import Column, Integer, String, ForeignKey, Text, Enum, ARRAY
from sqlalchemy.orm import relationship
import enum
from app.db.database import Base

class QuestionTypeEnum(enum.Enum):
    MCQ = "mcq"
    FAQ = "faq"
    BOOLEAN = "boolean"
    
class DifficultyLevelEnum(enum.Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"    

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    quizzes = relationship("Quiz", back_populates="owner")
    documents = relationship("Document", back_populates="owner")

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String, unique=True, index=True) 
    title = Column(String, index=True)
    content = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="documents")

class Quiz(Base):
    __tablename__ = "quizzes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="quizzes")
    questions = relationship("Question", back_populates="quiz")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    type = Column(Enum(QuestionTypeEnum, name="question_type"), nullable=False)
    difficulty = Column(Enum(DifficultyLevelEnum, name="difficulty_level"), nullable=False)  
    choices = Column(ARRAY(String), nullable=True)
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    quiz = relationship("Quiz", back_populates="questions")