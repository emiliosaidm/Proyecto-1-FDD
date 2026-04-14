from __future__ import annotations

import pandas as pd


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0.0)


def check_duplicate_uuid(comprobantes_df: pd.DataFrame) -> pd.DataFrame:
    """Return rows where UUID is repeated."""
    if "uuid" not in comprobantes_df.columns:
        return pd.DataFrame(columns=["uuid", "count"])

    counts = (
        comprobantes_df.groupby("uuid", dropna=False)
        .size()
        .reset_index(name="count")
        .query("count > 1")
    )
    return counts.reset_index(drop=True)


def check_tax_math(comprobantes_df: pd.DataFrame, conceptos_df: pd.DataFrame, tolerance: float = 0.01) -> pd.DataFrame:
    """Return rows where subtotal does not match concept sums."""
    if "uuid" not in comprobantes_df.columns or "uuid" not in conceptos_df.columns:
        return pd.DataFrame(columns=["uuid", "subtotal_reported", "subtotal_calculated", "difference"])
    if "subtotal" not in comprobantes_df.columns or "amount" not in conceptos_df.columns:
        return pd.DataFrame(columns=["uuid", "subtotal_reported", "subtotal_calculated", "difference"])

    conceptos = conceptos_df.copy()
    conceptos["amount"] = _to_numeric(conceptos["amount"])

    sum_by_uuid = conceptos.groupby("uuid", dropna=False)["amount"].sum().reset_index()
    sum_by_uuid = sum_by_uuid.rename(columns={"amount": "subtotal_calculated"})

    base = comprobantes_df[["uuid", "subtotal"]].copy()
    base["subtotal_reported"] = _to_numeric(base["subtotal"])
    merged = base.merge(sum_by_uuid, on="uuid", how="left")
    merged["subtotal_calculated"] = merged["subtotal_calculated"].fillna(0.0)
    merged["difference"] = (merged["subtotal_reported"] - merged["subtotal_calculated"]).abs()

    return merged.loc[merged["difference"] > tolerance, ["uuid", "subtotal_reported", "subtotal_calculated", "difference"]]


def check_date_range(comprobantes_df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    """Return rows where fecha is outside the selected range."""
    if "issue_date" not in comprobantes_df.columns:
        return pd.DataFrame(columns=list(comprobantes_df.columns))

    work = comprobantes_df.copy()
    work["issue_date"] = pd.to_datetime(work["issue_date"], errors="coerce")
    start_dt = pd.to_datetime(start)
    end_dt = pd.to_datetime(end)
    mask = (work["issue_date"] < start_dt) | (work["issue_date"] > end_dt)
    return work.loc[mask].reset_index(drop=True)


def validate_all(
    comprobantes_df: pd.DataFrame,
    conceptos_df: pd.DataFrame,
    start: str | None = None,
    end: str | None = None,
) -> dict[str, pd.DataFrame]:
    """Run all validations and return findings by category."""
    results = {
        "duplicate_uuid": check_duplicate_uuid(comprobantes_df),
        "tax_math": check_tax_math(comprobantes_df, conceptos_df),
        "date_range": pd.DataFrame(),
    }

    if start is not None and end is not None:
        results["date_range"] = check_date_range(comprobantes_df, start, end)

    return results
