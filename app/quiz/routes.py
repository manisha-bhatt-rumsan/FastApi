from fastapi import File, HTTPException, APIRouter, UploadFile, Query
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.models import Question as DBQuestion, Quiz as DBQuiz, Answer, QuestionTypeEnum
import logging
from datetime import datetime
from app.upload.service import extract_chunks_with_metadata, store_chunks_in_qdrant
from app.quiz.service import generate_questions, save_quiz_to_db
from app.quiz.schemas import (
    QuizSessionResponse,
    QuestionType,
    UploadResponse,
    QuestionCount,
    DifficultyLevel,
    AnswerRequest,
    AnswerResponse,
    AnswerResult
)

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

doc_lookup: dict[str, str] = {}  # doc_id -> original filename

@quiz_routes.post("/upload_document", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    filename = file.filename or "unknown_file"
    logger.info("Uploading %s", filename)

    try:
        chunks, metadata, doc_id = await extract_chunks_with_metadata(file)
        store_chunks_in_qdrant(chunks, metadata)

        doc_id = metadata[0]["doc_id"]
        doc_lookup[doc_id] = filename

        return UploadResponse(
            message="Upload successful; chunks stored.",
            original_filename=filename,
            document_id=doc_id,
        )
    except Exception as exc:
        logger.error("Upload failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))

@quiz_routes.post("/generate_question", response_model=QuizSessionResponse)
async def generate_question(
    document_id: str = Query(..., description="ID returned by /upload_document"),
    question_type: QuestionType = Query(...),
    num_questions: QuestionCount = QuestionCount.THREE,
    difficulty_level: DifficultyLevel = DifficultyLevel.MEDIUM,
):
    if document_id not in doc_lookup:
        raise HTTPException(status_code=404, detail="Unknown document_id — upload first.")

    try:
        questions = generate_questions(
            doc_id=document_id,
            question_type=question_type.value,
            num=num_questions.value,
            difficulty=difficulty_level.value,
        )

        if not questions:
            raise HTTPException(status_code=400, detail="Could not generate questions.")

        # Save to DB (required for persistence)
        db_result = await save_quiz_to_db(doc_lookup[document_id], questions)
        quiz_id = db_result.get("quiz_id")  

        return QuizSessionResponse(
            quiz_id=quiz_id, 
            original_filename=doc_lookup[document_id],
            questions=questions[: num_questions.value],
        )

    except Exception as exc:
        logger.error("Generation failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))

@quiz_routes.post("/submit_answer/{quiz_id}", response_model=AnswerResponse)
async def submit_answer(
    quiz_id: int,
    req: AnswerRequest,
    db: AsyncSession = Depends(get_db),
    # user: User = Depends(get_current_user),  # Commented out
):
    logger.info("Received request body: %s", req.dict())
    # Verify quiz exists
    quiz = await db.get(DBQuiz, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz ID not found.")

    # Fetch all questions for the quiz
    rows = await db.execute(select(DBQuestion).where(DBQuestion.quiz_id == quiz_id))
    questions = rows.scalars().all()
    if not questions:
        raise HTTPException(status_code=404, detail="No questions found for quiz.")

    # Track results and score
    results = []
    score = 0
    question_ids = {q.id for q in questions}  # Valid question IDs

    for answer in req.answers:
        # Verify question_id
        if answer.question_id not in question_ids:
            raise HTTPException(status_code=400, detail=f"Invalid question ID: {answer.question_id}")

        # Fetch question
        q_row = await db.get(DBQuestion, answer.question_id)
        if q_row is None:
            raise HTTPException(status_code=404, detail=f"Question {answer.question_id} not found.")

        # Type-specific validation
        submitted_answer = answer.submitted_answer.strip().lower()
        correct_answer = q_row.correct_answer.strip().lower()
        is_correct = False

        if q_row.type == QuestionTypeEnum.MCQ:
            if submitted_answer not in [choice.lower() for choice in q_row.choices]:
                raise HTTPException(status_code=400, detail=f"Answer for question {answer.question_id} not in choices.")
            is_correct = submitted_answer == correct_answer
        elif q_row.type == QuestionTypeEnum.FAQ:
            is_correct = submitted_answer == correct_answer
        elif q_row.type == QuestionTypeEnum.BOOLEAN:
            true_values = {"true", "yes", "1", "t"}
            false_values = {"false", "no", "0", "f"}
            if submitted_answer in true_values:
                normalized_answer = "true"
            elif submitted_answer in false_values:
                normalized_answer = "false"
            else:
                raise HTTPException(status_code=400, detail=f"Invalid boolean answer for question {answer.question_id}.")
            is_correct = normalized_answer == correct_answer
        else:
            raise HTTPException(status_code=400, doc="Unknown question type for question {answer.question_id}.")

        if is_correct:
            score += 1

        # Store answer in database
        db_answer = Answer(
            user_id=None,  
            quiz_id=quiz_id,
            question_id=answer.question_id,
            submitted_answer=answer.submitted_answer,
            is_correct=is_correct,
            timestamp=datetime.utcnow()
        )
        db.add(db_answer)

        # Add to results
        results.append(AnswerResult(
            question_id=answer.question_id,
            is_correct=is_correct,
            submitted_answer=answer.submitted_answer,
            correct_answer=q_row.correct_answer,
            explanation=q_row.explanation or ""
        ))

    # Commit answers to database
    await db.commit()

    # Calculate remaining questions
    submitted_ids = {ans.question_id for ans in req.answers}
    remaining = len(question_ids) - len(submitted_ids)
    quiz_completed = remaining == 0

    return AnswerResponse(
        results=results,
        quiz_completed=quiz_completed,
        score_so_far=score,
        remaining=remaining,
        message="Answers processed successfully"
    )