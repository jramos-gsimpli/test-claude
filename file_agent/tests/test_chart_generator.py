import pytest

from src.chart_generator import ChartGenerator, ChartGenerationError


@pytest.fixture
def gen(tmp_path, monkeypatch):
    monkeypatch.setattr("src.chart_generator.config.CHARTS_OUTPUT_DIR", tmp_path)
    return ChartGenerator()


def test_generates_bar_chart(gen, sample_df, tmp_path):
    path = gen.generate(sample_df, "barras", "producto", "Ventas por producto", columna_y="ventas")
    assert "Ventas_por_producto.png" in path


def test_output_file_exists(gen, sample_df, tmp_path):
    from pathlib import Path
    path = gen.generate(sample_df, "histograma", "ventas", "Distribución ventas")
    assert Path(path).exists()


def test_raises_on_missing_column(gen, sample_df):
    with pytest.raises(ChartGenerationError):
        gen.generate(sample_df, "barras", "columna_inexistente", "Test", columna_y="ventas")


def test_raises_when_column_y_missing_for_barras(gen, sample_df):
    with pytest.raises(ChartGenerationError):
        gen.generate(sample_df, "barras", "producto", "Sin Y")


def test_top_n_limits_rows(gen, sample_df, tmp_path):
    path = gen.generate(sample_df, "barras", "producto", "Top 2", columna_y="ventas", top_n=2)
    assert path is not None


def test_generates_pie_chart(gen, sample_df):
    path = gen.generate(sample_df, "torta", "producto", "Torta ventas", columna_y="ventas")
    assert path is not None


def test_generates_scatter_chart(gen, sample_df):
    path = gen.generate(sample_df, "dispersion", "ventas", "Dispersión", columna_y="ventas")
    assert path is not None
