from __future__ import annotations

import json
import urllib.request
from typing import Any

import pandas as pd

_BASE_URL = "https://open.er-api.com/v6/latest"


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0.0)


def fetch_exchange_rate(
    base: str = "MXN",
    target: str = "USD",
) -> dict[str, Any]:
    """Fetch an exchange rate from the Open ExchangeRate API (no key needed).

    Parameters
    ----------
    base : str
        Source currency code (default ``"MXN"``).
    target : str
        Target currency code (default ``"USD"``).

    Returns
    -------
    dict
        ``{"base", "date", "target", "rate"}``.
    """
    url = f"{_BASE_URL}/{base}"
    with urllib.request.urlopen(url, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    rate = data["rates"][target]
    return {"base": base, "date": data.get("time_last_update_utc", ""), "target": target, "rate": float(rate)}


def convert_totals(
    comprobantes_df: pd.DataFrame,
    target: str = "USD",
) -> pd.DataFrame:
    """Add a ``total_<target>`` column with converted amounts.

    Uses the live exchange rate from the Open ExchangeRate API.

    Parameters
    ----------
    comprobantes_df : pd.DataFrame
        Invoices DataFrame with a ``total`` column.
    target : str
        Target currency code (default ``"USD"``).

    Returns
    -------
    pd.DataFrame
        Copy of the input with the new column appended.
    """
    info = fetch_exchange_rate(base="MXN", target=target)
    rate = info["rate"]
    out = comprobantes_df.copy()
    out["total"] = _to_numeric(out["total"])
    col_name = f"total_{target.lower()}"
    out[col_name] = (out["total"] * rate).round(2)
    return out
