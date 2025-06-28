from fastapi import HTTPException, UploadFile
from docx import Document
from io import BytesIO
import pymupdf4llm
import os
import logging
from datetime import datetime
from app.upload.schemas import QuizGenerationState
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance
import uuid
from app.config import settings
import requests

# Configure logging
logger = logging.getLogger(__name__)

# Get configuration from settings
QDRANT_HOST = settings.qdrant_host
QDRANT_PORT = settings.qdrant_port
OLLAMA_HOST = settings.ollama_host
collection_name = "quiz_chunks"

# Log configuration for debugging
logger.info(f"Qdrant configuration: host={QDRANT_HOST}, port={QDRANT_PORT}, collection={collection_name}")
logger.info(f"Ollama configuration: base_url={OLLAMA_HOST}")

# Initialize Qdrant client
try:
    qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    logger.info("Successfully initialized Qdrant client")
except Exception as e:
    logger.error(f"Failed to initialize Qdrant client: {str(e)}")
    raise

# Function to generate embeddings using Ollama
def get_ollama_embeddings(texts: list[str], model: str = "nomic-embed-text") -> list[list[float]]:
    """
    Generate embeddings for a list of texts using Ollama's embedding API.
    """
    try:
        embeddings = []
        for text in texts:
            response = requests.post(
                f"{OLLAMA_HOST}/api/embeddings",
                json={"model": model, "prompt": text}
            )
            response.raise_for_status()  # Raise an exception for HTTP errors
            embedding = response.json().get("embedding")
            if not embedding or not isinstance(embedding, list):
                raise ValueError(f"Invalid embedding response for text: {text[:50]}...")
            embeddings.append(embedding)
        logger.info(f"Generated {len(embeddings)} embeddings using Ollama {model}")
        return embeddings
    except Exception as e:
        logger.error(f"Failed to generate embeddings with Ollama: {str(e)}")
        raise

def initialize_qdrant_collection():
    """Create a Qdrant collection if it doesn't exist."""
    try:
        collections = qdrant_client.get_collections()
        if collection_name not in [c.name for c in collections.collections]:
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)  # nomic-embed-text uses 768 dimensions
            )
            logger.info(f"Created Qdrant collection '{collection_name}'")
    except Exception as e:
        logger.error(f"Failed to initialize Qdrant collection: {str(e)}")
        raise

async def extract_and_save_text(file: UploadFile) -> dict:
    filename = file.filename or "unknown_file"
    logger.info(f"Starting text extraction and saving for '{filename}'")

    try:
        # Validate file type
        if not filename.lower().endswith(('.pdf', '.txt', '.docx')):
            raise HTTPException(status_code=400, detail="Only PDF, text, or DOCX files allowed")

        # Read file content
        content = await file.read()

        # Save the original file
        safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_')).rstrip()
        unique_filename = f"{int(datetime.now().timestamp())}_{safe_filename}"
        uploaded_file_path = os.path.join("uploaded_documents", "uploaded_files", unique_filename)
        os.makedirs(os.path.dirname(uploaded_file_path), exist_ok=True)
        try:
            with open(uploaded_file_path, 'wb') as f:
                f.write(content)
            logger.info(f"Saved uploaded file to: {uploaded_file_path}")
        except Exception as e:
            logger.error(f"Failed to save file '{filename}': {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

        # Extract text
        document_text = ""
        if filename.lower().endswith(".pdf"):
            temp_pdf_path = os.path.join("uploaded_documents", f"temp_{int(datetime.now().timestamp())}.pdf")
            try:
                with open(temp_pdf_path, 'wb') as temp_file:
                    temp_file.write(content)
                document_text = pymupdf4llm.to_markdown(temp_pdf_path)
            finally:
                if os.path.exists(temp_pdf_path):
                    os.remove(temp_pdf_path)
        elif filename.lower().endswith(".docx"):
            doc = Document(BytesIO(content))
            document_text = "\n".join([para.text for para in doc.paragraphs])
        else:  # .txt
            document_text = content.decode("utf-8")

        # Validate extracted text
        if not document_text.strip():
            raise HTTPException(status_code=400, detail="No valid text extracted from document")

        # Save extracted text
        text_filename = f"{safe_filename}.txt"
        text_file_path = os.path.join("uploaded_documents", "extracted_text", text_filename)
        os.makedirs(os.path.dirname(text_file_path), exist_ok=True)
        try:
            with open(text_file_path, 'w', encoding='utf-8') as f:
                f.write(document_text)
            logger.info(f"Saved extracted text to: {text_file_path}")
        except Exception as e:
            logger.error(f"Failed to save extracted text for '{filename}': {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save extracted text: {str(e)}")

        return {
            "original_filename": filename,
            "uploaded_file_path": uploaded_file_path,
            "text_file_path": text_file_path,
            "document_text": document_text,
            "chunks": [],
            "questions": [],
            "questions_file_path": "",
            "error_message": None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in extract_and_save_text for '{filename}': {e}", exc_info=True)
        return {
            "original_filename": filename,
            "uploaded_file_path": "",
            "text_file_path": "",
            "document_text": "",
            "chunks": [],
            "questions": [],
            "questions_file_path": "",
            "error_message": f"Failed to extract or save text for '{filename}': {str(e)}"
        }

def split_text(state: QuizGenerationState) -> QuizGenerationState:
    filename = state['original_filename']
    logger.info(f"Starting text splitting for '{filename}'")

    try:
        text = state.get("document_text", "")
        if not text:
            state["error_message"] = "No text available to split"
            return state

        # Split text into chunks (e.g., by paragraph or fixed length)
        chunks = text.split("\n\n")  # Example: split by paragraphs
        chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
        if not chunks:
            state["error_message"] = "No valid chunks generated from text"
            return state

        # Generate embeddings for chunks using Ollama
        embeddings = get_ollama_embeddings(chunks, model="nomic-embed-text")

        # Initialize Qdrant collection
        initialize_qdrant_collection()

        # Store chunks and embeddings in Qdrant
        points = [
            PointStruct(
                id=str(uuid.uuid4()),  # Unique ID for each chunk
                vector=embedding,
                payload={
                    "text": chunk,
                    "filename": state["original_filename"],
                    "chunk_index": idx
                }
            )
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ]
        qdrant_client.upsert(collection_name=collection_name, points=points)
        logger.info(f"Stored {len(points)} chunks in Qdrant for '{state['original_filename']}'")

        # Update state with chunk metadata
        state["chunks"] = chunks
        state["chunk_ids"] = [point.id for point in points]  # Store Qdrant point IDs
        state["error_message"] = None
        return state

    except Exception as e:
        logger.error(f"Error in split_text: {str(e)}", exc_info=True)
        state["error_message"] = f"Failed to split text or store in Qdrant: {str(e)}"
        return state