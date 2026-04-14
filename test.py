from pathlib import Path

from cfdi_pandas import (
    calculate_taxes,
    check_date_range,
    check_duplicate_uuid,
    check_tax_math,
    detect_cancelled,
    group_by_month,
    group_by_regimen,
    group_by_rfc,
    monthly_summary,
    read_cfdi,
    read_cfdi_folder,
    top_n,
    validate_all,
)


folder = Path(__file__).resolve().parent / "cfdi_tests"
if not folder.exists():
    folder = Path(__file__).resolve().parent / "cfdis_test"
data = read_cfdi_folder(folder)
comprobantes = data["comprobantes"]
conceptos = data["conceptos"]
impuestos = data["impuestos"]
xml_files = sorted(folder.glob("*.xml"))

print(comprobantes.head())
print(len(comprobantes), "XMLs leidos")
print(monthly_summary(comprobantes))
print(check_duplicate_uuid(comprobantes))
print("Primer invoice anidado:", data.to_json()[:1])
print("Conceptos rows:", len(conceptos))
print("Impuestos rows:", len(impuestos))
print("group_by_rfc emisor:", group_by_rfc(comprobantes, by="emisor"))
print("group_by_rfc receptor:", group_by_rfc(comprobantes, by="receptor"))
print("group_by_month:", group_by_month(comprobantes))
print("group_by_regimen:", group_by_regimen(comprobantes))
print("calculate_taxes (impuestos):", calculate_taxes(impuestos))
print("calculate_taxes (conceptos):", calculate_taxes(conceptos))
print("top_n emisor:", top_n(comprobantes, by="emisor", n=5))
print("top_n receptor:", top_n(comprobantes, by="receptor", n=5))
print("detect_cancelled:", detect_cancelled(comprobantes))
print("check_tax_math:", check_tax_math(comprobantes, conceptos))
print("check_date_range:", check_date_range(comprobantes, "2025-01-01", "2025-12-31"))
print("validate_all:", validate_all(comprobantes, conceptos, "2025-01-01", "2025-12-31"))

if xml_files:
    single = read_cfdi(xml_files[0])
    print("read_cfdi single keys:", single.keys())
    print("read_cfdi single to_json:", single.to_json()[:1])
