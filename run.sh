#!/usr/bin/env bash
# run.sh — быстрый запуск парсера (меню выбора телефона, если без аргументов)
cd "$(dirname "$0")"
if [ -x .venv/bin/python ]; then
    PY=.venv/bin/python
else
    PY=python3
fi
exec "$PY" avito_phone_parser.py "$@"
