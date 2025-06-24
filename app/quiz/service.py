#quiz/service.py
from langchain_ollama import OllamaLLM
import os
import json
from dotenv import load_dotenv
from app.quiz.schemas import QuizGenerationState, Question
import logging
from datetime import datetime
from app.quiz.prompts.mcq_prompt import  mcq_prompt
from app.quiz.prompts.faq_prompt import  faq_prompt
from app.quiz.prompts.boolean_prompt import boolean_prompt
from app.quiz.utils import store_questions
load_dotenv()

llm = OllamaLLM(base_url = os.getenv('OLLAMA_HOST'),model="llama3.2:latest")

os.makedirs("uploaded_documents", exist_ok=True)
os.makedirs("uploaded_documents/extracted_text", exist_ok=True)
os.makedirs("uploaded_documents/questions", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s ',
    handlers=[
        logging.FileHandler('quiz_generation.log'),
        logging.StreamHandler()   
        ]
)
logger = logging.getLogger(__name__)

    
def load_text_and_generate_question(state: QuizGenerationState, question_type: str) -> QuizGenerationState:
    filename = state['original_filename']
    logger.info(f"Starting question generation for '{filename}' with type '{question_type}'")

    try:
        if not state['chunks']:
            raise ValueError("No chunks available for question generation")

        text = "\n---\n".join(state['chunks'][:5])
        if not text.strip():
            raise ValueError("Combined chunks are empty")

        prompt_dict = {
            "mcq": mcq_prompt,
            "faq": faq_prompt,
            "boolean": boolean_prompt
        }
        if question_type not in prompt_dict:
            raise ValueError(f"Invalid question type: {question_type}. Must be 'mcq', 'faq', or 'boolean'")

        prompt_text = prompt_dict[question_type]
        formatted_prompt = prompt_text.replace("[Insert your context here]", text)

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = llm.invoke(formatted_prompt)
                response_text = str(response.content if hasattr(response, 'content') else response)
                logger.debug(f"LLM raw response for '{filename}' (attempt {attempt + 1}): {response_text}")

                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx == -1 or end_idx == 0:
                    raise ValueError("No valid JSON object in LLM response")

                result = json.loads(response_text[start_idx:end_idx])
                logger.debug(f"Parsed LLM result: {result}")
                if not isinstance(result, dict):
                    raise ValueError("Expected a single JSON object")

                if 'type' not in result:
                    result['type'] = question_type
                result['type'] = result['type'].lower()
                if result.get('type') != question_type:
                    logger.warning(f"Type mismatch: got {result['type']}, expected {question_type}. Forcing {question_type}")
                    result['type'] = question_type

                if not all(key in result for key in ['question', 'type', 'options', 'correct_answer', 'explanation']):
                    raise ValueError(f"Missing required fields in question: {result}")
                if question_type == 'mcq' and len(result.get('options', [])) != 4:
                    raise ValueError(f"MCQ must have exactly 4 options, got {len(result.get('options', []))}")
                if question_type in ['faq', 'boolean'] and result.get('options', []):
                    raise ValueError(f"{question_type} must have empty options")
                if question_type == 'boolean' and result['correct_answer'] not in ['True', 'False']:
                    raise ValueError(f"Boolean question must have 'True' or 'False' as correct_answer, got {result['correct_answer']}")

                state['questions'] = [
                    Question(
                        question=result['question'],
                        type=result['type'],
                        choices=result.get('options', []),
                        correct_answer=result['correct_answer'],
                        explanation=result['explanation']
                    )
                ]

                logger.info(f"Generated 1 question of type '{question_type}' for '{filename}'")
                state['error_message'] = None
                break

            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for '{filename}': {str(e)}")
                if attempt == max_retries - 1:
                    logger.error(f"All {max_retries} attempts failed for '{filename}': {str(e)}", exc_info=True)
                    state['error_message'] = f"Failed to generate valid question for '{filename}' after {max_retries} attempts: {str(e)}"
                    state['questions'] = []
                    return state
                continue

    except Exception as e:
        logger.error(f"Error in load_text_and_generate_question for '{filename}': {str(e)}", exc_info=True)
        state['error_message'] = f"Failed to generate questions for '{filename}': {str(e)}"
        state['questions'] = []

    return state
    

async def store_quiz_results(state: dict) -> dict:
    """
    Store quiz results both to file and database.
    Now includes database storage using the utils function.
    """
    filename = state['original_filename']
    logger.info(f"Starting to store quiz results for '{filename}'")

    try:
        if not state.get('questions'):
            logger.warning(f"No questions to store for '{filename}'")
            state['error_message'] = f"No questions available for '{filename}'"
            return state

        # Store to file (existing functionality)
        questions_dir = os.path.join("uploaded_documents", "questions")
        os.makedirs(questions_dir, exist_ok=True)

        safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_')).rstrip()
        questions_filename = f"{int(datetime.now().timestamp())}_{safe_filename}_questions.json"
        questions_file_path = os.path.join(questions_dir, questions_filename)

        questions_data = [q.dict() for q in state['questions']]

        with open(questions_file_path, 'w', encoding='utf-8') as f:
            json.dump(questions_data, f, indent=2)

        logger.info(f"Saved {len(state['questions'])} questions to file: {questions_file_path}")
        state['questions_file_path'] = questions_file_path

        try:
            # Create a quiz title from the filename
            quiz_title = f"Quiz from {safe_filename}"
            
            # Store in database
            db_result = await store_questions(state, quiz_title=quiz_title)
            
            if db_result['success']:
                logger.info(f"Successfully stored quiz in database with ID: {db_result['quiz_id']}")
                state['quiz_id'] = db_result['quiz_id']
                state['question_ids'] = db_result['question_ids']
                state['database_stored'] = True
            else:
                logger.error(f"Failed to store questions in database: {db_result['error_message']}")
                # Don't fail the entire operation if database storage fails
                state['database_error'] = db_result['error_message']
                state['database_stored'] = False
                
        except Exception as db_error:
            logger.error(f"Database storage failed for '{filename}': {str(db_error)}", exc_info=True)
            state['database_error'] = f"Database storage failed: {str(db_error)}"
            state['database_stored'] = False

        state['error_message'] = None

    except Exception as e:
        logger.error(f"Error storing quiz results for '{filename}': {str(e)}", exc_info=True)
        state['error_message'] = f"Failed to store quiz results for '{filename}': {str(e)}"
        state['questions_file_path'] = ""
        state['database_stored'] = False

    return state