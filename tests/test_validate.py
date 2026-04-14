from pathlib import Path

from cfdi_pandas.reader import read_cfdi_folder
from cfdi_pandas.validate import (
    check_date_range,
    check_duplicate_uuid,
    check_tax_math,
    validate_all,
)


def test_validate_duplicate_uuid(tmp_path: Path, sample_cfdi_xml: str) -> None:
    (tmp_path / "a.xml").write_text(sample_cfdi_xml, encoding="utf-8")
    (tmp_path / "b.xml").write_text(sample_cfdi_xml, encoding="utf-8")
    data = read_cfdi_folder(tmp_path)

    duplicates = check_duplicate_uuid(data["comprobantes"])
    assert len(duplicates) == 1
    assert int(duplicates.iloc[0]["count"]) == 2


def test_validate_tax_math_and_date_range(
    tmp_path: Path, sample_cfdi_xml: str, sample_cfdi_xml_egreso: str
) -> None:
    (tmp_path / "a.xml").write_text(sample_cfdi_xml, encoding="utf-8")
    (tmp_path / "b.xml").write_text(sample_cfdi_xml_egreso, encoding="utf-8")
    data = read_cfdi_folder(tmp_path)

    tax_issues = check_tax_math(data["comprobantes"], data["conceptos"])
    out_of_range = check_date_range(data["comprobantes"], "2024-01-01", "2024-01-31")
    full = validate_all(data["comprobantes"], data["conceptos"], "2024-01-01", "2024-01-31")

    assert tax_issues.empty
    assert len(out_of_range) == 1
    assert set(full.keys()) == {"duplicate_uuid", "tax_math", "date_range"}
