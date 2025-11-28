import re
from datetime import date, datetime

import pandas as pd
import pytest

from app.excel_uploader import (
    calculate_rut_verifier,
    generate_rut,
    get_name,
    ExcelUploader,
)
from app.excel_uploader import (
    EpisodeInfoType,
    EpisodeStatus,
)


def test_calculate_rut_verifier_known_example():
    # Known example: 12.345.678-5 => number 12345678 => verifier '5'
    assert calculate_rut_verifier(12345678) == "5"


def test_generate_rut_and_verifier_consistency():
    seed = "episode-123"
    rut = generate_rut(seed)

    # Basic format check: contains dash and digits/dots before it
    assert isinstance(rut, str)
    assert re.match(r"^[0-9.]+-[0-9K]$", rut)

    # Extract numeric part and compute verifier with calculate_rut_verifier
    num_part = rut.split("-")[0].replace(".", "")
    computed_verifier = calculate_rut_verifier(int(num_part))
    assert rut.endswith(computed_verifier)


def test_get_name_deterministic():
    seed = "episode-xyz"
    first1, last1 = get_name(seed)
    first2, last2 = get_name(seed)
    assert (first1, last1) == (first2, last2)
    assert isinstance(first1, str) and isinstance(last1, str)


def test_parse_bed_row_basic():
    uploader = ExcelUploader(db_session=None)
    # Create a pandas Series with CAMA and CAMA_BLOQUEADA
    row = pd.Series({"CAMA": "201A", "CAMA_BLOQUEADA": "NO", "HABITACION": None})
    parsed = uploader._parse_bed_row(row)
    assert parsed is not None
    assert parsed["room"] == "201A"
    assert parsed["available"] is True
    assert parsed["active"] is True


def test_parse_bed_row_blocked_variants():
    uploader = ExcelUploader(db_session=None)

    for blocked_val in ["SI", "S", "YES", "Y", "TRUE", "1"]:
        row = pd.Series({"CAMA": "300B", "CAMA_BLOQUEADA": blocked_val})
        parsed = uploader._parse_bed_row(row)
        # Blocked values should mark available=False
        assert parsed is not None
        assert parsed["room"] == "300B"
        assert parsed["available"] is False


def test_parse_patient_data_birthdate_and_generated_name():
    uploader = ExcelUploader(db_session=None)

    # Birth date as string
    row = pd.Series({"Episodio / Estadía": "EPI-007", "RUT": None, "Nombre": None, "Fecha de nacimiento": "1985-04-12"})
    parsed = uploader._parse_patient_data(row)
    assert parsed is not None
    assert isinstance(parsed["birth_date"], date)

    # Nombre with single name
    row2 = pd.Series({"Episodio / Estadía": "EPI-008", "RUT": None, "Nombre": "Mononym", "Fecha de nacimiento": None})
    parsed2 = uploader._parse_patient_data(row2)
    assert parsed2 is not None
    assert parsed2["first_name"] == "Mononym"
    assert parsed2["last_name"] == ""


def test_parse_patient_data_generated_and_real():
    uploader = ExcelUploader(db_session=None)

    # Case 1: anonymous/missing RUT and Nombre -> generate
    row1 = pd.Series({"Episodio / Estadía": "EPI-001", "RUT": None, "Nombre": None, "Fecha de nacimiento": None})
    parsed1 = uploader._parse_patient_data(row1)
    assert parsed1 is not None
    assert "medical_identifier" in parsed1
    assert parsed1["first_name"] and parsed1["last_name"] is not None

    # Case 2: real RUT and Nombre provided
    row2 = pd.Series({"Episodio / Estadía": "EPI-002", "RUT": "12.345.678-5", "Nombre": "Ana María", "Fecha de nacimiento": date(1980, 5, 2)})
    parsed2 = uploader._parse_patient_data(row2)
    assert parsed2 is not None
    assert parsed2["medical_identifier"] == "12.345.678-5"
    assert parsed2["first_name"] == "Ana"
    assert parsed2["last_name"] == "María"


