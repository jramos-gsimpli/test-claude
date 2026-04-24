from pathlib import Path
from typing import Literal, Optional

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from . import config

matplotlib.use("Agg")

ChartType = Literal["barras", "linea", "torta", "dispersion", "histograma"]


class ChartGenerationError(Exception):
    pass


class ChartGenerator:
    def __init__(self):
        config.CHARTS_OUTPUT_DIR.mkdir(exist_ok=True)

    def generate(
        self,
        df: pd.DataFrame,
        tipo: ChartType,
        columna_x: str,
        titulo: str,
        columna_y: Optional[str] = None,
        top_n: Optional[int] = None,
    ) -> str:
        self._validate_columns(df, columna_x, columna_y, tipo)

        data = self._prepare_data(df, columna_x, columna_y, top_n)
        fig, ax = plt.subplots(figsize=(10, 6))

        plotters = {
            "barras": self._plot_barras,
            "linea": self._plot_linea,
            "torta": self._plot_torta,
            "dispersion": self._plot_dispersion,
            "histograma": self._plot_histograma,
        }
        plotters[tipo](ax, data, columna_x, columna_y)

        ax.set_title(titulo, fontsize=14, fontweight="bold")
        plt.tight_layout()

        output_path = config.CHARTS_OUTPUT_DIR / f"{titulo.replace(' ', '_')}.png"
        fig.savefig(output_path, dpi=150)
        plt.close(fig)
        return str(output_path)

    def _validate_columns(self, df, col_x, col_y, tipo):
        if col_x not in df.columns:
            raise ChartGenerationError(f"Columna no encontrada: '{col_x}'")
        if col_y and col_y not in df.columns:
            raise ChartGenerationError(f"Columna no encontrada: '{col_y}'")
        if tipo in ("barras", "linea", "dispersion", "torta") and not col_y:
            if tipo != "histograma":
                raise ChartGenerationError(f"'{tipo}' requiere columna_y")

    def _prepare_data(self, df, col_x, col_y, top_n):
        data = df.copy()
        if top_n and col_y:
            data = data.nlargest(top_n, col_y)
        return data

    def _plot_barras(self, ax, data, col_x, col_y):
        ax.bar(data[col_x].astype(str), data[col_y], color="steelblue")
        ax.set_xlabel(col_x)
        ax.set_ylabel(col_y)
        plt.xticks(rotation=45, ha="right")

    def _plot_linea(self, ax, data, col_x, col_y):
        ax.plot(data[col_x], data[col_y], marker="o", color="steelblue")
        ax.set_xlabel(col_x)
        ax.set_ylabel(col_y)
        plt.xticks(rotation=45, ha="right")

    def _plot_torta(self, ax, data, col_x, col_y):
        ax.pie(data[col_y], labels=data[col_x].astype(str), autopct="%1.1f%%", startangle=90)

    def _plot_dispersion(self, ax, data, col_x, col_y):
        ax.scatter(data[col_x], data[col_y], alpha=0.6, color="steelblue")
        ax.set_xlabel(col_x)
        ax.set_ylabel(col_y)

    def _plot_histograma(self, ax, data, col_x, col_y):
        ax.hist(data[col_x].dropna(), bins=20, color="steelblue", edgecolor="white")
        ax.set_xlabel(col_x)
        ax.set_ylabel("Frecuencia")
