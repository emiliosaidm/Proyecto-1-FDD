from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from lxml import etree

from cfdi_pandas.parser import (
    parse_complemento,
    parse_comprobante,
    parse_conceptos,
    parse_emisor,
    parse_impuestos,
    parse_receptor,
)


class CFDIData(dict[str, pd.DataFrame]):
    """Dictionary-like container of CFDI DataFrames with JSON export."""

    def to_json(self) -> list[dict[str, Any]]:
        invoices: list[dict[str, Any]] = []
        comprobantes = self.get("comprobantes", pd.DataFrame())
        conceptos = self.get("conceptos", pd.DataFrame())
        impuestos = self.get("impuestos", pd.DataFrame())
        conceptos_has_uuid = "uuid" in conceptos.columns
        impuestos_has_uuid = "uuid" in impuestos.columns

        for row in comprobantes.to_dict(orient="records"):
            invoice_uuid = row.get("uuid")
            if conceptos_has_uuid:
                concepts = conceptos[conceptos["uuid"] == invoice_uuid].to_dict(orient="records")
            else:
                concepts = []
            if impuestos_has_uuid:
                taxes = impuestos[impuestos["uuid"] == invoice_uuid].to_dict(orient="records")
            else:
                taxes = []

            invoice = dict(row)
            invoice["concepts"] = concepts
            invoice["taxes"] = taxes
            invoices.append(invoice)

        return invoices


def _read_one_xml(path: Path) -> dict[str, list[dict[str, Any]]]:
    tree = etree.parse(str(path)).getroot()
    complemento = parse_complemento(tree)
    uuid = complemento.get("uuid")

    comprobante_row = {}
    comprobante_row.update(parse_comprobante(tree))
    comprobante_row.update(parse_emisor(tree))
    comprobante_row.update(parse_receptor(tree))
    comprobante_row.update(complemento)

    conceptos_rows: list[dict[str, Any]] = []
    for row in parse_conceptos(tree):
        concept_row = dict(row)
        concept_row["uuid"] = uuid
        conceptos_rows.append(concept_row)

    impuestos_rows: list[dict[str, Any]] = []
    for row in parse_impuestos(tree):
        tax_row = dict(row)
        tax_row["uuid"] = uuid
        impuestos_rows.append(tax_row)

    return {
        "comprobantes": [comprobante_row],
        "conceptos": conceptos_rows,
        "impuestos": impuestos_rows,
    }


def _to_frames(records: dict[str, list[dict[str, Any]]]) -> CFDIData:
    return CFDIData(
        {
        "comprobantes": pd.DataFrame(records["comprobantes"]),
        "conceptos": pd.DataFrame(records["conceptos"]),
        "impuestos": pd.DataFrame(records["impuestos"]),
        }
    )


def read_cfdi(path: str | Path) -> CFDIData:
    """Read one CFDI XML and return DataFrames by node type."""
    xml_path = Path(path)
    records = _read_one_xml(xml_path)
    return _to_frames(records)


def read_cfdi_folder(folder: str | Path, recursive: bool = False) -> CFDIData:
    """Read all CFDI XML files in a folder and return DataFrames by node type."""
    folder_path = Path(folder)
    if recursive:
        xml_paths = list(folder_path.rglob("*.xml")) + list(folder_path.rglob("*.XML"))
    else:
        xml_paths = list(folder_path.glob("*.xml")) + list(folder_path.glob("*.XML"))

    combined: dict[str, list[dict[str, Any]]] = {
        "comprobantes": [],
        "conceptos": [],
        "impuestos": [],
    }

    for xml_path in sorted(set(xml_paths)):
        records = _read_one_xml(xml_path)
        combined["comprobantes"].extend(records["comprobantes"])
        combined["conceptos"].extend(records["conceptos"])
        combined["impuestos"].extend(records["impuestos"])

    return _to_frames(combined)
