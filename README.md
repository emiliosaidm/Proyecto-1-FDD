# cfdi-pandas

`cfdi-pandas` is a Python library to read CFDI 4.0 XML invoices and work with them as pandas DataFrames for analysis and validation.

## Features

- Read one XML or a full folder of XMLs.
- Parse CFDI nodes into structured tables.
- Analyze invoices by RFC, month, and tax regime.
- Calculate tax totals (VAT, IEPS, withholdings).
- Validate duplicates, tax consistency, and date ranges.
- Export nested JSON per invoice (`concepts` + `taxes`).

## Installation

### From PyPI

```bash
pip install cfdi-pandas
```

### From this repository (editable mode)

```bash
pip install -e .
```

## Docker usage

This repository includes a dockerized setup to run the library, examples, tests, and notebook with the same environment.

### Build image

```bash
docker build -t cfdi-pandas:local .
```

### Run interactive shell

```bash
docker run --rm -it -v "$(pwd)":/app -w /app cfdi-pandas:local
```

### Run repository example (`test.py`)

This script uses the local example data in `cfdis_test` (or `cfdi_data` if present).

```bash
docker run --rm -it -v "$(pwd)":/app -w /app cfdi-pandas:local ./scripts/docker_example.sh
```

### Run tests

```bash
docker run --rm -it -v "$(pwd)":/app -w /app cfdi-pandas:local ./scripts/docker_tests.sh
```

## Quick start

```python
from pathlib import Path
from cfdi_pandas import read_cfdi_folder, monthly_summary, check_duplicate_uuid

folder = Path("cfdi_data")
data = read_cfdi_folder(folder)

invoices = data["comprobantes"]
print("Invoices:", len(invoices))
print(monthly_summary(invoices))
print(check_duplicate_uuid(invoices))
```

## Data model

`read_cfdi(...)` and `read_cfdi_folder(...)` return a `CFDIData` object (dict-like):

- `data["comprobantes"]`: one row per invoice.
- `data["conceptos"]`: one row per concept line.
- `data["impuestos"]`: one row per tax line.

You can also export nested JSON:

```python
json_invoices = data.to_json()
print(json_invoices[0].keys())
```

## Main API

### Reader

- `read_cfdi(path)`: read one CFDI XML.
- `read_cfdi_folder(folder, recursive=False)`: read all XML files in a folder.

### Analysis

- `group_by_rfc(df, by="emisor" | "receptor")`
- `group_by_month(df)`
- `group_by_regimen(df)`
- `calculate_taxes(df, period=None)`
- `monthly_summary(df)`
- `top_n(df, by="emisor" | "receptor", n=10)`
- `detect_cancelled(df)`

### Validation

- `check_duplicate_uuid(comprobantes_df)`
- `check_tax_math(comprobantes_df, conceptos_df)`
- `check_date_range(comprobantes_df, start, end)`
- `validate_all(comprobantes_df, conceptos_df, start=None, end=None)`

## Full example

```python
from pathlib import Path
from cfdi_pandas import (
    read_cfdi_folder,
    group_by_rfc,
    group_by_month,
    group_by_regimen,
    calculate_taxes,
    monthly_summary,
    top_n,
    detect_cancelled,
    check_duplicate_uuid,
    check_tax_math,
    check_date_range,
    validate_all,
)

folder = Path("cfdi_data")
if not folder.exists():
    folder = Path("cfdis_test")

data = read_cfdi_folder(folder)
comprobantes = data["comprobantes"]
conceptos = data["conceptos"]
impuestos = data["impuestos"]

print(group_by_rfc(comprobantes, by="emisor"))
print(group_by_month(comprobantes))
print(group_by_regimen(comprobantes))
print(monthly_summary(comprobantes))
print(top_n(comprobantes, by="receptor", n=10))
print(calculate_taxes(impuestos))
print(calculate_taxes(conceptos))
print(detect_cancelled(comprobantes))
print(check_duplicate_uuid(comprobantes))
print(check_tax_math(comprobantes, conceptos))
print(check_date_range(comprobantes, "2025-01-01", "2025-12-31"))
print(validate_all(comprobantes, conceptos, "2025-01-01", "2025-12-31"))
print(data.to_json()[:1])
```

## Notes

- This project expects CFDI 4.0 structure.
- Tax calculations can be run from `impuestos` or from concept-level taxes in `conceptos`.
- Empty DataFrames in validations mean no issues were found for that check.