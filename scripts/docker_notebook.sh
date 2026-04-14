#!/usr/bin/env bash
set -euo pipefail

python - <<'PY'
from pathlib import Path
import nbformat
from nbclient import NotebookClient

path = Path("cfdi_pandas_tutorial.ipynb")
nb = nbformat.read(path.open("r", encoding="utf-8"), as_version=4)
NotebookClient(nb, timeout=1200, kernel_name="python3").execute()
nbformat.write(nb, path.open("w", encoding="utf-8"))
print("Notebook executed:", path)
PY
