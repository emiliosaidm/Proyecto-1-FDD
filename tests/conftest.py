import pytest


@pytest.fixture
def sample_cfdi_xml() -> str:
    return """<?xml version="1.0" encoding="utf-8"?>
<cfdi:Comprobante
    xmlns:cfdi="http://www.sat.gob.mx/cfd/4"
    xmlns:tfd="http://www.sat.gob.mx/TimbreFiscalDigital"
    Version="4.0"
    Serie="A"
    Folio="100"
    Fecha="2024-01-10T10:00:00"
    SubTotal="1000.00"
    Total="1160.00"
    TipoDeComprobante="I"
    Moneda="MXN"
    LugarExpedicion="64000">
  <cfdi:Emisor Rfc="AAA010101AAA" Nombre="Empresa Emisora" RegimenFiscal="601" />
  <cfdi:Receptor
      Rfc="BBB010101BBB"
      Nombre="Cliente Receptor"
      UsoCFDI="G03"
      DomicilioFiscalReceptor="64000"
      RegimenFiscalReceptor="605" />
  <cfdi:Conceptos>
    <cfdi:Concepto
        ClaveProdServ="01010101"
        Cantidad="1"
        ClaveUnidad="E48"
        Unidad="Servicio"
        Descripcion="Servicio de prueba"
        ValorUnitario="1000.00"
        Importe="1000.00">
      <cfdi:Impuestos>
        <cfdi:Traslados>
          <cfdi:Traslado Base="1000.00" Impuesto="002" TipoFactor="Tasa" TasaOCuota="0.160000" Importe="160.00" />
        </cfdi:Traslados>
      </cfdi:Impuestos>
    </cfdi:Concepto>
  </cfdi:Conceptos>
  <cfdi:Impuestos TotalImpuestosTrasladados="160.00">
    <cfdi:Traslados>
      <cfdi:Traslado Base="1000.00" Impuesto="002" TipoFactor="Tasa" TasaOCuota="0.160000" Importe="160.00" />
    </cfdi:Traslados>
  </cfdi:Impuestos>
  <cfdi:Complemento>
    <tfd:TimbreFiscalDigital
        Version="1.1"
        UUID="123E4567-E89B-12D3-A456-426614174000"
        FechaTimbrado="2024-01-10T10:01:00"
        NoCertificadoSAT="00001000000504465028"
        SelloCFD="ABC123" />
  </cfdi:Complemento>
</cfdi:Comprobante>
"""


@pytest.fixture
def sample_cfdi_xml_egreso(sample_cfdi_xml: str) -> str:
    return (
        sample_cfdi_xml.replace('TipoDeComprobante="I"', 'TipoDeComprobante="E"')
        .replace('Fecha="2024-01-10T10:00:00"', 'Fecha="2024-02-15T11:00:00"')
        .replace('UUID="123E4567-E89B-12D3-A456-426614174000"', 'UUID="223E4567-E89B-12D3-A456-426614174000"')
        .replace('Total="1160.00"', 'Total="580.00"')
        .replace('SubTotal="1000.00"', 'SubTotal="500.00"')
        .replace('Importe="1000.00"', 'Importe="500.00"')
        .replace('ValorUnitario="1000.00"', 'ValorUnitario="500.00"')
        .replace('Base="1000.00"', 'Base="500.00"')
        .replace('Importe="160.00"', 'Importe="80.00"')
        .replace('TotalImpuestosTrasladados="160.00"', 'TotalImpuestosTrasladados="80.00"')
    )
