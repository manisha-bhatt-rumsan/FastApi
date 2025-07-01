from langchain_ollama import OllamaLLM
import os
import json
<<<<<<< HEAD
from dotenv import load_dotenv
from app.quiz.schemas import QuizGenerationState, Question
import logging
from datetime import datetime
from app.quiz.prompts.mcq_prompt import  mcq_prompt
from app.quiz.prompts.faq_prompt import  faq_prompt
from app.quiz.prompts.boolean_prompt import boolean_prompt
from app.quiz.utils import store_questions
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from app.upload.service import qdrant_client, collection_name
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

=======
import logging
import random
from dotenv import load_dotenv
from app.quiz.schemas import QuizGenerationState, Question
from app.quiz.prompts.mcq_prompt import mcq_prompt
from app.quiz.prompts.faq_prompt import faq_prompt
from app.quiz.prompts.boolean_prompt import boolean_prompt
from app.quiz.utils import store_questions
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from app.upload.service import qdrant_client, COLLECTION_NAME
load_dotenv()

llm = OllamaLLM(base_url=os.getenv('OLLAMA_HOST'), model="llama3.2:latest")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('quiz_generation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


>>>>>>> qdrant
def load_text_and_generate_question(
    state: QuizGenerationState,
    question_type: str,
    num_questions: int = 3,
    difficulty: str = "Medium"
) -> QuizGenerationState:
<<<<<<< HEAD
    """
    Generate questions of the specified type with regeneration based on difficulty changes.
    Uses Qdrant to retrieve chunks if not available in state.
    """
=======
>>>>>>> qdrant
    filename = state.get('original_filename', 'unknown')
    logger.info(f"Starting generation of {num_questions} '{question_type}' questions for '{filename}' with difficulty '{difficulty}'")

    try:
<<<<<<< HEAD
        # Retrieve chunks from Qdrant if not in state
        if not state.get('chunks'):
=======
        # Step 1: Retrieve chunks with metadata from Qdrant
        if not state.get('chunks') or not state.get('chunk_metadata'):
>>>>>>> qdrant
            search_filter = Filter(
                must=[FieldCondition(key="filename", match=MatchValue(value=filename))]
            )
            search_result = qdrant_client.scroll(
<<<<<<< HEAD
                collection_name="quiz_chunks",
                scroll_filter=search_filter,
                limit=1000  # Adjust based on expected number of chunks
            )
            chunks = [hit.payload["text"] for hit in search_result[0]]
            chunk_ids = [hit.id for hit in search_result[0]]
            if not chunks:
                raise ValueError(f"No chunks found in Qdrant for filename '{filename}'")
            state["chunks"] = chunks
            state["chunk_ids"] = chunk_ids
            logger.info(f"Retrieved {len(chunks)} chunks from Qdrant for '{filename}'")

        # Initialize state if necessary
        if 'questions' not in state:
            state['questions'] = []
        if 'chunk_indices_used' not in state:
            state['chunk_indices_used'] = []
        if 'error_message' not in state:
            state['error_message'] = None
        state.setdefault('difficulty_by_type', {})

        # Force regeneration if difficulty changes for the same question type
        current_difficulty = state['difficulty_by_type'].get(question_type.lower(), None)
        if current_difficulty and current_difficulty != difficulty:
            state['questions'] = [q for q in state['questions'] if q.type.lower() != question_type.lower()]
            state['chunk_indices_used'] = []
            logger.info(f"Difficulty changed from '{current_difficulty}' to '{difficulty}'. Regenerating questions.")
        state['difficulty_by_type'][question_type.lower()] = difficulty

        # Filter existing questions of the same type
        existing_questions = {q.question for q in state['questions'] if q.type.lower() == question_type.lower()}
        questions_needed = num_questions - len(existing_questions)

        if questions_needed <= 0:
            logger.info(f"Enough '{question_type}' questions already exist for '{filename}'")
            return state

        prompt_dict = {"mcq": mcq_prompt, "faq": faq_prompt, "boolean": boolean_prompt}
        if question_type.lower() not in prompt_dict:
            raise ValueError(f"Invalid question type: {question_type}")

=======
                collection_name=COLLECTION_NAME,
                scroll_filter=search_filter,
                limit=1000
            )
            chunks = []
            metadata = []

            for hit in search_result[0]:
                chunks.append(hit.payload["text"])
                metadata.append({
                    "page_number": hit.payload.get("page_number", 1),
                    "chunk_number": hit.payload.get("chunk_number", 0)
                })

            if not chunks:
                raise ValueError(f"No chunks found in Qdrant for '{filename}'")

            state["chunks"] = chunks
            state["chunk_metadata"] = metadata
            logger.info(f"Retrieved {len(chunks)} chunks from Qdrant for '{filename}'")

        # Step 2: Initialize state
        state.setdefault("questions", [])
        state.setdefault("chunk_indices_used", [])
        state.setdefault("difficulty_by_type", {})
        state.setdefault("error_message", None)

        current_difficulty = state["difficulty_by_type"].get(question_type.lower())
        if current_difficulty and current_difficulty != difficulty:
            state["questions"] = [q for q in state["questions"] if q.type.lower() != question_type.lower()]
            state["chunk_indices_used"] = []
            logger.info(f"Difficulty changed. Regenerating questions for type '{question_type}'.")

        state["difficulty_by_type"][question_type.lower()] = difficulty

        existing_questions = {q.question for q in state["questions"] if q.type.lower() == question_type.lower()}
        questions_needed = num_questions - len(existing_questions)

        if questions_needed <= 0:
            logger.info(f"Already have enough '{question_type}' questions.")
            return state

        prompt_dict = {
            "mcq": mcq_prompt,
            "faq": faq_prompt,
            "boolean": boolean_prompt
        }
        if question_type.lower() not in prompt_dict:
            raise ValueError(f"Invalid question type: {question_type}")

        available_indices = [i for i in range(len(state["chunks"])) if i not in state["chunk_indices_used"]]
        if not available_indices:
            logger.warning("No unused chunks left. Reusing all.")
            available_indices = list(range(len(state["chunks"])))
        random.shuffle(available_indices)

