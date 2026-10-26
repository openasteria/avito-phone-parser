#!/usr/bin/env bash
# install.sh — установка и запуск парсера Avito на Linux / Kali Linux.
#
#  curl -fsSL https://raw.githubusercontent.com/openasteria/avito-phone-parser/main/install.sh | bash
#  или:  git clone https://github.com/openasteria/avito-phone-parser.git && cd avito-phone-parser && ./install.sh
set -e

REPO_URL="https://github.com/openasteria/avito-phone-parser.git"
TARGET_DIR="${AVITO_HOME:-$HOME/avito-phone-parser}"

# если скрипт скачан отдельно (не из клонов репозитория) — скачиваем репозиторий сам
if [ ! -f "avito_phone_parser.py" ]; then
    HERE="$(cd "$(dirname "$0")" && pwd)"
    if [ ! -f "$HERE/avito_phone_parser.py" ]; then
        echo "[*] Репозиторий не найден локально — скачиваю с GitHub..."
        command -v git >/dev/null || { apt-get update -y && apt-get install -y git; } 2>/dev/null || \
            { command -v sudo >/dev/null && sudo apt-get update -y && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y git; }
        rm -rf "$TARGET_DIR"
        git clone --depth 1 "$REPO_URL" "$TARGET_DIR"
        exec bash "$TARGET_DIR/install.sh" "$@"
    fi
    cd "$HERE"
else
    cd "$(dirname "$0")"
fi

PY=python3
SUDO=""
[ "$(id -u)" != "0" ] && command -v sudo >/dev/null && SUDO="sudo"

echo "[*] Проверка зависимостей..."
NEED_PKGS=""
command -v python3 >/dev/null || NEED_PKGS="$NEED_PKGS python3 python3-pip"
command -v curl    >/dev/null || NEED_PKGS="$NEED_PKGS curl"
if [ -n "$NEED_PKGS" ]; then
    echo "[*] Ставлю пакеты:$NEED_PKGS"
    if command -v apt-get >/dev/null; then
        $SUDO apt-get update -y
        DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y $NEED_PKGS
    elif command -v dnf >/dev/null; then
        $SUDO dnf install -y $NEED_PKGS
    elif command -v pacman >/dev/null; then
        $SUDO pacman -Sy --noconfirm $NEED_PKGS
    fi
fi

echo "[*] Создаю виртуальное окружение .venv..."
$PY -m venv .venv 2>/dev/null || { $SUDO apt-get install -y python3-venv && $PY -m venv .venv; }
./.venv/bin/pip install --quiet --upgrade pip
./.venv/bin/pip install --quiet -r requirements.txt

chmod +x avito_phone_parser.py run.sh 2>/dev/null || true

# симлинк в PATH для запуска командой «avito» из любой папки
if [ -d /usr/local/bin ]; then
    $SUDO ln -sf "$(pwd)/run.sh" /usr/local/bin/avito 2>/dev/null || true
fi

echo ""
echo "[✔] Установка завершена."
echo "    Запуск меню выбора телефона:   ./run.sh        (или команда: avito)"
echo "    CLI-режим:                     ./run.sh --model \"iPhone 15 Pro Max\" --count 50"
echo ""
exec ./run.sh "$@"
