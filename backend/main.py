
import os
import re
import uuid
from pathlib import Path
from typing import Optional

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    Request
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from document_processor import process_pdf, collection
from rag import rag_pipeline


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

MAX_FILE_SIZE = 10 * 1024 * 1024

DOCUMENTS_DIR = "documents"

os.makedirs(DOCUMENTS_DIR, exist_ok=True)

# Read allowed frontend URLs from environment variables.
FRONTEND_ORIGINS = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173"
)

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in FRONTEND_ORIGINS.split(",")
    if origin.strip()
]


# --------------------------------------------------
# RATE LIMITER
# --------------------------------------------------

limiter = Limiter(key_func=get_remote_address)


# --------------------------------------------------
# FASTAPI APPLICATION
# --------------------------------------------------

app = FastAPI(
    title="Document Q&A Assistant",
    description="Multi-document PDF Q&A using RAG and Gemini."
)

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"]
)


# --------------------------------------------------
# REQUEST VALIDATION
# --------------------------------------------------

class QuestionRequest(BaseModel):

    question: str = Field(
        ...,
        min_length=1,
        max_length=1000
    )

    filename: Optional[str] = Field(
        default=None,
        max_length=255
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, value):

        value = value.strip()

        if not value:
            raise ValueError("Question cannot be empty.")

        return value

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, value):

        if value is not None:
            if Path(value).name != value:
                raise ValueError("Invalid filename.")

        return value


# --------------------------------------------------
# ROOT ENDPOINT
# --------------------------------------------------

@app.get("/")
async def root():

    return {
        "message": "Document Q&A Assistant API is running"
    }


# --------------------------------------------------
# HEALTH CHECK ENDPOINT
# --------------------------------------------------

@app.get("/health")
async def health_check():

    try:

        document_count = collection.count()

        return {
            "status": "healthy",
            "api": "running",
            "database": "connected",
            "stored_chunks": document_count
        }

    except Exception as e:

        print(f"Health check failed: {e}")

        raise HTTPException(
            status_code=503,
            detail="Application health check failed."
        )


# --------------------------------------------------
# PDF UPLOAD
# --------------------------------------------------

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    original_filename = Path(file.filename or "").name

    if not original_filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    safe_filename = re.sub(
        r"[^A-Za-z0-9._-]",
        "_",
        original_filename
    )

    stored_filename = (
        f"{uuid.uuid4().hex}_{safe_filename}"
    )

    file_path = os.path.join(
        DOCUMENTS_DIR,
        stored_filename
    )

    total_size = 0
    first_chunk = True

    try:

        with open(file_path, "wb") as buffer:

            while True:

                chunk = await file.read(1024 * 1024)

                if not chunk:
                    break

                if first_chunk:

                    first_chunk = False

                    if not chunk.startswith(b"%PDF-"):
                        raise HTTPException(
                            status_code=400,
                            detail="Invalid PDF file."
                        )

                total_size += len(chunk)

                if total_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="PDF exceeds the 10 MB upload limit."
                    )

                buffer.write(chunk)

        if total_size == 0:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty."
            )

        result = process_pdf(file_path)

        return {
            "message": "PDF uploaded and processed successfully",
            "filename": result["filename"],
            "pages_processed": result["pages_processed"],
            "chunks_stored": result["chunks_stored"]
        }

    except HTTPException:

        if os.path.exists(file_path):
            os.remove(file_path)

        raise

    except Exception as e:

        print(f"PDF processing error: {e}")

        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=500,
            detail="PDF processing failed. Check backend logs."
        )

    finally:
        await file.close()


# --------------------------------------------------
# QUESTION ANSWERING
# --------------------------------------------------

@app.post("/ask")
@limiter.limit("10/minute")
async def ask_question(
    request: Request,
    request_body: QuestionRequest
):

    try:

        result = rag_pipeline(
            request_body.question,
            filename=request_body.filename
        )

        return {
            "question": request_body.question,
            "filename": request_body.filename,
            "answer": result["answer"],
            "sources": result["sources"]
        }

    except Exception as e:

        print(f"RAG processing error: {e}")

        raise HTTPException(
            status_code=500,
            detail="Failed to process your question. Please try again."
        )


# --------------------------------------------------
# LIST DOCUMENTS
# --------------------------------------------------

@app.get("/documents")
async def list_documents():

    try:

        results = collection.get(
            include=["metadatas"]
        )

        documents = {}

        for metadata in results["metadatas"]:

            filename = metadata["source"]

            if filename not in documents:

                documents[filename] = {
                    "filename": filename,
                    "chunks": 0
                }

            documents[filename]["chunks"] += 1

        return {
            "total_documents": len(documents),
            "documents": list(documents.values())
        }

    except Exception as e:

        print(f"Document listing error: {e}")

        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve uploaded documents."
        )
