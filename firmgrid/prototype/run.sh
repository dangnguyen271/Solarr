#!/bin/sh
# One-command demo. Fully offline — no network needed at the venue.
cd "$(dirname "$0")"
PY=../.venv/bin/python
[ -x "$PY" ] || PY=python3
exec "$PY" -m streamlit run app.py --server.headless true
