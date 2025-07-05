import logging
from typing import Optional

from app.db.models import Quiz, Question as DBQuestion
from app.quiz.schemas import QuizGenerationState

logger = logging.getLogger(__name__)

async def store_questions(
    state: QuizGenerationState,
    quiz_title: Optional[str] = None,
    user_id: Optional[int] = None
) -> dict:
    filename = state.get('original_filename', 'unknown_file')
    logger.info(f"Starting to store questions for '{filename}' in database")

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
        
        from app.db.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            try:
                quiz_title = quiz_title or f"Quiz from {filename}"
                new_quiz = Quiz(
                    title=quiz_title,
                    owner_id=user_id
                )
                db.add(new_quiz)
                await db.flush()

                logger.info(f"Created quiz with ID: {new_quiz.id}")
                result['quiz_id'] = new_quiz.id

                question_ids = []
                for question in state['questions']:
                    try:
                        q_type_str = question.type.value
                        difficulty_str = question.difficulty

                        db_question = DBQuestion(
                            question=question.question,
                            type=q_type_str,
                            choices=question.choices if question.choices else [],
                            correct_answer=question.correct_answer,
                            explanation=question.explanation,
                            difficulty=difficulty_str,
                            quiz_id=new_quiz.id
                        )

                        db.add(db_question)
                        await db.flush()
                        question_ids.append(db_question.id)

                        logger.info(f"Stored question with ID: {db_question.id}")

                    except AttributeError as e:
                        error_msg = f"Invalid type or difficulty format in question: {str(e)}. Expected Enum, got something else."
                        logger.error(error_msg, exc_info=True)
                        result['error_message'] = error_msg
                        await db.rollback()
                        return result
                    except Exception as e:
                        error_msg = f"Error storing individual question: {str(e)}"
                        logger.error(error_msg, exc_info=True)
                        result['error_message'] = error_msg
                        await db.rollback()
                        return result

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
