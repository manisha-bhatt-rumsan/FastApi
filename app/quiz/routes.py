#quiz/routes.py
from fastapi import File, HTTPException, APIRouter, UploadFile
import logging
from app.upload.service import split_text,extract_and_save_text
from app.quiz.service import load_text_and_generate_question, store_quiz_results
from app.quiz.schemas import  QuizSessionResponse, AnswerRequest, AnswerResponse, QuestionType, UploadResponse, QuestionCount, DifficultyLevel

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('quiz_generator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

quiz_routes=APIRouter()

current_state = None

upload_store = {"latest": None}

@quiz_routes.post("/upload_document", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    global current_state
    filename = file.filename or "unknown_file"
    logger.info(f"Uploading document: {filename}")

    try:
        # Step 1: Extract and save text
        state = await extract_and_save_text(file)

        # Step 2: Split text into chunks
        state = split_text(state)

        # Check for errors
        if state.get('error_message'):
            logger.error(f"Processing failed for '{filename}': {state['error_message']}")
            raise HTTPException(status_code=400, detail=f"Failed to process '{filename}': {state['error_message']}")

        # Update global state
        current_state = state
        upload_store["latest"] = state

        return UploadResponse(
            message="Document uploaded, text saved, and text split into chunks",
            original_filename=state["original_filename"],
            uploaded_file_path=state["uploaded_file_path"],
            text_file_path=state["text_file_path"],
            error_message=None
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
    difficulty_level: DifficultyLevel = DifficultyLevel.MEDIUM
):
    try:
        if "latest" not in upload_store or upload_store["latest"] is None:
            raise HTTPException(status_code=404, detail="No document uploaded. Please upload a document first.")

        state = upload_store["latest"].copy()  # Work with a copy
        filename = state["original_filename"]
        logger.info(f"Fetching {num_questions.value} questions of type '{question_type.value}' with difficulty '{difficulty_level.value}' for '{filename}'")

        # Clear existing questions if type or difficulty changes
        current_questions = state.get("questions", [])
        if current_questions:
            last_type = current_questions[0].type.lower() if current_questions else None
            last_difficulty = state.get("last_difficulty", None)
            if last_type != question_type.value.lower() or last_difficulty != difficulty_level.value:
                state["questions"] = []
                state["chunk_indices_used"] = []  # Reset used chunks for new generation
                state["last_difficulty"] = difficulty_level.value  # Track last used difficulty

        current_state["selected_question_type"] = question_type.value

        state = current_state
        if not state.get("chunks"):
            state = split_text(state)

        if not state.get("questions") or not any(q.type.lower() == question_type.value.lower() for q in state["questions"]):
            logger.info(f"No matching questions found. Regenerating {num_questions.value} questions...")
            state = load_text_and_generate_question(state, question_type.value, num_questions=num_questions.value, difficulty=difficulty_level.value)

        state = await store_quiz_results(state)

        if state.get('error_message'):
            raise HTTPException(status_code=400, detail=state['error_message'])

        upload_store["latest"] = state  # Update with new state

        if state["questions"]:
            questions_of_type = [q for q in state["questions"] if q.type.lower() == question_type.value.lower()]
            if len(questions_of_type) < num_questions.value:
                logger.warning(f"Regenerating due to insufficient questions: found {len(questions_of_type)}, need {num_questions.value}")
                state = load_text_and_generate_question(state, question_type.value, num_questions=num_questions.value, difficulty=difficulty_level.value)
                questions_of_type = [q for q in state["questions"] if q.type.lower() == question_type.value.lower()]

            response_data = {
                "original_filename": state["original_filename"],
                "questions": questions_of_type[:num_questions.value]
            }
            if len(response_data["questions"]) < num_questions.value:
                logger.warning(f"Only {len(response_data['questions'])} questions available, requested {num_questions.value}")
        else:
            raise HTTPException(status_code=400, detail="No questions generated")

        if state.get('database_stored'):
            logger.info(f"Questions stored in database with quiz ID: {state.get('quiz_id')}")
        elif state.get('database_error'):
            logger.warning(f"Database storage failed: {state.get('database_error')}")

        return QuizSessionResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_question: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Something went wrong: {str(e)}")@quiz_routes.get("/get_question", response_model=QuizSessionResponse)
async def get_question(
    question_type: QuestionType,
    num_questions: QuestionCount = QuestionCount.THREE,
    difficulty_level: DifficultyLevel = DifficultyLevel.MEDIUM
):
    try:
        if "latest" not in upload_store or upload_store["latest"] is None:
            raise HTTPException(status_code=404, detail="No document uploaded. Please upload a document first.")

        state = upload_store["latest"].copy()  # Work with a copy
        filename = state["original_filename"]
        logger.info(f"Fetching {num_questions.value} questions of type '{question_type.value}' with difficulty '{difficulty_level.value}' for '{filename}'")

        # Regenerate questions if type or difficulty changes
        current_questions = [q for q in state.get("questions", []) if q.type.lower() == question_type.value.lower()]
        last_difficulty = state.get("difficulty_by_type", {}).get(question_type.value.lower(), None)
        if len(current_questions) < num_questions.value or last_difficulty != difficulty_level.value:
            logger.info(f"Regenerating questions due to type/difficulty change or insufficient questions.")
            state = load_text_and_generate_question(
                state,
                question_type=question_type.value,
                num_questions=num_questions.value,
                difficulty=difficulty_level.value
            )

        state = await store_quiz_results(state)

        if state.get('error_message'):
            raise HTTPException(status_code=400, detail=state['error_message'])

        upload_store["latest"] = state  # Update with new state
        current_state = state  # Sync global state

        questions_of_type = [q for q in state["questions"] if q.type.lower() == question_type.value.lower()]
        if not questions_of_type:
            raise HTTPException(status_code=400, detail="No questions generated")

        response_data = {
            "original_filename": state["original_filename"],
            "questions": questions_of_type[:num_questions.value]
        }
        if len(response_data["questions"]) < num_questions.value:
            logger.warning(f"Only {len(response_data['questions'])} questions available, requested {num_questions.value}")

        if state.get('database_stored'):
            logger.info(f"Questions stored in database with quiz ID: {state.get('quiz_id')}")
        elif state.get('database_error'):
            logger.warning(f"Database storage failed: {state.get('database_error')}")

        return QuizSessionResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_question: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Something went wrong: {str(e)}")
    
    
@quiz_routes.post("/submit_answer", response_model=AnswerResponse)
async def submit_answer(request: AnswerRequest):
    try:
        if current_state is None or not current_state.get("questions"):
            raise HTTPException(status_code=404, detail="No quiz available. Generate questions first.")

        if not request.answer.strip():
            raise HTTPException(status_code=400, detail="Answer cannot be empty.")

        latest_question = current_state["questions"][-1]

        if request.question != latest_question.question:
            raise HTTPException(status_code=400, detail="Submitted question does not match the current quiz question.")

        correct_answer = latest_question.correct_answer
        is_correct = request.answer.strip().lower() == correct_answer.lower()

        explanation = latest_question.explanation

        return AnswerResponse(
            correct=is_correct,
            correct_answer=correct_answer,
            explanation=explanation
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in submit_answer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Something went wrong: {str(e)}")