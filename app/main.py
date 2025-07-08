from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import RedirectResponse
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select
# from .config import settings
# from .database import engine, Base, get_db
# from .models import User, Document, Quiz, Question
# from .schemas import (
#     UserCreate, UserOut,
#     DocumentCreate, DocumentOut,
#     QuizCreate, QuizOut,
#     QuestionCreate, QuestionOut
# )
# from .models import User, Document, Quiz, Question  
# from fastapi import File, UploadFile
# import shutil
# import os
# from uuid import uuid4
# from .models import Document
# from .schemas import DocumentOut
# from sqlalchemy.ext.asyncio import AsyncSession
# from fasta.responses import FileResponse
# from pydantic import BaseModel

# from upload.routes import upload_routes
from app.quiz.routes import quiz_routes
import uvicorn

app = FastAPI(
    # title=settings.app_name,
    # description=settings.app_description,
    # version=settings.app_version,
    # docs_url="/docs",
    # redoc_url="/redoc",
    # openapi_url="/openapi.json"
)

# app.include_router(upload_routes)
app.include_router(quiz_routes)



# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.allowed_origins,
#     allow_credentials=True,
#     allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
#     allow_headers=["*"],
# )

# UPLOAD_DIR = "uploaded_files"
# os.makedirs(UPLOAD_DIR, exist_ok=True)


# @app.on_event("startup")
# async def startup_event():
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)

# class HealthResponse(BaseModel):
#     status: str
#     message: str
#     version: str

# @app.get("/", include_in_schema=False)
# async def root():
#     return RedirectResponse(url="/docs")

# @app.get("/info", tags=["Information"])
# async def get_app_info():
#     return {
#         "name": settings.app_name,
#         "version": settings.app_version,
#         "description": settings.app_description,
#         "documentation": "/docs",
#         "alternative_docs": "/redoc",
#         "health_check": f"{settings.api_v1_prefix}/health"
#     }

# @app.get("/health", tags=["Health Check"], response_model=HealthResponse)
# async def health_check():
#     return HealthResponse(
#         status="healthy",
#         message="API is running perfectly!",
#         version=settings.app_version
#     )

# # CRUD for User
# @app.post(f"{settings.api_v1_prefix}/users/", response_model=UserOut, tags=["Users"])
# async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
#     result = await db.execute(select(User).filter(User.email == user.email))
#     if result.scalars().first():
#         raise HTTPException(status_code=400, detail="Email already registered")
#     db_user = User(name=user.name, email=user.email)
#     db.add(db_user)
#     await db.commit()
#     await db.refresh(db_user)
#     return db_user

# @app.get(f"{settings.api_v1_prefix}/users/{{user_id}}", response_model=UserOut, tags=["Users"])
# async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
#     result = await db.execute(select(User).filter(User.id == user_id))
#     db_user = result.scalars().first()
#     if db_user is None:
#         raise HTTPException(status_code=404, detail="User not found")
#     return db_user

# # CRUD for Document
# ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

# @app.post(f"{settings.api_v1_prefix}/upload/", response_model=DocumentOut, tags=["Documents"])
# async def upload_file(
#     owner_id: int,
#     file: UploadFile = File(...),
#     db: AsyncSession = Depends(get_db)
# ):
#     ext = os.path.splitext(file.filename)[1].lower()
#     if ext not in ALLOWED_EXTENSIONS:
#         raise HTTPException(status_code=400, detail="Unsupported file type")

#     unique_filename = f"{uuid4().hex}_{file.filename}"
#     file_path = os.path.join(UPLOAD_DIR, unique_filename)

#     with open(file_path, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)

#     new_doc = Document(
#         title=file.filename,
#         content=file_path,  # storing path instead of content
#         owner_id=owner_id
#     )
#     db.add(new_doc)
#     await db.commit()
#     await db.refresh(new_doc)

#     return new_doc

# @app.get(f"{settings.api_v1_prefix}/download/{{document_id}}", tags=["Documents"])
# async def download_file(document_id: int, db: AsyncSession = Depends(get_db)):
#     result = await db.execute(select(Document).filter(Document.id == document_id))
#     document = result.scalars().first()

#     if not document or not os.path.exists(document.content):
#         raise HTTPException(status_code=404, detail="File not found")

#     return FileResponse(path=document.content, filename=document.title)

# @app.post(f"{settings.api_v1_prefix}/documents/", response_model=DocumentOut, tags=["Documents"])
# async def create_document(document: DocumentCreate, db: AsyncSession = Depends(get_db)):
#     db_document = Document(title=document.title, content=document.content, owner_id=document.owner_id)
#     db.add(db_document)
#     await db.commit()
#     await db.refresh(db_document)
#     return db_document

# @app.get(f"{settings.api_v1_prefix}/documents/{{document_id}}", response_model=DocumentOut, tags=["Documents"])
# async def get_document(document_id: int, db: AsyncSession = Depends(get_db)):
#     result = await db.execute(select(Document).filter(Document.id == document_id))
#     db_document = result.scalars().first()
#     if db_document is None:
#         raise HTTPException(status_code=404, detail="Document not found")
#     return db_document

# # CRUD for Quiz
# @app.post(f"{settings.api_v1_prefix}/quizzes/", response_model=QuizOut, tags=["Quizzes"])
# async def create_quiz(quiz: QuizCreate, db: AsyncSession = Depends(get_db)):
#     db_quiz = Quiz(title=quiz.title, owner_id=quiz.owner_id)
#     db.add(db_quiz)
#     await db.commit()
#     await db.refresh(db_quiz)
#     return db_quiz

# @app.get(f"{settings.api_v1_prefix}/quizzes/{{quiz_id}}", response_model=QuizOut, tags=["Quizzes"])
# async def get_quiz(quiz_id: int, db: AsyncSession = Depends(get_db)):
#     result = await db.execute(select(Quiz).filter(Quiz.id == quiz_id))
#     db_quiz = result.scalars().first()
#     if db_quiz is None:
#         raise HTTPException(status_code=404, detail="Quiz not found")
#     return db_quiz

# # CRUD for Question
# @app.post(f"{settings.api_v1_prefix}/questions/", response_model=QuestionOut, tags=["Questions"])
# async def create_question(question: QuestionCreate, db: AsyncSession = Depends(get_db)):
#     db_question = Question(text=question.text, quiz_id=question.quiz_id)
#     db.add(db_question)
#     await db.commit()
#     await db.refresh(db_question)
#     return db_question

# @app.get(f"{settings.api_v1_prefix}/questions/{{question_id}}", response_model=QuestionOut, tags=["Questions"])
# async def get_question(question_id: int, db: AsyncSession = Depends(get_db)):
#     result = await db.execute(select(Question).filter(Question.id == question_id))
#     db_question = result.scalars().first()
#     if db_question is None:
#         raise HTTPException(status_code=404, detail="Question not found")
#     return db_question

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)