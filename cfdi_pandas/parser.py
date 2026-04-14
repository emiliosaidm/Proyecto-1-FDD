from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from lxml import etree

NS = {
    "cfdi": "http://www.sat.gob.mx/cfd/4",
    "tfd": "http://www.sat.gob.mx/TimbreFiscalDigital",
    "implocal": "http://www.sat.gob.mx/implocal",
}


def _attr(node: etree._Element | None, key: str, default: str | None = None) -> str | None:
    if node is None:
        return default
    return node.attrib.get(key, default)


def _to_decimal(value: str | None) -> Decimal:
    if value in (None, ""):
        return Decimal("0")
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError):
        return Decimal("0")


def parse_comprobante(tree: etree._Element) -> dict[str, Any]:
    """Extract top-level comprobante attributes."""
    return {
        "version": _attr(tree, "Version"),
        "series": _attr(tree, "Serie"),
        "folio_number": _attr(tree, "Folio"),
        "issue_date": _attr(tree, "Fecha"),
        "subtotal": _attr(tree, "SubTotal"),
        "total": _attr(tree, "Total"),
        "invoice_type": _attr(tree, "TipoDeComprobante"),
        "currency": _attr(tree, "Moneda"),
        "exchange_rate": _attr(tree, "TipoCambio"),
        "place_of_issue": _attr(tree, "LugarExpedicion"),
    }


def parse_emisor(tree: etree._Element) -> dict[str, Any]:
    """Extract emisor node values."""
    emisor = tree.find("cfdi:Emisor", namespaces=NS)
    return {
        "issuer_rfc": _attr(emisor, "Rfc"),
        "issuer_name": _attr(emisor, "Nombre"),
        "issuer_tax_regime": _attr(emisor, "RegimenFiscal"),
    }


def parse_receptor(tree: etree._Element) -> dict[str, Any]:
    """Extract receptor node values."""
    receptor = tree.find("cfdi:Receptor", namespaces=NS)
    return {
        "receiver_rfc": _attr(receptor, "Rfc"),
        "receiver_name": _attr(receptor, "Nombre"),
        "receiver_cfdi_use": _attr(receptor, "UsoCFDI"),
        "receiver_fiscal_address": _attr(receptor, "DomicilioFiscalReceptor"),
        "receiver_tax_regime": _attr(receptor, "RegimenFiscalReceptor"),
    }


def parse_complemento(tree: etree._Element) -> dict[str, Any]:
    """Extract TimbreFiscalDigital values from complemento."""
    timbre = tree.find("cfdi:Complemento/tfd:TimbreFiscalDigital", namespaces=NS)
    return {
        "uuid": _attr(timbre, "UUID"),
        "stamp_date": _attr(timbre, "FechaTimbrado"),
        "sat_certificate_number": _attr(timbre, "NoCertificadoSAT"),
        "cfd_seal": _attr(timbre, "SelloCFD"),
    }


def parse_conceptos(tree: etree._Element) -> list[dict[str, Any]]:
    """Extract conceptos rows with tax totals per concept."""
    conceptos = tree.findall("cfdi:Conceptos/cfdi:Concepto", namespaces=NS)
    rows: list[dict[str, Any]] = []

    for index, concepto in enumerate(conceptos):
        impuestos_trasladados = Decimal("0")
        impuestos_retenidos = Decimal("0")
        iva = Decimal("0")
        ieps = Decimal("0")
        impuestos_concepto: list[dict[str, Any]] = []

        for traslado in concepto.findall("cfdi:Impuestos/cfdi:Traslados/cfdi:Traslado", namespaces=NS):
            importe = _to_decimal(_attr(traslado, "Importe"))
            impuesto = _attr(traslado, "Impuesto")
            impuestos_trasladados += importe
            if impuesto == "002":
                iva += importe
            if impuesto == "003":
                ieps += importe
            impuestos_concepto.append(
                {
                    "tax_type": "transfer",
                    "tax_code": impuesto,
                    "factor_type": _attr(traslado, "TipoFactor"),
                    "rate_or_fee": _attr(traslado, "TasaOCuota"),
                    "base": _attr(traslado, "Base"),
                    "amount": str(importe),
                }
            )

        for retencion in concepto.findall("cfdi:Impuestos/cfdi:Retenciones/cfdi:Retencion", namespaces=NS):
            importe = _to_decimal(_attr(retencion, "Importe"))
            impuestos_retenidos += importe
            impuestos_concepto.append(
                {
                    "tax_type": "withholding",
                    "tax_code": _attr(retencion, "Impuesto"),
                    "factor_type": _attr(retencion, "TipoFactor"),
                    "rate_or_fee": _attr(retencion, "TasaOCuota"),
                    "base": _attr(retencion, "Base"),
                    "amount": str(importe),
                }
            )

        rows.append(
            {
                "concept_index": index,
                "product_service_key": _attr(concepto, "ClaveProdServ"),
                "description": _attr(concepto, "Descripcion"),
                "quantity": _attr(concepto, "Cantidad"),
                "unit_key": _attr(concepto, "ClaveUnidad"),
                "unit": _attr(concepto, "Unidad"),
                "unit_price": _attr(concepto, "ValorUnitario"),
                "amount": _attr(concepto, "Importe"),
                "discount": _attr(concepto, "Descuento"),
                "transferred_taxes_amount": str(impuestos_trasladados),
                "withheld_taxes_amount": str(impuestos_retenidos),
                "vat_amount": str(iva),
                "ieps_amount": str(ieps),
                "concept_taxes": impuestos_concepto,
            }
        )

    return rows


