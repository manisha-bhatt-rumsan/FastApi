# from fastapi import  File, UploadFile, HTTPException,APIRouter
# import logging
# from quiz.schemas import UploadResponse
# from upload.service import extract_and_save_text, split_text


# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler('quiz_generator.log'),
#         logging.StreamHandler()
#     ]
# )
# logger = logging.getLogger(__name__)

# upload_routes = APIRouter()

# current_state = None

# @upload_routes.post("/upload_document", response_model=UploadResponse)
# async def upload_document(file: UploadFile = File(...)):
#     global current_state
#     filename = file.filename or "unknown_file"
#     logger.info(f"Uploading document: {filename}")

#     try:
#         # Step 1: Extract and save text
#         state = await extract_and_save_text(file)

#         # Step 2: Split text into chunks
#         state = split_text(state)

#         # Check for errors
#         if state.get('error_message'):
#             logger.error(f"Processing failed for '{filename}': {state['error_message']}")
#             raise HTTPException(status_code=400, detail=f"Failed to process '{filename}': {state['error_message']}")

#         # Update global state
#         current_state = state

#         return UploadResponse(
#             message="Document uploaded, text saved, and text split into chunks",
#             original_filename=state["original_filename"],
#             uploaded_file_path=state["uploaded_file_path"],
#             text_file_path=state["text_file_path"],
#             error_message=None
#         )

#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error in upload_document for '{filename}': {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail=f"Something went wrong: {str(e)}")