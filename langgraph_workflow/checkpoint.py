from langgraph.checkpoint.base import BaseCheckpointSaver
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance
import uuid
from app.config import settings
class QdrantCheckpoint(BaseCheckpointSaver):
    def __init__(self):
        self.client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        self.collection_name = "checkpoints"
        try:
            self.client.get_collection(self.collection_name)
        except:
            self.client.create_collection(
                self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
    async def aget(self, config):
        result = self.client.scroll(
            self.collection_name,
            scroll_filter={"must": [{"key": "config_id", "match": {"value": config["id"]}}]}
        )[0]
        return result[0].payload["checkpoint"] if result else None
    async def aput(self, config, checkpoint):
        self.client.upsert(
            self.collection_name,
            points=[
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=[0] * 384,
                    payload={"config_id": config["id"], "checkpoint": checkpoint}
                )
            ]
        )