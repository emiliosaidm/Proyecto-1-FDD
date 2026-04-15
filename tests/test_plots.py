from pathlib import Path

import matplotlib
matplotlib.use("Agg")

from cfdi_pandas.plots import plot_by_cfdi_type, plot_income_expenses
from cfdi_pandas.reader import read_cfdi_folder


def _load_data(tmp_path: Path, xml_a: str, xml_b: str):
    (tmp_path / "a.xml").write_text(xml_a, encoding="utf-8")
    (tmp_path / "b.xml").write_text(xml_b, encoding="utf-8")
    return read_cfdi_folder(tmp_path)


def test_plot_income_expenses(tmp_path: Path, sample_cfdi_xml: str, sample_cfdi_xml_egreso: str) -> None:
    data = _load_data(tmp_path, sample_cfdi_xml, sample_cfdi_xml_egreso)
    fig = plot_income_expenses(data["comprobantes"])
    assert fig is not None
    axes = fig.get_axes()
    assert len(axes) == 1
    assert axes[0].get_title() == "Ingresos vs Egresos por Mes"


def test_plot_by_cfdi_type(tmp_path: Path, sample_cfdi_xml: str, sample_cfdi_xml_egreso: str) -> None:
    data = _load_data(tmp_path, sample_cfdi_xml, sample_cfdi_xml_egreso)
    fig = plot_by_cfdi_type(data["comprobantes"])
    assert fig is not None
    axes = fig.get_axes()
    assert len(axes) == 1
    assert axes[0].get_title() == "Distribución por Tipo de CFDI"
