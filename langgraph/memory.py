from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from app.config import settings
import uuid
client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
embedder = SentenceTransformer("all-MiniLM-L6-v2")
COLLECTION_NAME = "user_memory"
def setup_memory():
    try:
        client.get_collection(COLLECTION_NAME)
    except:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
setup_memory()
async def save_memory(user_id: int, conversation_history: list):
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=embedder.encode(f"{msg['user']} {msg['bot']}").tolist(),
            payload={"user_id": user_id, "user_message": msg["user"], "bot_message": msg["bot"]}
        )
        for msg in conversation_history
    ]
    client.upsert(collection_name=COLLECTION_NAME, points=points)
async def get_memory(user_id: int):
    result = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter={"must": [{"key": "user_id", "match": {"value": user_id}}]}
    )[0]
    return [{"user": point.payload["user_message"], "bot": point.payload["bot_message"]} for point in result]