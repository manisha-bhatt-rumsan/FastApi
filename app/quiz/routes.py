from fastapi import File, HTTPException, APIRouter, UploadFile, Query
from fastapi import Depends, Body
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.models import Question as DBQuestion, Quiz as DBQuiz, Answer, QuestionTypeEnum, Document
import logging
from sqlalchemy.orm import selectinload
from datetime import datetime
from app.upload.service import extract_chunks_with_metadata, store_chunks_in_qdrant
from app.quiz.service import generate_questions, save_quiz_to_db
from app.quiz.schemas import (QuizSessionResponse, QuestionType, UploadResponse, QuestionCount, DifficultyLevel, AnswerRequest, AnswerResponse, AnswerResult, QuizDetailResponse, QuizDetail, QuestionDetail)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("quiz_generator.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

quiz_routes = APIRouter()

@quiz_routes.post("/upload_document", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    filename = file.filename or "unknown_file"
    logger.info("Uploading %s", filename)

    # Check if the document was already uploaded
    existing_doc = await db.execute(select(Document).where(Document.title == filename))
    if existing_doc.scalars().first():
        raise HTTPException(status_code=409, detail="This document has already been uploaded.")

    try:
        # Extract metadata and save file
        chunks, metadata, doc_id, uploaded_file_path = await extract_chunks_with_metadata(file)
        store_chunks_in_qdrant(chunks, metadata)

        # Save document metadata to DB
        new_doc = Document(
            document_id=doc_id,
            title=filename,
            uploaded_file_path=uploaded_file_path 
        )
        db.add(new_doc)
        await db.commit()

        return UploadResponse(
            message="Upload successful; chunks stored.",
            original_filename=filename,
            document_id=doc_id,
            uploaded_file_path=uploaded_file_path
        )

    except Exception as exc:
        logger.error("Upload failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))

@quiz_routes.post("/quizzes/generate", response_model=QuizSessionResponse)
async def generate_question(
    document_id: str = Query(..., description="ID returned by /upload_document"),
    question_type: QuestionType = Query(...),
    num_questions: QuestionCount = QuestionCount.THREE,
    difficulty_level: DifficultyLevel = DifficultyLevel.MEDIUM,
    db: AsyncSession = Depends(get_db)
):
    # Fetch document from DB
    result = await db.execute(select(Document).where(Document.document_id == document_id))
    document = result.scalars().first()

    if not document:
        raise HTTPException(status_code=404, detail="Document ID not found. Please upload the document first.")

    try:
        # Generate questions from Qdrant
        questions = generate_questions(
            doc_id=document_id,
            question_type=question_type.value,
            num=num_questions.value,
            difficulty=difficulty_level.value,
        )

        if not questions:
            raise HTTPException(status_code=400, detail="Could not generate questions.")

        # Save quiz + questions in DB
        db_result = await save_quiz_to_db(document.title, questions)
        quiz_id = db_result.get("quiz_id")

        return QuizSessionResponse(
            quiz_id=quiz_id,
            original_filename=document.title,
            questions=questions[: num_questions.value],
        )

    except Exception as exc:
        logger.error("Generation failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))
    
    
@quiz_routes.get("/quizzes/{quiz_id}", response_model=QuizDetailResponse)
async def get_quiz_by_id(
    quiz_id: int,
    db: AsyncSession = Depends(get_db),
):
    # Fetch quiz and eagerly load related questions
    result = await db.execute(
        select(DBQuiz)
        .options(selectinload(DBQuiz.questions))
        .where(DBQuiz.id == quiz_id)
    )
    quiz = result.scalars().first()

    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Serialize questions
    questions = [
        QuestionDetail(
            id=q.id,
            question=q.question,
            type=q.type,
            choices=q.choices or [],
            correct_answer=q.correct_answer,
            explanation=q.explanation or ""
        )
        for q in quiz.questions
    ]

    return QuizDetailResponse(
        message="Quiz retrieved successfully",
        quiz=QuizDetail(
            id=quiz.id,
            title=quiz.title,
            owner_id=quiz.owner_id,
            # created_at=getattr(quiz, "created_at", None)
            questions=questions
        )
    )


@quiz_routes.post("/quizzes/{quiz_id}/submit_answers", response_model=AnswerResponse)
async def submit_answers(
    quiz_id: int,
    req: AnswerRequest = Body(...),
    db: AsyncSession = Depends(get_db)
):
    quiz = await db.get(DBQuiz, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    rows = await db.execute(
        select(DBQuestion).where(DBQuestion.quiz_id == quiz_id)
    )
    questions = rows.scalars().all()

    if not questions:
        raise HTTPException(status_code=404, detail="No questions found for quiz.")

    question_map = {q.id: q for q in questions}
    question_ids = set(question_map.keys())

    # New: Prevent submission if quiz is already completed
    answered_count = await db.scalar(
        select(func.count(func.distinct(Answer.question_id)))
        .where(Answer.quiz_id == quiz_id)
    )
    if answered_count == len(question_ids):
        raise HTTPException(status_code=400, detail="Quiz has already been completed.")

    results = []
    db_answers = []

    for answer in req.answers:
        if answer.question_id not in question_ids:
            raise HTTPException(status_code=400, detail=f"Invalid question ID: {answer.question_id}")
        
        existing_answer = await db.scalar(
            select(Answer).where(
                Answer.quiz_id == quiz_id,
                Answer.question_id == answer.question_id
            )
        )
        if existing_answer:
            raise HTTPException(
                status_code=400,
                detail=f"Question {answer.question_id} has already been answered."
            )

        q = question_map[answer.question_id]
        submitted_answer = answer.submitted_answer.strip().lower()
        correct_answer = q.correct_answer.strip().lower()
        is_correct = False

        if q.type == QuestionTypeEnum.MCQ.value:
            if submitted_answer not in [choice.lower() for choice in q.choices]:
                raise HTTPException(status_code=400, detail=f"Answer for question {answer.question_id} not in choices.")
            is_correct = submitted_answer == correct_answer

        elif q.type == QuestionTypeEnum.FAQ.value:
            is_correct = submitted_answer == correct_answer

        elif q.type == QuestionTypeEnum.BOOLEAN.value:
            true_values = {"true", "yes", "1", "t"}
            false_values = {"false", "no", "0", "f"}
            if submitted_answer in true_values:
                normalized = "true"
            elif submitted_answer in false_values:
                normalized = "false"
            else:
                raise HTTPException(status_code=400, detail=f"Invalid boolean answer for question {answer.question_id}")
            is_correct = normalized == correct_answer

        else:
            raise HTTPException(status_code=400, detail=f"Unknown question type for question {answer.question_id}")

        db_answers.append(
            Answer(
                user_id=None,
                quiz_id=quiz_id,
                question_id=answer.question_id,
                submitted_answer=answer.submitted_answer,
                is_correct=is_correct,
                timestamp=datetime.utcnow(),
            )
        )

        results.append(
            AnswerResult(
                question_id=answer.question_id,
                is_correct=is_correct,
                submitted_answer=answer.submitted_answer,
                correct_answer=q.correct_answer,
                explanation=q.explanation or ""
            )
        )

    db.add_all(db_answers)
    await db.commit()

    total_correct = await db.scalar(
        select(func.count()).select_from(Answer).where(
            Answer.quiz_id == quiz_id,
            Answer.is_correct == True
        )
    )

    answered_questions = await db.scalar(
        select(func.count(func.distinct(Answer.question_id))).where(
            Answer.quiz_id == quiz_id
        )
    )

    remaining = len(question_ids) - answered_questions
    quiz_completed = remaining == 0

    return AnswerResponse(
        results=results,
        quiz_completed=quiz_completed,
        score_so_far=total_correct or 0,
        remaining=remaining,
        message="Answers processed successfully"
    )

