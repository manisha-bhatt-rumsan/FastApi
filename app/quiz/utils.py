from app.db.models import Quiz, Question as DBQuestion
from app.quiz.schemas import QuizGenerationState
from app.db.database import AsyncSessionLocal
import logging
from typing import Optional

logger = logging.getLogger(__name__)

async def store_questions(
    state: QuizGenerationState, 
    quiz_title: Optional[str] = None,
    user_id: Optional[int] = None
) -> dict:
    filename = state.get('original_filename', 'unknown_file')
    logger.info(f"Starting to store questions for '{filename}' in database")
    
    # Initialize return values
    result = {
        'quiz_id': None,
        'question_ids': [],
        'error_message': None,
        'success': False
    }
    
    try:
        if not state.get('questions'):
            error_msg = f"No questions to store for '{filename}'"
            logger.warning(error_msg)
            result['error_message'] = error_msg
            return result

        async with AsyncSessionLocal() as db:
            try:
                # Create a new quiz
                quiz_title = quiz_title or f"Quiz from {filename}"
                new_quiz = Quiz(
                    title=quiz_title,
                    owner_id=user_id  # Will be None for now
                )
                db.add(new_quiz)
                await db.flush()
                
                logger.info(f"Created quiz with ID: {new_quiz.id}")
                result['quiz_id'] = new_quiz.id
                
                # Store each question
                question_ids = []
                for question in state['questions']:
                    try:
                        # Create database question
                        db_question = DBQuestion(
                            question=question.question,
                            type=question.type.lower(),
                            choices=question.choices if question.choices else [],
                            correct_answer=question.correct_answer,
                            explanation=question.explanation,
                            quiz_id=new_quiz.id
                        )
                        
                        db.add(db_question)
                        await db.flush()  # Flush to get the question ID
                        question_ids.append(db_question.id)
                        
                        logger.info(f"Stored question with ID: {db_question.id}")
                        
                    except ValueError as e:
                        error_msg = f"Invalid question type '{question.type}': {str(e)}"
                        logger.error(error_msg)
                        result['error_message'] = error_msg
                        await db.rollback()
                        return result
                    
                    except Exception as e:
                        error_msg = f"Error storing individual question: {str(e)}"
                        logger.error(error_msg, exc_info=True)
                        result['error_message'] = error_msg
                        await db.rollback()
                        return result
                
                # Commit all changes
                await db.commit()
                
                result['question_ids'] = question_ids
                result['success'] = True
                
                logger.info(f"Successfully stored {len(question_ids)} questions for quiz '{quiz_title}' (ID: {new_quiz.id})")
                
            except Exception as e:
                await db.rollback()
                error_msg = f"Database transaction failed for '{filename}': {str(e)}"
                logger.error(error_msg, exc_info=True)
                result['error_message'] = error_msg
                return result
                
    except Exception as e:
        error_msg = f"Failed to connect to database for '{filename}': {str(e)}"
        logger.error(error_msg, exc_info=True)
        result['error_message'] = error_msg
        return result
    
    return result