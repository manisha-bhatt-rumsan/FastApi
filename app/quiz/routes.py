from fastapi import File, HTTPException, APIRouter, UploadFile, Query
import logging
from app.upload.service import extract_chunks_with_metadata, store_chunks_in_qdrant
from app.quiz.service import generate_questions, save_quiz_to_db
from app.quiz.schemas import (
    QuizSessionResponse,
    AnswerRequest,
    AnswerResponse,
    QuestionType,
    UploadResponse,
    QuestionCount,
    DifficultyLevel,
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

doc_lookup: dict[str, str] = {}          # doc_id -> original filename
latest_batch: dict[str, list] = {}       # remembers last questions per doc_id


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

        # Save to DB (optional but recommended)
        await save_quiz_to_db(doc_lookup[document_id], questions)

        # Remember this batch for /submit_answer
        latest_batch[document_id] = questions

        return QuizSessionResponse(
            original_filename=doc_lookup[document_id],
            questions=questions[: num_questions.value],
        )

    except Exception as exc:
        logger.error("Generation failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))



@quiz_routes.post("/submit_answer", response_model=AnswerResponse)
async def submit_answer(request: AnswerRequest, document_id: str = Query(...)):
    if document_id not in latest_batch or not latest_batch[document_id]:
        raise HTTPException(status_code=404, detail="No active quiz for this document_id.")

    latest_q = latest_batch[document_id][-1]

    if request.question != latest_q.question:
        raise HTTPException(status_code=400, detail="Question mismatch.")

    is_correct = request.answer.strip().lower() == latest_q.correct_answer.strip().lower()

    return AnswerResponse(
        correct=is_correct,
        correct_answer=latest_q.correct_answer,
        explanation=latest_q.explanation,
    )