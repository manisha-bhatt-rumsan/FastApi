import logging
import json
from openai import OpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.database import get_db
from app.models import Document, Quiz, Question
from app.schemas import QuestionCreate
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('quiz_generator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client for Ollama
client = OpenAI(
    base_url=f"{settings.ollama_host}/v1",
    api_key=settings.ollama_api_key
)

# Node 1: Save document text to PostgreSQL
async def save_document_text(state: dict, db: AsyncSession = Depends(get_db)) -> dict:
    logger.info(f"Saving document text for session: {state['session_id']}")
    try:
        document_id = state["document_id"]
        document_text = state["document_text"]
        
        # Update document in PostgreSQL
        db_document = await db.get(Document, document_id)
        if not db_document:
            logger.error(f"Document ID {document_id} not found")
            raise ValueError(f"Document ID {document_id} not found")
        db_document.content = document_text
        await db.commit()
        await db.refresh(db_document)
        
        state["document_id"] = db_document.id
        logger.info(f"Document text saved for document ID: {document_id}")
        return state
    
    except Exception as e:
        logger.error(f"Error in save_document_text: {str(e)}")
        raise Exception(f"Failed to save document text: {str(e)}")

# Node 2: Generate quiz question from document text
async def generate_question(state: dict, db: AsyncSession = Depends(get_db)) -> dict:
    logger.info(f"Generating question for session: {state['session_id']}")
    try:
        document_id = state["document_id"]
        
        # Load document from PostgreSQL
        db_document = await db.get(Document, document_id)
        if not db_document or not db_document.content:
            logger.error(f"Document ID {document_id} has no content")
            raise ValueError(f"Document ID {document_id} has no content")
        
        document_text = db_document.content
        logger.info(f"Loaded document text for ID: {document_id}")
        
        # Prompt for question generation
        prompt = f"""You are an expert educational content creator. Generate a high-quality question based on the document.

RULES:
- Generate ONE question
- Test comprehension, not just memory
- Focus on key concepts or facts
- Provide the correct answer and a brief explanation
- Return valid JSON

DOCUMENT TEXT:
{document_text}

OUTPUT FORMAT:
{{
    "question": "Your question here?",
    "correct_answer": "The correct answer here",
    "explanation": "Brief explanation of why this is correct"
}}"""

        logger.info("Sending request to Ollama via OpenAI SDK")
        try:
            response = client.chat.completions.create(
                model=settings.ollama_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            content = response.choices[0].message.content.strip()
            result = json.loads(content)
            
            # Validate response
            required_fields = ["question", "correct_answer", "explanation"]
            for field in required_fields:
                if field not in result or not result[field]:
                    logger.error(f"Missing or empty field: {field}")
                    raise ValueError(f"Missing or empty field: {field}")
            
            state["question"] = result["question"]
            state["correct_answer"] = result["correct_answer"]
            state["explanation"] = result["explanation"]
            logger.info(f"Question generated: {result['question']}")
        
        except Exception as e:
            logger.error(f"Ollama request failed: {str(e)}")
            raise Exception(f"Failed to generate question: {str(e)}")
        
        return state
    
    except Exception as e:
        logger.error(f"Error in generate_question: {str(e)}")
        raise Exception(f"Failed to generate question: {str(e)}")

# Node 3: Store quiz results in PostgreSQL
async def store_quiz_results(state: dict, db: AsyncSession = Depends(get_db)) -> dict:
    logger.info(f"Storing quiz results for session: {state['session_id']}")
    try:
        user_id = state["user_id"]
        document_id = state["document_id"]
        
        # Create quiz
        quiz_title = f"Quiz for Document {document_id}"
        db_quiz = Quiz(title=quiz_title, owner_id=user_id)
        db.add(db_quiz)
        await db.commit()
        await db.refresh(db_quiz)
        
        # Store question
        question_data = QuestionCreate(
            text=state["question"],
            correct_answer=state["correct_answer"],
            explanation=state["explanation"],
            quiz_id=db_quiz.id
        )
        db_question = Question(**question_data.model_dump())
        db.add(db_question)
        await db.commit()
        await db.refresh(db_question)
        
        state["quiz_id"] = db_quiz.id
        state["question_id"] = db_question.id
        logger.info(f"Quiz ID {db_quiz.id} and Question ID {db_question.id} stored")
        return state
    
    except Exception as e:
        logger.error(f"Error in store_quiz_results: {str(e)}")
        raise Exception(f"Failed to store quiz results: {str(e)}")