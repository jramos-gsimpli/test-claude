from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pandas as pd
import pytest

from src.file_reader import FileReader, UnsupportedFileError


@pytest.fixture
def reader():
    return FileReader()


def test_raises_on_unsupported_extension(reader, tmp_path):
    bad_file = tmp_path / "data.txt"
    bad_file.write_text("contenido")
    with pytest.raises(UnsupportedFileError):
        reader.read(str(bad_file))


def test_reads_csv_returns_dataframe(reader, tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("nombre,edad\nJuan,30\nPedro,25")
    content = reader.read(str(csv_file))
    assert content.file_type == "csv"
    assert content.dataframe is not None
    assert list(content.dataframe.columns) == ["nombre", "edad"]


def test_reads_csv_context_includes_stats(reader, tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("nombre,ventas\nA,100\nB,200")
    content = reader.read(str(csv_file))
    assert "Filas totales: 2" in content.context_text
    assert "ventas" in content.context_text


def test_reads_pdf_returns_no_dataframe(reader, tmp_path):
    with patch("src.file_reader.pdfplumber.open") as mock_pdf:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Texto del PDF"
        mock_pdf.return_value.__enter__.return_value.pages = [mock_page]

        pdf_file = tmp_path / "doc.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")
        content = reader.read(str(pdf_file))

    assert content.file_type == "pdf"
    assert content.dataframe is None
    assert "Texto del PDF" in content.context_text


def test_context_includes_sample_rows(reader, tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("col\n" + "\n".join(str(i) for i in range(150)))
    content = reader.read(str(csv_file))
    assert "filas adicionales no mostradas" in content.context_text
