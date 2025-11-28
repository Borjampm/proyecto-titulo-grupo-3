import pytest

from fastapi import HTTPException

import app.routers.excel_upload as excel_router_module


class DummyUploadFile:
    def __init__(self, filename: str, content: bytes = b"data"):
        self.filename = filename
        self._content = content

    async def read(self):
        return self._content


class FakeUploaderSuccess:
    def __init__(self, session):
        self.session = session

    async def upload_beds_from_excel(self, path):
        return 5

    async def upload_patients_from_excel(self, path):
        return 3

    async def upload_gestion_estadia_from_excel(self, path):
        return 7


class FakeUploaderError(FakeUploaderSuccess):
    async def upload_beds_from_excel(self, path):
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_upload_beds_invalid_file_type():
    file = DummyUploadFile(filename="not_excel.txt")
    with pytest.raises(HTTPException) as ei:
        await excel_router_module.upload_beds(file, session=None)
    assert ei.value.status_code == 400


@pytest.mark.asyncio
async def test_upload_beds_success(monkeypatch):
    file = DummyUploadFile(filename="camas.xlsx", content=b"fake")

    # Monkeypatch ExcelUploader to avoid DB work
    monkeypatch.setattr(excel_router_module, "ExcelUploader", FakeUploaderSuccess)

    result = await excel_router_module.upload_beds(file, session=None)
    assert result["status"] == "success"
    assert result["beds_created"] == 5


@pytest.mark.asyncio
async def test_upload_beds_internal_error(monkeypatch):
    file = DummyUploadFile(filename="camas.xlsx", content=b"fake")
    monkeypatch.setattr(excel_router_module, "ExcelUploader", FakeUploaderError)

    with pytest.raises(HTTPException) as ei:
        await excel_router_module.upload_beds(file, session=None)
    assert ei.value.status_code == 500


@pytest.mark.asyncio
async def test_upload_patients_invalid_file_type():
    file = DummyUploadFile(filename="patients.csv")
    with pytest.raises(HTTPException) as ei:
        await excel_router_module.upload_patients(file, session=None)
    assert ei.value.status_code == 400


@pytest.mark.asyncio
async def test_upload_patients_success(monkeypatch):
    file = DummyUploadFile(filename="score.xlsx", content=b"fake")
    monkeypatch.setattr(excel_router_module, "ExcelUploader", FakeUploaderSuccess)

    result = await excel_router_module.upload_patients(file, session=None)
    assert result["status"] == "success"
    assert result["patients_processed"] == 3


@pytest.mark.asyncio
async def test_upload_gestion_estadia_accepts_xlsm(monkeypatch):
    file = DummyUploadFile(filename="gestion.xlsm", content=b"fake")
    monkeypatch.setattr(excel_router_module, "ExcelUploader", FakeUploaderSuccess)

    result = await excel_router_module.upload_gestion_estadia(file, session=None)
    assert result["status"] == "success"
    assert result["processed"] == 7


@pytest.mark.asyncio
async def test_upload_all_success(monkeypatch):
    beds_file = DummyUploadFile(filename="camas.xlsx", content=b"fake")
    patients_file = DummyUploadFile(filename="score.xlsx", content=b"fake")
    monkeypatch.setattr(excel_router_module, "ExcelUploader", FakeUploaderSuccess)

    result = await excel_router_module.upload_all(beds_file, patients_file, session=None)
    assert result["status"] == "success"
    assert result["beds_created"] == 5
    assert result["patients_processed"] == 3
