from pathlib import Path

from cfdi_pandas.reader import read_cfdi, read_cfdi_folder


def test_read_cfdi_single(tmp_path: Path, sample_cfdi_xml: str) -> None:
    xml_path = tmp_path / "invoice.xml"
    xml_path.write_text(sample_cfdi_xml, encoding="utf-8")

    data = read_cfdi(xml_path)

    assert set(data.keys()) == {"comprobantes", "conceptos", "impuestos"}
    assert len(data["comprobantes"]) == 1
    assert data["comprobantes"].iloc[0]["uuid"] == "123E4567-E89B-12D3-A456-426614174000"
    invoice_json = data.to_json()
    assert len(invoice_json) == 1
    assert len(invoice_json[0]["concepts"]) == 1
    assert len(invoice_json[0]["concepts"][0]["concept_taxes"]) == 1
    assert len(invoice_json[0]["taxes"]) >= 1


def test_read_cfdi_folder(tmp_path: Path, sample_cfdi_xml: str, sample_cfdi_xml_egreso: str) -> None:
    (tmp_path / "a.xml").write_text(sample_cfdi_xml, encoding="utf-8")
    (tmp_path / "b.xml").write_text(sample_cfdi_xml_egreso, encoding="utf-8")

    data = read_cfdi_folder(tmp_path)

    assert len(data["comprobantes"]) == 2
    assert data["conceptos"]["uuid"].nunique() == 2
    assert len(data.to_json()) == 2
