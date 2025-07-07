from fastapi import HTTPException, UploadFile
from docx import Document
from io import BytesIO
import os
import logging
from datetime import datetime
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance

from app.config import settings
from langchain_community.embeddings import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader

logger = logging.getLogger(__name__)

QDRANT_HOST = settings.qdrant_host
QDRANT_PORT = settings.qdrant_port
OLLAMA_HOST = settings.ollama_host
COLLECTION_NAME = "quiz_chunks"

qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
embedder = OllamaEmbeddings(base_url=OLLAMA_HOST, model="nomic-embed-text")

def initialize_qdrant_collection():
    existing_collections = qdrant_client.get_collections()
    if COLLECTION_NAME not in [c.name for c in existing_collections.collections]:
        logger.info(f"Creating Qdrant collection: {COLLECTION_NAME}")
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE)
        )

def split_text_into_chunks(text: str, chunk_size=512, chunk_overlap=100) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    return splitter.split_text(text)

async def extract_chunks_with_metadata(file: UploadFile) -> tuple[str, list[str], list[dict]]:
    filename = file.filename or "unknown_file"
    if not filename.lower().endswith((".pdf", ".txt", ".docx")):
        raise HTTPException(status_code=400, detail="Only PDF, text, or DOCX files are allowed.")

    content = await file.read()

    safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_')).rstrip()
    unique_filename = f"{int(datetime.now().timestamp())}_{safe_filename}"
    uploaded_file_path = os.path.join("uploaded_documents", "uploaded_files", unique_filename)
    os.makedirs(os.path.dirname(uploaded_file_path), exist_ok=True)
    with open(uploaded_file_path, 'wb') as f:
        f.write(content)

    doc_id = str(uuid.uuid4())
    all_chunks = []
    chunk_metadata = []

    if filename.lower().endswith(".pdf"):
        temp_pdf_path = os.path.join("uploaded_documents", f"temp_{int(datetime.now().timestamp())}.pdf")
        with open(temp_pdf_path, 'wb') as temp_file:
            temp_file.write(content)
        try:
            loader = PyMuPDFLoader(temp_pdf_path)
            pages = loader.load_and_split()
            for page_idx, page in enumerate(pages, start=1):
                page_text = page.page_content.strip()
                if not page_text:
                    continue
                page_chunks = split_text_into_chunks(page_text)
                for chunk_idx, chunk in enumerate(page_chunks):
                    all_chunks.append(chunk)
                    chunk_metadata.append({
                        "doc_id": doc_id,
                        "filename": filename,
                        "page_number": page_idx,
                        "chunk_number": chunk_idx
                    })
        finally:
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)

    elif filename.lower().endswith(".docx"):
        doc = Document(BytesIO(content))
        full_text = "\n".join([para.text.strip() for para in doc.paragraphs if para.text.strip()])
        chunks = split_text_into_chunks(full_text)
        for chunk_idx, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            chunk_metadata.append({
                "doc_id": doc_id,
                "filename": filename,
                "page_number": 1,
                "chunk_number": chunk_idx
            })

    else:
        text = content.decode("utf-8")
        chunks = split_text_into_chunks(text)
        for chunk_idx, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            chunk_metadata.append({
                "doc_id": doc_id,
                "filename": filename,
                "page_number": 1,
                "chunk_number": chunk_idx
            })

    if not all_chunks:
        raise HTTPException(status_code=400, detail="No valid chunks extracted from the document.")

    logger.info(f"Extracted {len(all_chunks)} chunks from '{filename}' with per-page splitting")
    logger.info(f"Returning {len(all_chunks)} chunks with metadata keys: {chunk_metadata[0].keys()} and doc_id: {doc_id}")
    return all_chunks, chunk_metadata, doc_id, uploaded_file_path
    

def store_chunks_in_qdrant(chunks: list[str], metadata: list[dict]):
    logger.info(f"Generating embeddings for {len(chunks)} chunks")
    logger.info(f"Metadata sample: {metadata[:2]}") 
    embeddings = embedder.embed_documents(chunks)
    initialize_qdrant_collection()

    points = []
    for chunk, embedding, meta in zip(chunks, embeddings, metadata):
        if not isinstance(meta, dict):
            logger.error(f"Invalid metadata format: {meta} (type={type(meta)})")
            continue  
    
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={**meta, "text": chunk}
        )
        points.append(point)

    logger.info(f"Uploading {len(points)} points to Qdrant collection '{COLLECTION_NAME}'")
    qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)
    logger.info("Chunks successfully stored in Qdrant.")