>>>>>>> qdrant
        generated_questions = []
        chunk_indices_used = []
        max_retries = 3

<<<<<<< HEAD
        available_indices = [i for i in range(len(state['chunks'])) if i not in state['chunk_indices_used']]
        if not available_indices:
            available_indices = list(range(len(state['chunks'])))
            logger.warning("No unused chunks available; reusing all chunks.")
        random.shuffle(available_indices)

        while len(generated_questions) < questions_needed and available_indices:
            batch_indices = available_indices[:2] if len(available_indices) >= 2 else available_indices
            batch_chunks = [state['chunks'][idx] for idx in batch_indices]
            text = "\n---\n".join(batch_chunks)
            if not text.strip():
                logger.warning(f"Empty batch for chunks {batch_indices}")
                available_indices = [i for i in available_indices if i not in batch_indices]
                continue

            # Format the prompt using PromptTemplate's format method
            formatted_prompt = prompt_dict[question_type.lower()].format(difficulty=difficulty, context=text)

            for attempt in range(max_retries):
                try:
                    response = llm.invoke(formatted_prompt)
                    response_text = response if isinstance(response, str) else response.content
                    start_idx = response_text.find('{')
                    end_idx = response_text.rfind('}') + 1
                    if start_idx == -1 or end_idx == 0:
                        raise ValueError("No valid JSON object in LLM response")

                    result = json.loads(response_text[start_idx:end_idx])
                    if not isinstance(result, dict):
                        raise ValueError("Expected a single JSON object")

                    result['type'] = result.get('type', question_type).lower()
                    if result['type'] != question_type.lower():
                        raise ValueError(f"Generated type '{result['type']}' does not match requested '{question_type}'")

                    if question_type.lower() == 'mcq':
                        if len(result.get('options', [])) != 4 or not all(isinstance(opt, str) for opt in result.get('options', [])):
                            raise ValueError("MCQ must have exactly 4 string options")
                    elif question_type.lower() == 'boolean':
                        if result.get('options', []):
                            raise ValueError("Boolean questions must have no options")
                        if result['correct_answer'] not in ['True', 'False']:
                            raise ValueError("Boolean correct_answer must be 'True' or 'False'")
                    elif question_type.lower() == 'faq':
                        if result.get('options', []):
                            raise ValueError("FAQ questions must have no options")

                    if 'question' not in result or 'correct_answer' not in result or 'explanation' not in result:
                        raise ValueError("Missing required fields: 'question', 'correct_answer', or 'explanation'")

                    if result['question'] in existing_questions:
                        logger.warning(f"Duplicate question detected: {result['question']}")
                        continue

                    question = Question(
                        question=result['question'],
                        type=question_type.lower(),
                        choices=result.get('options', []),
                        correct_answer=result['correct_answer'],
                        explanation=result['explanation'],
                        difficulty=difficulty
                    )
                    generated_questions.append(question)
                    existing_questions.add(result['question'])
                    chunk_indices_used.extend(batch_indices)
                    logger.info(f"Generated question {len(generated_questions)} of type '{question_type}' for '{filename}'")
                    break

                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed for batch {batch_indices}: {str(e)}")
                    if attempt == max_retries - 1:
                        logger.error(f"All retries failed for batch {batch_indices}: {str(e)}")
                        available_indices = [i for i in available_indices if i not in batch_indices]
                        break

            available_indices = [i for i in available_indices if i not in batch_indices]

        state['questions'].extend(generated_questions)
        state['chunk_indices_used'].extend(chunk_indices_used)
        state['error_message'] = None if len(generated_questions) == questions_needed else f"Generated only {len(generated_questions)} out of {questions_needed} '{question_type}' questions for '{filename}'"
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
=======
        while len(generated_questions) < questions_needed and available_indices:
            batch_indices = available_indices[:2]
            batch_chunks = [state["chunks"][i] for i in batch_indices]
            batch_metadata = [state["chunk_metadata"][i] for i in batch_indices]

            context_header = "\n".join([
                f"(Page {m['page_number']}, Chunk {m['chunk_number']})\n{chunk}"
                for m, chunk in zip(batch_metadata, batch_chunks)
            ])
            prompt = prompt_dict[question_type.lower()].format(difficulty=difficulty, context=context_header)

            for attempt in range(max_retries):
                try:
                    response = llm.invoke(prompt)
                    response_text = response if isinstance(response, str) else response.content
                    start, end = response_text.find("{"), response_text.rfind("}") + 1
                    if start == -1 or end == 0:
                        raise ValueError("No valid JSON found in response.")
                    parsed = json.loads(response_text[start:end])

                    if parsed.get("question") in existing_questions:
                        logger.warning("Duplicate question skipped.")
                        break

                    q_type = parsed.get("type", question_type).lower()
                    if q_type != question_type.lower():
                        raise ValueError(f"LLM returned wrong question type: {q_type}")

                    if question_type.lower() == "mcq":
                        if len(parsed.get("options", [])) != 4:
                            raise ValueError("MCQ must have 4 options.")
                    elif question_type.lower() in {"faq", "boolean"} and parsed.get("options"):
                        raise ValueError(f"{question_type} should not have options.")

                    if not all(k in parsed for k in ["question", "correct_answer", "explanation"]):
                        raise ValueError("Missing required fields.")

                    question = Question(
                        question=parsed["question"],
                        type=question_type.lower(),
                        choices=parsed.get("options", []),
                        correct_answer=parsed["correct_answer"],
                        explanation=parsed["explanation"],
                        difficulty=difficulty
                    )
                    generated_questions.append(question)
                    existing_questions.add(parsed["question"])
                    chunk_indices_used.extend(batch_indices)
                    logger.info(f"Generated '{question_type}' question.")
                    break

                except Exception as e:
                    logger.warning(f"Retry {attempt + 1} failed: {e}")
                    if attempt == max_retries - 1:
                        logger.error(f"All retries failed for chunks {batch_indices}: {e}")

            available_indices = [i for i in available_indices if i not in batch_indices]

        state["questions"].extend(generated_questions)
        state["chunk_indices_used"].extend(chunk_indices_used)
        state["error_message"] = None if len(generated_questions) == questions_needed else f"Only {len(generated_questions)} out of {questions_needed} generated."
        logger.info(f"Finished generation of {len(generated_questions)} questions.")
        return state

    except Exception as e:
        logger.error(f"Error during question generation: {e}", exc_info=True)
        state["error_message"] = str(e)
        return state


async def store_quiz_results(state: dict) -> dict:
    filename = state.get("original_filename", "unknown")
    logger.info(f"Storing quiz results for '{filename}'")

    try:
        if not state.get("questions"):
            state["error_message"] = "No questions to store."
            return state

        quiz_title = f"Quiz from {filename}"
        db_result = await store_questions(state, quiz_title=quiz_title)

        if db_result.get("success"):
            state["quiz_id"] = db_result["quiz_id"]
            state["question_ids"] = db_result["question_ids"]
            state["database_stored"] = True
        else:
            state["database_stored"] = False
            state["database_error"] = db_result.get("error_message")

        return state

    except Exception as e:
        logger.error(f"Failed to store quiz results: {e}", exc_info=True)
        state["database_error"] = str(e)
        state["database_stored"] = False
        return state
>>>>>>> qdrant
