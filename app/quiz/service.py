from langchain_ollama import OllamaLLM
import os
import json
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


def load_text_and_generate_question(
    state: QuizGenerationState,
    question_type: str,
    num_questions: int = 3,
    difficulty: str = "Medium"
) -> QuizGenerationState:
    doc_id = state.get("doc_id")
    if not doc_id:
        raise ValueError("Missing document ID in state.")
    logger.info(f"Starting generation of {num_questions} '{question_type}' questions for doc_id '{doc_id}' with difficulty '{difficulty}'")

    try:
        # Step 1: Retrieve chunks with metadata from Qdrant using doc_id
        if not state.get('chunks') or not state.get('chunk_metadata'):
            search_filter = Filter(
                must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
            )
            search_result = qdrant_client.scroll(
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
                raise ValueError(f"No chunks found in Qdrant for doc_id '{doc_id}'")

            state["chunks"] = chunks
            state["chunk_metadata"] = metadata
            logger.info(f"Retrieved {len(chunks)} chunks from Qdrant for doc_id '{doc_id}'")

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

        generated_questions = []
        chunk_indices_used = []
        max_retries = 3

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
