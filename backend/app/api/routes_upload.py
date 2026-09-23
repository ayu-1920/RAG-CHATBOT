from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from app.services.ingestion import process_and_store_pdf
import uuid

router = APIRouter()

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...)
):
    document_id = str(uuid.uuid4())
    
    # Push the heavy lifting to a background task
    background_tasks.add_task(process_and_store_pdf, file, document_id)
    
    return {
        "status": "processing", 
        "document_id": document_id, 
        "message": "Document is being ingested in the background."
    }
