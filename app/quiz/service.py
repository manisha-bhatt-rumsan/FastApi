# app/quiz/service.py
import json
import os
import random
import logging
from typing import List, Tuple
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

from app.db.models import DifficultyLevelEnum
from app.quiz.prompts.mcq_prompt import mcq_prompt
from app.quiz.prompts.faq_prompt import faq_prompt
from app.quiz.prompts.boolean_prompt import boolean_prompt
from app.quiz.schemas import Question
from app.quiz.utils import store_questions
from app.upload.service import qdrant_client, COLLECTION_NAME

load_dotenv()
llm = OllamaLLM(base_url=os.getenv("OLLAMA_HOST"), model="llama3.2:latest")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    logger.addHandler(h)

def fetch_chunks(doc_id: str) -> Tuple[List[str], List[dict]]:
    fltr = Filter(must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))])
    hits, _ = qdrant_client.scroll(COLLECTION_NAME, scroll_filter=fltr, limit=1000)
    chunks, meta = [], []
    for h in hits:
        chunks.append(h.payload["text"])
        meta.append({
            "page_number": h.payload.get("page_number", 1),
            "chunk_number": h.payload.get("chunk_number", 0)
        })
    if not chunks:
        raise ValueError("No content found for this document.")
    return chunks, meta

def build_prompt(qtype: str, difficulty: str, chunks: list[str], meta: list[dict]) -> str:
    context = "\n".join(
        f"(Page {m['page_number']}, Chunk {m['chunk_number']})\n{c}"
        for m, c in zip(meta, chunks)
    )
    templates = {
        "mcq": mcq_prompt,
        "faq": faq_prompt,
        "boolean": boolean_prompt
    }
    return templates[qtype.lower()].format(difficulty=difficulty, context=context)

def parse_response(text: str) -> dict:
    start, end = text.find("{"), text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("Response is not valid JSON.")
    return json.loads(text[start:end])

def check_valid(q: dict, qtype: str):
    if not all(k in q and q[k] for k in ["question", "correct_answer", "explanation"]):
        raise ValueError("Missing fields.")
    if qtype == "mcq" and len(q.get("options", [])) != 4:
        raise ValueError("MCQ must have 4 options.")
    if qtype in {"faq", "boolean"} and q.get("options"):
        raise ValueError(f"{qtype} should not have options.")

def generate_questions(
    doc_id: str,
    question_type: str,
    num: int = 3,
    difficulty: str = "Medium"
) -> List[Question]:
    # Map difficulty to enum
    difficulty_map = {
        "Easy": "easy",
        "Medium": "medium",
        "Hard": "hard"
    }
    
    chunks, meta = fetch_chunks(doc_id)
    indexes = list(range(len(chunks)))
    random.shuffle(indexes)
    created = []
    seen = set()

    while len(created) < num and indexes:
        idx = indexes[:2]
        indexes = indexes[2:]
        prompt = build_prompt(question_type, difficulty, [chunks[i] for i in idx], [meta[i] for i in idx])

        for _ in range(3):
            try:
                raw = llm.invoke(prompt)
                text = raw if isinstance(raw, str) else raw.content
                data = parse_response(text)

                if data["question"] in seen:
                    break
                if data.get("type", question_type).lower() != question_type.lower():
                    raise ValueError("Mismatched type.")
                check_valid(data, question_type)

                q = Question(
                    question=data["question"],
                    type=question_type.lower(),
                    choices=data.get("options", []),
                    correct_answer=data["correct_answer"],
                    explanation=data["explanation"],
                    difficulty=difficulty_map[difficulty]  # Use lowercase enum value
                )
                created.append(q)
                seen.add(q.question)
                break
            except Exception as e:
                logger.warning(f"Retry failed: {e}")
                continue

    return created

async def save_quiz_to_db(filename: str, questions: List[Question]) -> dict:
    if not questions:
        raise ValueError("No questions to save.")
    
    return await store_questions(
        {"original_filename": filename, "questions": questions},
        f"Quiz from {filename}"
    )