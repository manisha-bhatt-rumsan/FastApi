from fastapi import HTTPException, UploadFile
from docx import Document
from io import BytesIO
import pymupdf4llm
import os
import logging
from datetime import datetime
from upload.schemas import QuizGenerationState
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


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
        # Check if document_text is available
        if not state['document_text']:
            raise ValueError("No document text available to split")

        # Split text into chunks
        splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=100)
        chunks = splitter.split_text(state['document_text'])
        logger.info(f"Split text into {len(chunks)} chunks")

        # Update state
        state['chunks'] = chunks
        state['error_message'] = None

    except Exception as e:
        logger.error(f"Error in split_text for '{filename}': {e}", exc_info=True)
        state['error_message'] = f"Failed to split text for '{filename}': {str(e)}"
        state['chunks'] = []

    return state