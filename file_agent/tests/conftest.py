import pandas as pd
import pytest

from src.file_reader import FileContent


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "producto": ["A", "B", "C", "D"],
        "ventas": [100, 250, 80, 320],
        "mes": ["Enero", "Enero", "Febrero", "Febrero"],
    })


@pytest.fixture
def csv_file_content(sample_df):
    return FileContent(
        filename="ventas.csv",
        file_type="csv",
        context_text="datos de ventas...",
        dataframe=sample_df,
    )


@pytest.fixture
def pdf_file_content():
    return FileContent(
        filename="informe.pdf",
        file_type="pdf",
        context_text="Informe Q1 2026\nResultados positivos...",
    )
