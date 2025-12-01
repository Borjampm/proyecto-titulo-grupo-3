"""
Document upload endpoints for patient documents.
"""

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.deps import get_session
from app.models.patient_document import PatientDocument
from app.models.patient_document import DocumentType as ModelDocumentType
from app.schemas.patient_document import PatientDocumentResponse, DocumentType


router = APIRouter(prefix="/documents", tags=["documents"])

# Directory for storing uploaded documents
UPLOAD_DIR = Path("uploads/documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.gif', '.xlsx', '.xls', '.txt'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def get_document_type_from_extension(filename: str) -> ModelDocumentType:
    """Determine document type based on file extension."""
    ext = Path(filename).suffix.lower()
    
    if ext in {'.pdf', '.doc', '.docx', '.txt'}:
        return ModelDocumentType.MEDICAL_REPORT
    elif ext in {'.jpg', '.jpeg', '.png', '.gif'}:
        return ModelDocumentType.IMAGING
    elif ext in {'.xlsx', '.xls'}:
        return ModelDocumentType.LAB_RESULT
    else:
        return ModelDocumentType.OTHER


def transform_to_response(doc: PatientDocument, uploaded_by: str = "Sistema") -> PatientDocumentResponse:
    """Transform a PatientDocument model to the frontend response format."""
    return PatientDocumentResponse(
        id=str(doc.id),
        patientId=str(doc.patient_id),
        name=doc.file_url.split('/')[-1] if '/' in doc.file_url else doc.file_url,
        type=doc.document_type.value,
        uploadedBy=uploaded_by,
        uploadedAt=doc.created_at.isoformat() if doc.created_at else datetime.now(timezone.utc).isoformat(),
        url=f"/documents/{doc.id}/download"
    )


@router.get("/patient/{patient_id}", response_model=List[PatientDocumentResponse])
async def get_patient_documents(
    patient_id: str,
    session: AsyncSession = Depends(get_session)
) -> List[PatientDocumentResponse]:
    """
    Get all documents for a patient.
    
    Args:
        patient_id: UUID of the patient
        
    Returns:
        List of documents for the patient
    """
    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid patient ID format")
    
    result = await session.execute(
        select(PatientDocument)
        .where(PatientDocument.patient_id == patient_uuid)
        .order_by(PatientDocument.created_at.desc())
    )
    documents = result.scalars().all()
    
    return [transform_to_response(doc) for doc in documents]


@router.post("/patient/{patient_id}", response_model=PatientDocumentResponse)
async def upload_document(
    patient_id: str,
    file: UploadFile = File(...),
    uploaded_by: str = Form(default="Sistema"),
    session: AsyncSession = Depends(get_session)
) -> PatientDocumentResponse:
    """
    Upload a document for a patient.
    
    Args:
        patient_id: UUID of the patient
        file: The file to upload
        uploaded_by: Name of the person uploading the document
        
    Returns:
        The created document metadata
    """
    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid patient ID format")
    
    # Validate file extension
    if file.filename:
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
    
    # Read file content
    content = await file.read()
    
    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Generate unique filename
    file_ext = Path(file.filename or "document").suffix
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    try:
        # Save file to disk
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Determine document type
        doc_type = get_document_type_from_extension(file.filename or "")
        
        # Create database record
        document = PatientDocument(
            patient_id=patient_uuid,
            document_type=doc_type,
            file_url=str(file_path),
        )
        
        session.add(document)
        await session.flush()
        await session.refresh(document)
        
        # Return response with original filename
        response = transform_to_response(document, uploaded_by)
        response.name = file.filename or unique_filename
        
        return response
        
    except Exception as e:
        # Clean up file if database operation fails
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading document: {str(e)}"
        )


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    session: AsyncSession = Depends(get_session)
) -> FileResponse:
    """
    Download a document by its ID.
    
    Args:
        document_id: UUID of the document
        
    Returns:
        The file as a download response
    """
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")
    
    result = await session.execute(
        select(PatientDocument).where(PatientDocument.id == doc_uuid)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    file_path = Path(document.file_url)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document file not found")
    
    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/octet-stream"
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """
    Delete a document by its ID.
    
    Args:
        document_id: UUID of the document
        
    Returns:
        Confirmation message
    """
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")
    
    result = await session.execute(
        select(PatientDocument).where(PatientDocument.id == doc_uuid)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file from disk
    file_path = Path(document.file_url)
    if file_path.exists():
        file_path.unlink()
    
    # Delete from database
    await session.delete(document)
    await session.flush()
    
    return {
        "status": "success",
        "message": "Document deleted successfully"
    }

