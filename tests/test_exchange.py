from pathlib import Path
from unittest.mock import patch
import json

import pandas as pd

from cfdi_pandas.exchange import convert_totals, fetch_exchange_rate
from cfdi_pandas.reader import read_cfdi_folder


_MOCK_RESPONSE = json.dumps({
    "result": "success",
    "base_code": "MXN",
    "time_last_update_utc": "Mon, 14 Apr 2025 00:02:31 +0000",
    "rates": {"MXN": 1, "USD": 0.058},
}).encode()


def _load_data(tmp_path: Path, xml_a: str, xml_b: str):
    (tmp_path / "a.xml").write_text(xml_a, encoding="utf-8")
    (tmp_path / "b.xml").write_text(xml_b, encoding="utf-8")
    return read_cfdi_folder(tmp_path)


class _FakeResponse:
    def __init__(self, data: bytes):
        self._data = data

    def read(self) -> bytes:
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


def test_fetch_exchange_rate() -> None:
    with patch("cfdi_pandas.exchange.urllib.request.urlopen", return_value=_FakeResponse(_MOCK_RESPONSE)):
        result = fetch_exchange_rate(base="MXN", target="USD")
    assert result["base"] == "MXN"
    assert result["target"] == "USD"
    assert result["rate"] == 0.058


def test_convert_totals(tmp_path: Path, sample_cfdi_xml: str, sample_cfdi_xml_egreso: str) -> None:
    data = _load_data(tmp_path, sample_cfdi_xml, sample_cfdi_xml_egreso)
    comprobantes = data["comprobantes"]

    with patch("cfdi_pandas.exchange.urllib.request.urlopen", return_value=_FakeResponse(_MOCK_RESPONSE)):
        result = convert_totals(comprobantes, target="USD")

    assert "total_usd" in result.columns
    assert len(result) == len(comprobantes)
    assert (result["total_usd"] >= 0).all()
