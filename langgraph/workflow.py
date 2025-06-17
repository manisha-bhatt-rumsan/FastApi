from langgraph.graph import StateGraph, END
from app.langgraph.state import QuizState
from app.langgraph.memory import save_memory, get_memory
from app.langgraph.checkpoint import QdrantCheckpoint
from app.langgraph.utils import save_document_text, generate_question, store_quiz_results
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from fastapi import Depends
import logging
logger = logging.getLogger(__name__)
async def conversation_task(state: QuizState, db: AsyncSession = Depends(get_db)) -> QuizState:
    logger.info(f"Saving conversation for session {state['session_id']}")
    state["conversation_history"].append(
        {"user": f"Requested quiz for document {state['document_id']}", "bot": f"Generated question: {state['question']}"}
    )
    await save_memory(state["user_id"], state["conversation_history"])
    return state
def build_workflow():
    workflow = StateGraph(QuizState)
    workflow.add_node("save_text", save_document_text)
    workflow.add_node("generate_question", generate_question)
    workflow.add_node("conversation", conversation_task)
    workflow.add_node("store_results", store_quiz_results)
    workflow.set_entry_point("save_text")
    workflow.add_edge("save_text", "generate_question")
    workflow.add_edge("generate_question", "conversation")
    workflow.add_edge("conversation", "store_results")
    workflow.add_edge("store_results", END)
    return workflow.compile(checkpointer=QdrantCheckpoint())