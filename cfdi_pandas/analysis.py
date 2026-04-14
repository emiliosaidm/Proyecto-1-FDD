from __future__ import annotations

import pandas as pd


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0.0)


def _with_month(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "issue_date" not in out.columns:
        out["issue_date"] = pd.NaT
    out["issue_date"] = pd.to_datetime(out["issue_date"], errors="coerce")
    out["month"] = out["issue_date"].dt.to_period("M").astype(str)
    return out


def _normalize_tax_rows(df: pd.DataFrame) -> pd.DataFrame:
    if {"tax_type", "tax_code", "amount"}.issubset(df.columns):
        out = df.copy()
        out["amount"] = _to_numeric(out["amount"])
        return out

    if "concept_taxes" in df.columns:
        rows = []
        base_cols = [c for c in ["uuid", "issue_date"] if c in df.columns]
        for record in df.to_dict(orient="records"):
            concept_taxes = record.get("concept_taxes") or []
            for tax in concept_taxes:
                row = {
                    "tax_type": tax.get("tax_type"),
                    "tax_code": tax.get("tax_code"),
                    "amount": tax.get("amount"),
                }
                for col in base_cols:
                    row[col] = record.get(col)
                rows.append(row)
        out = pd.DataFrame(rows)
        if out.empty:
            return pd.DataFrame(columns=["tax_type", "tax_code", "amount"])
        out["amount"] = _to_numeric(out["amount"])
        return out

    return pd.DataFrame(columns=["tax_type", "tax_code", "amount"])


def group_by_rfc(df: pd.DataFrame, by: str = "emisor") -> pd.DataFrame:
    """Group invoices by emisor or receptor RFC."""
    rfc_col = "issuer_rfc" if by == "emisor" else "receiver_rfc"
    work = df.copy()
    work["total"] = _to_numeric(work["total"])
    grouped = work.groupby(rfc_col, dropna=False)["total"].agg(["sum", "count", "mean"]).reset_index()
    return grouped.rename(
        columns={
            rfc_col: "rfc",
            "sum": "total_facturado",
            "count": "facturas",
            "mean": "promedio_factura",
        }
    )


def group_by_month(df: pd.DataFrame) -> pd.DataFrame:
    """Group invoices by month in YYYY-MM format."""
    work = _with_month(df)
    work["total"] = _to_numeric(work["total"])
    grouped = work.groupby("month", dropna=False)["total"].agg(["sum", "count"]).reset_index()
    return grouped.rename(columns={"sum": "total_facturado", "count": "facturas"})


def group_by_regimen(df: pd.DataFrame) -> pd.DataFrame:
    """Group invoices by emisor fiscal regime."""
    work = df.copy()
    work["total"] = _to_numeric(work["total"])
    grouped = work.groupby("issuer_tax_regime", dropna=False)["total"].agg(["sum", "count"]).reset_index()
    return grouped.rename(
        columns={
            "issuer_tax_regime": "tax_regime",
            "sum": "total_facturado",
            "count": "facturas",
        }
    )


def calculate_taxes(df: pd.DataFrame, period: str | tuple[str, str] | None = None) -> pd.DataFrame:
    """Calculate IVA, IEPS, and retentions totals from tax rows."""
    work = _normalize_tax_rows(df)

    if period is not None and "issue_date" in work.columns:
        dates = pd.to_datetime(work["issue_date"], errors="coerce")
        if isinstance(period, str):
            work = work[dates.dt.to_period("M").astype(str) == period]
        else:
            start, end = period
            work = work[(dates >= pd.to_datetime(start)) & (dates <= pd.to_datetime(end))]

    vat = work.loc[(work["tax_type"] == "transfer") & (work["tax_code"] == "002"), "amount"].sum()
    ieps = work.loc[(work["tax_type"] == "transfer") & (work["tax_code"] == "003"), "amount"].sum()
    withholdings = work.loc[work["tax_type"].astype(str).str.contains("withholding", na=False), "amount"].sum()

    return pd.DataFrame(
        [
            {
                "vat_total": float(vat),
                "ieps_total": float(ieps),
                "withholdings_total": float(withholdings),
            }
        ]
    )


def monthly_summary(comprobantes_df: pd.DataFrame) -> pd.DataFrame:
    """Build monthly ingresos, egresos, and net totals."""
    work = _with_month(comprobantes_df)
    work["total"] = _to_numeric(work["total"])

    ingresos = (
        work.loc[work["invoice_type"] == "I"]
        .groupby("month", dropna=False)["total"]
        .sum()
        .rename("ingresos")
    )
    egresos = (
        work.loc[work["invoice_type"] == "E"]
        .groupby("month", dropna=False)["total"]
        .sum()
        .rename("egresos")
    )

    summary = pd.concat([ingresos, egresos], axis=1).fillna(0.0).reset_index()
    summary["neto"] = summary["ingresos"] - summary["egresos"]
    return summary


def top_n(df: pd.DataFrame, by: str = "emisor", n: int = 10) -> pd.DataFrame:
    """Return top entities by billed amount."""
    col = "issuer_rfc" if by == "emisor" else "receiver_rfc"
    work = df.copy()
    work["total"] = _to_numeric(work["total"])
    result = work.groupby(col, dropna=False)["total"].sum().reset_index()
    result = result.rename(columns={col: "rfc", "total": "total_facturado"})
    return result.sort_values("total_facturado", ascending=False).head(n).reset_index(drop=True)


def detect_cancelled(comprobantes_df: pd.DataFrame) -> pd.DataFrame:
    """Detect invoices marked as canceled by status."""
    work = comprobantes_df.copy()
    status_cancelled = pd.Series(False, index=work.index)

    if "status" in work.columns:
        status_cancelled = work["status"].astype(str).str.contains("cancel", case=False, na=False)

    return work[status_cancelled].reset_index(drop=True)
