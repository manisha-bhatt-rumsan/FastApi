from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from models import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True)

class Document(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)

class Quiz(Base):
    __tablename__ = 'quizzes'
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'))

class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey('quizzes.id'))
    text = Column(String, nullable=False)