def test_parse_patient_information_handles_types_and_missing():
    uploader = ExcelUploader(db_session=None)
    ts = pd.Timestamp("2025-09-24T12:35:00")
    row = pd.Series({
        "RUT": "",
        "Nombre": "",
        "SomeNumber": 3.0,
        "SomeInt": 7,
        "SomeDate": ts,
        "Empty": float('nan'),
    })

    info = uploader._parse_patient_information(row)
    # Expect keys for provided columns except excluded ones
    assert "SomeNumber" in info and isinstance(info["SomeNumber"], float)
    assert "SomeInt" in info and isinstance(info["SomeInt"], int)
    assert "SomeDate" in info and isinstance(info["SomeDate"], str)
    assert "Empty" in info and info["Empty"] is None


def test_parse_clinical_episode_data_discharge_timestamp_and_unknown():
    uploader = ExcelUploader(db_session=None)

    # discharge as pandas Timestamp
    row = pd.Series({
        "Episodio / Estadía": "EPI-11",
        "Fe.admisión": pd.Timestamp("2025-09-20"),
        "Fecha del alta": pd.Timestamp("2025-09-25"),
        "Estado de alta": None,
    })

    episode = uploader._parse_clinical_episode_data(row)
    assert episode["expected_discharge"] == date(2025, 9, 25)
    # When status missing but discharge exists -> DISCHARGED
    assert episode["status"] == EpisodeStatus.DISCHARGED


def test_parse_clinical_episode_information_puntaje_and_valor_parcial():
    uploader = ExcelUploader(db_session=None)
    row = pd.Series({
        "Encuesta": None,
        "Motivo": None,
        "Puntaje": "15",
        " Encuestadora": None,
        " Valor Parcial ": "200.5",
    })

    records = uploader._parse_clinical_episode_information(row)
    # find puntaje and valor_parcial records
    found_puntaje = any(r["title"] == "Información de Encuesta" and r["value"].get("puntaje") == 15.0 for r in records)
    found_valor = any(r["title"] == "Valor Parcial" and (r["value"].get("valor_parcial") == 200.5) for r in records)
    assert found_puntaje
    assert found_valor


def test_parse_clinical_episode_data_and_status_mapping():
    uploader = ExcelUploader(db_session=None)

    # When discharge string present and status contains 'Alta' => DISCHARGED
    row = pd.Series({
        "Episodio / Estadía": "EPI-10",
        "Fe.admisión": pd.Timestamp("2025-09-20"),
        "Fecha del alta": "24-09-2025",
        "Estado de alta": "Alta",
        "Cama": "201A",
    })

    episode = uploader._parse_clinical_episode_data(row)
    assert isinstance(episode["admission_at"], datetime)
    assert episode["expected_discharge"] == date(2025, 9, 24)
    assert episode["status"] == EpisodeStatus.DISCHARGED
    assert episode["bed_room"] == "201A"


def test_parse_clinical_episode_information_collects_records():
    uploader = ExcelUploader(db_session=None)
    row = pd.Series({
        "Texto libre diagnóstico admisión": "Neumonía",
        "Servicio": "UCI",
        "Centro Atención": "Hospital Central",
        "Clasificación Marca 1": "A",
        "Desc. Convenio": "ConvenioX",
        "Encuesta": "S1",
        "Puntaje": 12,
        " Valor Parcial ": 123.45,
        "DÍAS PACIENTES ACOSTADOS": 5,
        "ExtraCol": "ExtraValue",
    })

    records = uploader._parse_clinical_episode_information(row)
    # Expect at least diagnosis, servicio, centro, classifications, coverage, survey, valor, dias, and extra
    titles = [r["title"] for r in records]
    assert any("Diagnóstico" in t for t in titles)
    assert any("Servicio" in t for t in titles)
    assert any("Centro" in t for t in titles)
    assert any("Clasificaciones" in t for t in titles)
    assert any("Información de Cobertura" in t for t in titles)
    assert any("Información de Encuesta" in t for t in titles)
    assert any("Valor Parcial" in t for t in titles)
    assert any("Días de Hospitalización" in t for t in titles)
    assert any("ExtraCol" in t for t in titles)
