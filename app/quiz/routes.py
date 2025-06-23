from fastapi import File, HTTPException, APIRouter, UploadFile
import logging
from upload.service import split_text
from quiz.service import load_text_and_generate_question, store_quiz_results
from upload.service import extract_and_save_text, split_text
from quiz.schemas import  QuizSessionResponse, AnswerRequest, AnswerResponse, QuestionType, UploadResponse

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
async def get_question(question_type: QuestionType):
    global current_state
    try:
        if current_state is None or not current_state.get("document_text"):
            raise HTTPException(status_code=404, detail="No document available. Upload a document first.")

        filename = current_state["original_filename"]
        logger.info(f"Fetching question of type '{question_type}' for '{filename}'")

        current_state["selected_question_type"] = question_type.value

        state = current_state
        if not state.get("chunks"):
            state = split_text(state)

        # Regenerate questions if none exist or no questions match the requested type
        if not state.get("questions") or not any(q.type.lower() == question_type.value.lower() for q in state["questions"]):
            logger.info(f"No questions of type '{question_type.value}' found. Regenerating...")
            state = load_text_and_generate_question(state, question_type.value)

        state = store_quiz_results(state)

        if state.get('error_message'):
            logger.error(f"Question generation failed for '{filename}': {state['error_message']}")
            raise HTTPException(status_code=400, detail=f"Failed to generate questions for '{filename}': {state['error_message']}")

        matching_questions = [q for q in state["questions"] if q.type.lower() == question_type.value.lower()]
        if not matching_questions:
            logger.error(f"No matching questions found for type '{question_type.value}' after generation")
            raise HTTPException(status_code=400, detail=f"No questions of type '{question_type}' generated for the document.")

        selected_question = matching_questions[0]
        logger.info(f"Selected question type: {selected_question.type} for '{filename}'")

        current_state = state

        return QuizSessionResponse(
            original_file_name=state["original_filename"],
            questions=[selected_question]
        )

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