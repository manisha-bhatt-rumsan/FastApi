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
import random
load_dotenv()

llm = OllamaLLM(base_url = os.getenv('OLLAMA_HOST'), model="llama3.2:latest")

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

    
def load_text_and_generate_question(
    state: QuizGenerationState,
    question_type: str,
    num_questions: int = 3,
    difficulty: str = "Medium"
) -> QuizGenerationState:
    """
    Generate questions of the specified type with strict validation to prevent hallucination.
    """
    filename = state.get('original_filename', 'unknown')
    logger.info(f"Starting generation of {num_questions} '{question_type}' questions for '{filename}' with difficulty '{difficulty}'")

    try:
        if not state.get('chunks'):
            raise ValueError("No chunks provided for question generation")

        if 'questions' not in state:
            state['questions'] = []
        state['questions'] = [q for q in state['questions'] if q.type.lower() == question_type.lower()]  # Keep only matching type
        if 'chunk_indices_used' not in state:
            state['chunk_indices_used'] = []
        if 'error_message' not in state:
            state['error_message'] = None

        existing_questions = {q.question for q in state['questions']}

        prompt_dict = {"mcq": mcq_prompt, "faq": faq_prompt, "boolean": boolean_prompt}
        if question_type not in prompt_dict:
            raise ValueError(f"Invalid question type: {question_type}")

        prompt_text = prompt_dict[question_type].replace("[Difficulty]", difficulty)
        generated_questions = []
        chunk_indices_used = []
        max_retries = 3

        available_indices = [i for i in range(len(state['chunks'])) if i not in state['chunk_indices_used']]
        if not available_indices:
            available_indices = list(range(len(state['chunks'])))
        random.shuffle(available_indices)

        for i in range(0, len(available_indices), 2):
            if len(generated_questions) >= num_questions:
                break

            batch_indices = available_indices[i:i + 2]
            batch_chunks = [state['chunks'][idx] for idx in batch_indices]
            text = "\n---\n".join(batch_chunks)
            if not text.strip():
                logger.warning(f"Empty batch for chunks {batch_indices}")
                continue

            formatted_prompt = prompt_text.replace("[Insert your context here]", text)

            for attempt in range(max_retries):
                try:
                    response = llm.invoke(formatted_prompt)
                    response_text = str(response.content if hasattr(response, 'content') else response)
                    start_idx = response_text.find('{')
                    end_idx = response_text.rfind('}') + 1
                    if start_idx == -1 or end_idx == 0:
                        raise ValueError("No valid JSON object in LLM response")

                    result = json.loads(response_text[start_idx:end_idx])
                    if not isinstance(result, dict):
                        raise ValueError("Expected a single JSON object")

                    # Enforce strict type-specific validation
                    if 'type' not in result:
                        result['type'] = question_type
                    result['type'] = result['type'].lower()
                    if result['type'] != question_type.lower():
                        raise ValueError(f"Generated type '{result['type']}' does not match requested '{question_type}'")

                    if question_type == 'mcq':
                        if len(result.get('options', [])) != 4 or not all(isinstance(opt, str) for opt in result.get('options', [])):
                            raise ValueError("MCQ must have exactly 4 string options")
                    elif question_type == 'boolean':
                        if result.get('options', []):
                            raise ValueError("Boolean questions must have no options")
                        if result['correct_answer'] not in ['True', 'False']:
                            raise ValueError("Boolean correct_answer must be 'True' or 'False'")
                    elif question_type == 'faq':
                        if result.get('options', []):
                            raise ValueError("FAQ questions must have no options")

                    if 'question' not in result or 'correct_answer' not in result or 'explanation' not in result:
                        raise ValueError("Missing required fields: 'question', 'correct_answer', or 'explanation'")

                    if result['question'] in existing_questions:
                        logger.warning(f"Duplicate question detected: {result['question']}")
                        continue

                    question = Question(
                        question=result['question'],
                        type=question_type,
                        choices=result.get('options', []),
                        correct_answer=result['correct_answer'],
                        explanation=result.get('explanation', '')
                    )
                    generated_questions.append(question)
                    existing_questions.add(result['question'])
                    chunk_indices_used.extend(batch_indices)
                    logger.info(f"Generated question {len(generated_questions)} of type '{question_type}' for '{filename}' using chunks {batch_indices}")
                    break

                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed for batch {batch_indices}: {str(e)}")
                    if attempt == max_retries - 1:
                        logger.error(f"All retries failed for batch {batch_indices}: {str(e)}")
                        continue

        state['questions'].extend(generated_questions)
        state['chunk_indices_used'].extend(chunk_indices_used)
        state['error_message'] = None if generated_questions else f"Failed to generate {num_questions} '{question_type}' questions for '{filename}'"
        logger.info(f"Completed generation with {len(generated_questions)} '{question_type}' questions for '{filename}'")
        return state

    except Exception as e:
        logger.error(f"Error in question generation for '{filename}': {str(e)}", exc_info=True)
        state['error_message'] = f"Failed to generate questions for '{filename}': {str(e)}"
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