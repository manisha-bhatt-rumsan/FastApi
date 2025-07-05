# app/db/models.py
from sqlalchemy import Column, Integer, String, ForeignKey, Text, ARRAY, DateTime, Boolean
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from app.db.database import Base

class QuestionTypeEnum(enum.Enum):
    MCQ = "mcq"
    FAQ = "faq"
    BOOLEAN = "boolean"

class DifficultyLevelEnum(enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    quizzes = relationship("Quiz", back_populates="owner")
    documents = relationship("Document", back_populates="owner")
    answers = relationship("Answer", back_populates="owner")

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
    answers = relationship("Answer", back_populates="quiz")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    type = Column(String(7), nullable=False)
    difficulty = Column(String(6), nullable=False)
    choices = Column(ARRAY(String), nullable=True)
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    quiz = relationship("Quiz", back_populates="questions")
    answers = relationship("Answer", back_populates="question")

class Answer(Base):
    __tablename__ = "answers"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    submitted_answer = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    owner = relationship("User", back_populates="answers")
    quiz = relationship("Quiz", back_populates="answers")
    question = relationship("Question", back_populates="answers")