def parse_impuestos(tree: etree._Element) -> list[dict[str, Any]]:
    """Extract comprobante-level tax rows and totals."""
    impuestos = tree.find("cfdi:Impuestos", namespaces=NS)
    total_trasladados = _attr(impuestos, "TotalImpuestosTrasladados", "0")
    total_retenidos = _attr(impuestos, "TotalImpuestosRetenidos", "0")

    rows: list[dict[str, Any]] = []

    for traslado in tree.findall("cfdi:Impuestos/cfdi:Traslados/cfdi:Traslado", namespaces=NS):
        rows.append(
            {
                "tax_type": "transfer",
                "tax_code": _attr(traslado, "Impuesto"),
                "factor_type": _attr(traslado, "TipoFactor"),
                "rate_or_fee": _attr(traslado, "TasaOCuota"),
                "base": _attr(traslado, "Base"),
                "amount": _attr(traslado, "Importe"),
                "total_transferred_taxes": total_trasladados,
                "total_withheld_taxes": total_retenidos,
            }
        )

    for retencion in tree.findall("cfdi:Impuestos/cfdi:Retenciones/cfdi:Retencion", namespaces=NS):
        rows.append(
            {
                "tax_type": "withholding",
                "tax_code": _attr(retencion, "Impuesto"),
                "factor_type": _attr(retencion, "TipoFactor"),
                "rate_or_fee": _attr(retencion, "TasaOCuota"),
                "base": _attr(retencion, "Base"),
                "amount": _attr(retencion, "Importe"),
                "total_transferred_taxes": total_trasladados,
                "total_withheld_taxes": total_retenidos,
            }
        )

    for local_traslado in tree.findall(
        "cfdi:Complemento/implocal:ImpuestosLocales/implocal:TrasladosLocales",
        namespaces=NS,
    ):
        rows.append(
            {
                "tax_type": "local_transfer",
                "tax_code": _attr(local_traslado, "ImpLocTrasladado"),
                "factor_type": "Tasa",
                "rate_or_fee": _attr(local_traslado, "TasadeTraslado"),
                "base": None,
                "amount": _attr(local_traslado, "Importe"),
                "total_transferred_taxes": total_trasladados,
                "total_withheld_taxes": total_retenidos,
            }
        )

    for local_retencion in tree.findall(
        "cfdi:Complemento/implocal:ImpuestosLocales/implocal:RetencionesLocales",
        namespaces=NS,
    ):
        rows.append(
            {
                "tax_type": "local_withholding",
                "tax_code": _attr(local_retencion, "ImpLocRetenido"),
                "factor_type": "Tasa",
                "rate_or_fee": _attr(local_retencion, "TasadeRetencion"),
                "base": None,
                "amount": _attr(local_retencion, "Importe"),
                "total_transferred_taxes": total_trasladados,
                "total_withheld_taxes": total_retenidos,
            }
        )

    if not rows:
        rows.append(
            {
                "tax_type": None,
                "tax_code": None,
                "factor_type": None,
                "rate_or_fee": None,
                "base": None,
                "amount": None,
                "total_transferred_taxes": total_trasladados,
                "total_withheld_taxes": total_retenidos,
            }
        )

    return rows
