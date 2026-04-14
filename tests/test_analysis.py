from pathlib import Path

from cfdi_pandas.analysis import (
    calculate_taxes,
    detect_cancelled,
    group_by_month,
    group_by_regimen,
    group_by_rfc,
    monthly_summary,
    top_n,
)
from cfdi_pandas.reader import read_cfdi_folder


def _load_data(tmp_path: Path, xml_a: str, xml_b: str):
    (tmp_path / "a.xml").write_text(xml_a, encoding="utf-8")
    (tmp_path / "b.xml").write_text(xml_b, encoding="utf-8")
    return read_cfdi_folder(tmp_path)


def test_analysis_functions(tmp_path: Path, sample_cfdi_xml: str, sample_cfdi_xml_egreso: str) -> None:
    data = _load_data(tmp_path, sample_cfdi_xml, sample_cfdi_xml_egreso)
    comprobantes = data["comprobantes"]
    conceptos = data["conceptos"]
    impuestos = data["impuestos"]

    assert not group_by_rfc(comprobantes, by="emisor").empty
    assert not group_by_month(comprobantes).empty
    assert not group_by_regimen(comprobantes).empty
    assert not calculate_taxes(impuestos).empty
    assert not calculate_taxes(conceptos).empty
    assert not monthly_summary(comprobantes).empty
    assert len(top_n(comprobantes, by="receptor", n=1)) == 1
    assert len(detect_cancelled(comprobantes)) == 0
