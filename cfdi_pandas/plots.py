from __future__ import annotations

import pandas as pd

try:
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
except ImportError:  # pragma: no cover
    plt = None  # type: ignore[assignment]
    ticker = None  # type: ignore[assignment]


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0.0)


def _require_matplotlib() -> None:
    if plt is None:
        raise ImportError("matplotlib is required for plotting – install it with: pip install matplotlib")


def _with_month(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "issue_date" not in out.columns:
        out["issue_date"] = pd.NaT
    out["issue_date"] = pd.to_datetime(out["issue_date"], errors="coerce")
    out["month"] = out["issue_date"].dt.to_period("M").astype(str)
    return out


_TYPE_LABELS: dict[str, str] = {
    "I": "Ingreso",
    "E": "Egreso",
    "T": "Traslado",
    "P": "Pago",
    "N": "Nómina",
}


def plot_income_expenses(comprobantes_df: pd.DataFrame) -> plt.Figure:  # type: ignore[name-defined]
    """Bar chart of monthly ingresos vs egresos."""
    _require_matplotlib()

    work = _with_month(comprobantes_df)
    work["total"] = _to_numeric(work["total"])

    ingresos = (
        work.loc[work["invoice_type"] == "I"]
        .groupby("month", dropna=False)["total"]
        .sum()
        .rename("Ingresos")
    )
    egresos = (
        work.loc[work["invoice_type"] == "E"]
        .groupby("month", dropna=False)["total"]
        .sum()
        .rename("Egresos")
    )

    summary = pd.concat([ingresos, egresos], axis=1).fillna(0.0).sort_index()

    fig, ax = plt.subplots(figsize=(10, 5))
    x = range(len(summary))
    width = 0.35

    bars_in = ax.bar(
        [i - width / 2 for i in x],
        summary["Ingresos"],
        width,
        label="Ingresos",
        color="#2ecc71",
    )
    bars_eg = ax.bar(
        [i + width / 2 for i in x],
        summary["Egresos"],
        width,
        label="Egresos",
        color="#e74c3c",
    )

    ax.set_xticks(list(x))
    ax.set_xticklabels(summary.index, rotation=45, ha="right")
    ax.set_xlabel("Mes")
    ax.set_ylabel("Total ($)")
    ax.set_title("Ingresos vs Egresos por Mes")
    ax.legend()
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("${x:,.0f}"))
    fig.tight_layout()
    return fig


def plot_by_cfdi_type(comprobantes_df: pd.DataFrame) -> plt.Figure:  # type: ignore[name-defined]
    """Pie chart of invoice count by CFDI type (I, E, T, P, N)."""
    _require_matplotlib()

    work = comprobantes_df.copy()
    work["type_label"] = work["invoice_type"].map(_TYPE_LABELS).fillna(work["invoice_type"])

    counts = work["type_label"].value_counts()

    colors = ["#2ecc71", "#e74c3c", "#3498db", "#f39c12", "#9b59b6"]
    fig, ax = plt.subplots(figsize=(7, 7))
    wedges, texts, autotexts = ax.pie(
        counts.values,
        labels=counts.index,
        autopct="%1.1f%%",
        startangle=140,
        colors=colors[: len(counts)],
    )
    ax.set_title("Distribución por Tipo de CFDI")
    fig.tight_layout()
    return fig
