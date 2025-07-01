from fastapi import File, HTTPException, APIRouter, UploadFile
import logging
from app.upload.service import extract_chunks_with_metadata, store_chunks_in_qdrant
from app.quiz.service import load_text_and_generate_question, store_quiz_results
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

# Holds the current state across requests
upload_store = {"latest": None}
current_state = None


@quiz_routes.post("/upload_document", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    global current_state
    filename = file.filename or "unknown_file"
    logger.info(f"Uploading document: {filename}")

    try:
        # Step 1: Extract chunks and metadata
        chunks, metadata = await extract_chunks_with_metadata(file)

        # Step 2: Store in Qdrant
        store_chunks_in_qdrant(chunks, metadata)

        # Step 3: Store state
        current_state = {
            "original_filename": filename,
            "chunks": chunks,
            "chunk_metadata": metadata,
            "questions": [],
            "chunk_indices_used": [],
            "error_message": None,
        }
        upload_store["latest"] = current_state

        return UploadResponse(
            message="Document uploaded and chunks stored in Qdrant",
            original_filename=filename,
            uploaded_file_path="",  # Optional: path info
            text_file_path="",      # Optional: text output file path
            error_message=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in upload_document for '{filename}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Something went wrong: {str(e)}")


@quiz_routes.get("/get_question", response_model=QuizSessionResponse)
async def get_question(
    question_type: QuestionType,
    num_questions: QuestionCount = QuestionCount.THREE,
    difficulty_level: DifficultyLevel = DifficultyLevel.MEDIUM,
):
    try:
        if not upload_store.get("latest"):
            raise HTTPException(status_code=404, detail="No document uploaded. Please upload one first.")

        state = upload_store["latest"].copy()
        filename = state["original_filename"]

        state.setdefault("questions", [])
        state.setdefault("chunk_indices_used", [])
        state.setdefault("difficulty_by_type", {})
        state.setdefault("error_message", None)

        prev_difficulty = state["difficulty_by_type"].get(question_type.value.lower())
        prev_type = state["questions"][0].type.lower() if state["questions"] else None

        # Reset if new difficulty or type
        if prev_type != question_type.value.lower() or prev_difficulty != difficulty_level.value:
            logger.info("Regenerating due to question type or difficulty change.")
            state["questions"] = []
            state["chunk_indices_used"] = []

        state["selected_question_type"] = question_type.value
        state["difficulty_by_type"][question_type.value.lower()] = difficulty_level.value

        # Trigger question generation if needed
        existing = [q for q in state["questions"] if q.type.lower() == question_type.value.lower()]
        if not existing or len(existing) < num_questions.value:
            logger.info(f"Generating {num_questions.value} questions of type '{question_type.value}'...")
            state = load_text_and_generate_question(
                state=state,
                question_type=question_type.value,
                num_questions=num_questions.value,
                difficulty=difficulty_level.value
            )

        # Save quiz results to DB
        state = await store_quiz_results(state)

        if state.get("error_message"):
            raise HTTPException(status_code=400, detail=state["error_message"])

        upload_store["latest"] = state  # Update global store

        matching = [q for q in state["questions"] if q.type.lower() == question_type.value.lower()]
        if not matching:
            raise HTTPException(status_code=400, detail="No questions generated.")

        if len(matching) < num_questions.value:
            logger.warning(f"Only {len(matching)} questions generated out of requested {num_questions.value}")

        if state.get("database_stored"):
            logger.info(f"Questions stored in DB with quiz ID: {state.get('quiz_id')}")
        elif state.get("database_error"):
            logger.warning(f"Database storage failed: {state.get('database_error')}")

        return QuizSessionResponse(
            original_filename=state["original_filename"],
            questions=matching[:num_questions.value],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Something went wrong: {str(e)}")


@quiz_routes.post("/submit_answer", response_model=AnswerResponse)
async def submit_answer(request: AnswerRequest):
    try:
        if current_state is None or not current_state.get("questions"):
            raise HTTPException(status_code=404, detail="No quiz found. Generate questions first.")

        if not request.answer.strip():
            raise HTTPException(status_code=400, detail="Answer cannot be empty.")

        latest_question = current_state["questions"][-1]
        if request.question != latest_question.question:
            raise HTTPException(status_code=400, detail="Submitted question does not match the last question shown.")

        correct = latest_question.correct_answer.strip().lower()
        submitted = request.answer.strip().lower()

        return AnswerResponse(
            correct=(submitted == correct),
            correct_answer=latest_question.correct_answer,
            explanation=latest_question.explanation
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in submit_answer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Something went wrong: {str(e)}")
