from typing import TypedDict, Optional, List, Dict
class QuizState(TypedDict):
    session_id: str
    user_id: int
    document_id: int
    document_text: Optional[str]
    quiz_id: Optional[int]
    question_id: Optional[int]
    question: Optional[str]
    correct_answer: Optional[str]
    explanation: Optional[str]
    conversation_history: List[Dict[str, str]]