from lxml import etree

from cfdi_pandas.parser import (
    parse_complemento,
    parse_comprobante,
    parse_conceptos,
    parse_emisor,
    parse_impuestos,
    parse_receptor,
)


def test_parse_main_nodes(sample_cfdi_xml: str) -> None:
    root = etree.fromstring(sample_cfdi_xml.encode("utf-8"))

    comprobante = parse_comprobante(root)
    emisor = parse_emisor(root)
    receptor = parse_receptor(root)
    complemento = parse_complemento(root)
    conceptos = parse_conceptos(root)
    impuestos = parse_impuestos(root)

    assert comprobante["version"] == "4.0"
    assert emisor["issuer_rfc"] == "AAA010101AAA"
    assert receptor["receiver_rfc"] == "BBB010101BBB"
    assert complemento["uuid"] == "123E4567-E89B-12D3-A456-426614174000"
    assert len(conceptos) == 1
    assert conceptos[0]["vat_amount"] == "160.00"
    assert len(conceptos[0]["concept_taxes"]) == 1
    assert len(impuestos) >= 1
