"""
Excel upload endpoints for importing bed and patient data.
"""

import tempfile
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_session
from app.excel_uploader import ExcelUploader


router = APIRouter(prefix="/excel", tags=["excel-upload"])


@router.post("/upload-beds")
async def upload_beds(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """
    Upload bed data from "Camas NWP1" Excel file.
    
    Expected file: Excel file with "Camas" sheet containing bed information.
    
    Returns:
        Dictionary with upload statistics (beds_created, status, message)
    """
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload an Excel file (.xlsx or .xls)"
        )
    
    # Save uploaded file temporarily
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Upload beds using the ExcelUploader
        uploader = ExcelUploader(session)
        beds_created = await uploader.upload_beds_from_excel(tmp_file_path)
        
        return {
            "status": "success",
            "message": f"Successfully uploaded {beds_created} beds",
            "beds_created": beds_created,
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading beds: {str(e)}"
        )
    
    finally:
        # Clean up temporary file
        Path(tmp_file_path).unlink(missing_ok=True)


@router.post("/upload-patients")
async def upload_patients(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """
    Upload patient and clinical episode data from "Score Social" Excel file.
    
    Expected file: Excel file with "Data Casos" sheet containing patient information.
    
    Returns:
        Dictionary with upload statistics (patients_processed, status, message)
    """
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload an Excel file (.xlsx or .xls)"
        )
    
    # Save uploaded file temporarily
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Upload patients using the ExcelUploader
        uploader = ExcelUploader(session)
        patients_processed = await uploader.upload_patients_from_excel(tmp_file_path)
        
        return {
            "status": "success",
            "message": f"Successfully processed {patients_processed} patient records",
            "patients_processed": patients_processed,
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading patients: {str(e)}"
        )
    
    finally:
        # Clean up temporary file
        Path(tmp_file_path).unlink(missing_ok=True)
        
       

@router.post("/upload-gestion-estadia")
async def upload_gestion_estadia(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """
    Upload patient and episode data from Gestion Estadía Excel file (UCCC sheet).

    Returns:
        Dictionary with counts of processed rows
    """
    if not file.filename.endswith(('.xlsx', '.xls', '.xlsm')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload an Excel file (.xlsx, .xls, .xlsm)"
        )

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        uploader = ExcelUploader(session)
        processed = await uploader.upload_gestion_estadia_from_excel(tmp_file_path)

        return {
            "status": "success",
            "message": f"Successfully processed {processed} UCCC rows",
            "processed": processed,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading Gestion Estadía: {str(e)}"
        )

    finally:
        Path(tmp_file_path).unlink(missing_ok=True)


@router.post("/upload-social-scores")
async def upload_social_scores(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """
    Upload social score data from "Score Social" Excel file.
    
    Expected file: Excel file with "Data Casos" sheet containing:
    - Episodio / Estadía: Episode identifier to match
    - Puntaje: The social score (can be null)
    - Fecha Asignación: Recorded date (used as recorded_at)
    - Encuestadora: Person who recorded (used as recorded_by)
    - Motivo: Reason if score is null
    
    Returns:
        Dictionary with upload statistics (scores_processed, status, message)
    """
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload an Excel file (.xlsx or .xls)"
        )
    
    # Save uploaded file temporarily
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Upload social scores using the ExcelUploader
        uploader = ExcelUploader(session)
        result = await uploader.upload_social_scores_from_excel(tmp_file_path)
        
        return {
            "status": "success",
            "message": f"Successfully processed {result['count']} social score records",
            "scores_processed": result['count'],
            "missing_count": result['missing_count'],
            "missing_ids": result['missing_ids'],
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading social scores: {str(e)}"
        )
    
    finally:
        # Clean up temporary file
        Path(tmp_file_path).unlink(missing_ok=True)

@router.post("/upload-grd")
async def upload_grd(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """
    Upload GRD (expected stay days) data from Excel file.
    
    Expected file: Excel file with "egresos 2024-2025" sheet containing:
    - Episodio CMBD: Episode identifier to match
    - Estancia Norma GRD: Expected stay days from GRD norm
    
    Returns:
        Dictionary with upload statistics (episodes_updated, status, message)
    """
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls', '.xlsm')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload an Excel file (.xlsx, .xls, .xlsm)"
        )
    
    # Save uploaded file temporarily
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Upload GRD data using the ExcelUploader
        uploader = ExcelUploader(session)
        result = await uploader.upload_grd_from_excel(tmp_file_path)
        
        response = {
            "status": "success",
            "message": f"Successfully updated {result['count']} episodes with GRD data",
            "episodes_updated": result['count'],
            "missing_count": result['missing_count'],
            "missing_ids": result['missing_ids'],
        }
        
        # Add debug info if available
        if 'sample_db_ids' in result:
            response['debug_sample_db_ids'] = result['sample_db_ids']
        if 'sample_file_ids' in result:
            response['debug_sample_file_ids'] = result['sample_file_ids']
        
        return response
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading GRD data: {str(e)}"
        )
    
    finally:
        # Clean up temporary file
        Path(tmp_file_path).unlink(missing_ok=True)


@router.post("/upload-all")
async def upload_all(
    beds_file: UploadFile = File(..., description="Camas NWP1 Excel file"),
    patients_file: UploadFile = File(..., description="Score Social Excel file"),
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """
    Upload both bed and patient data from two Excel files.
    
    Args:
        beds_file: Excel file with "Camas" sheet for bed data
        patients_file: Excel file with "Data Casos" sheet for patient data
    
    Returns:
        Dictionary with complete upload statistics
    """
    beds_tmp_path = None
    patients_tmp_path = None
    
    try:
        # Validate file types
        if not beds_file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Invalid beds file type. Please upload an Excel file (.xlsx or .xls)"
            )
        
        if not patients_file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Invalid patients file type. Please upload an Excel file (.xlsx or .xls)"
            )
        
        # Save beds file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            content = await beds_file.read()
            tmp_file.write(content)
            beds_tmp_path = tmp_file.name
        
        # Save patients file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            content = await patients_file.read()
            tmp_file.write(content)
            patients_tmp_path = tmp_file.name
        
        # Upload data using the ExcelUploader
        uploader = ExcelUploader(session)
        
        # Upload beds first
        beds_created = await uploader.upload_beds_from_excel(beds_tmp_path)
        
        # Then upload patients
        patients_processed = await uploader.upload_patients_from_excel(patients_tmp_path)
        
        return {
            "status": "success",
            "message": "Successfully uploaded all data",
            "beds_created": beds_created,
            "patients_processed": patients_processed,
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading data: {str(e)}"
        )
    
    finally:
        # Clean up temporary files
        if beds_tmp_path:
            Path(beds_tmp_path).unlink(missing_ok=True)
        if patients_tmp_path:
            Path(patients_tmp_path).unlink(missing_ok=True)
