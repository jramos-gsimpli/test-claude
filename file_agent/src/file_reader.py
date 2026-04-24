from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd
import pdfplumber

from . import config


class UnsupportedFileError(Exception):
    pass


@dataclass
class FileContent:
    filename: str
    file_type: str
    context_text: str
    dataframe: Optional[pd.DataFrame] = field(default=None, repr=False)


class FileReader:
    def read(self, path: str) -> FileContent:
        p = Path(path)
        suffix = p.suffix.lower()

        if suffix not in config.SUPPORTED_EXTENSIONS:
            raise UnsupportedFileError(f"Formato no soportado: {suffix}. Usá PDF, CSV o Excel.")

        if suffix == ".pdf":
            return self._read_pdf(p)
        return self._read_tabular(p, suffix)

    def _read_pdf(self, path: Path) -> FileContent:
        with pdfplumber.open(path) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        return FileContent(
            filename=path.name,
            file_type="pdf",
            context_text=f"Archivo: {path.name}\nPáginas: {len(pages)}\n\n" + "\n\n".join(pages),
        )

    def _read_tabular(self, path: Path, suffix: str) -> FileContent:
        df = pd.read_csv(path) if suffix == ".csv" else pd.read_excel(path)
        file_type = "csv" if suffix == ".csv" else "excel"
        return FileContent(
            filename=path.name,
            file_type=file_type,
            context_text=_dataframe_to_context(df, path.name),
            dataframe=df,
        )


def _dataframe_to_context(df: pd.DataFrame, filename: str) -> str:
    sample = df.head(config.MAX_ROWS_IN_CONTEXT)
    remaining = len(df) - len(sample)

    sections = [
        f"Archivo: {filename}",
        f"Filas totales: {len(df)} | Columnas: {len(df.columns)}",
        "\nColumnas y tipos de dato:",
        *[f"  - {col}: {df[col].dtype}" for col in df.columns],
        "\nEstadísticas generales:",
        df.describe(include="all").to_string(),
        f"\nPrimeras {len(sample)} filas:",
        sample.to_string(index=False),
    ]

    if remaining > 0:
        sections.append(f"\n[... {remaining} filas adicionales no mostradas ...]")

    return "\n".join(sections)
