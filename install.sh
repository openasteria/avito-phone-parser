#!/usr/bin/env bash
# install.sh — установка и запуск парсера Avito на Linux / Kali Linux.
#
#  curl -fsSL https://raw.githubusercontent.com/openasteria/avito-phone-parser/main/install.sh | bash
#  или:  git clone https://github.com/openasteria/avito-phone-parser.git && cd avito-phone-parser && ./install.sh
set -e

REPO_URL="https://github.com/openasteria/avito-phone-parser.git"
TARGET_DIR="${AVITO_HOME:-$HOME/avito-phone-parser}"

# Если скрипт скачан отдельно (curl | bash) или файлы устарели — (пере)скачиваем репозиторий.
# Повторный запуск команды установки всегда подтягивает свежие изменения с GitHub (git pull).
need_clone=0
if [ ! -f "avito_phone_parser.py" ]; then
    need_clone=1
else
    cd "$(dirname "$0")"
    # если это git-клон и на GitHub есть новые коммиты — обновляем, чтобы фиксы сразу применялись
    if [ -d .git ] && command -v git >/dev/null 2>&1; then
        echo "[*] Проверяю обновления на GitHub..."
        git fetch --depth 1 origin main >/dev/null 2>&1 && \
            git reset --hard origin/main >/dev/null 2>&1 && \
            echo "[✔] Код обновлён до последней версии." || true
    fi
fi

if [ "$need_clone" = "1" ]; then
    HERE="$(cd "$(dirname "$0" 2>/dev/null)" && pwd)" || HERE="$PWD"
    if [ ! -f "$HERE/avito_phone_parser.py" ]; then
        echo "[*] Репозиторий не найден локально — скачиваю с GitHub..."
        command -v git >/dev/null || { apt-get update -y && apt-get install -y git; } 2>/dev/null || \
            { command -v sudo >/dev/null && sudo apt-get update -y && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y git; }
        if [ -d "$TARGET_DIR/.git" ]; then
            git -C "$TARGET_DIR" pull --ff-only 2>/dev/null || { rm -rf "$TARGET_DIR"; git clone --depth 1 "$REPO_URL" "$TARGET_DIR"; }
        else
            rm -rf "$TARGET_DIR"
            git clone --depth 1 "$REPO_URL" "$TARGET_DIR"
        fi
        exec bash "$TARGET_DIR/install.sh" "$@"
    fi
    cd "$HERE"
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

# команда «avito» в PATH — генерируем обёртку с АБСОЛЮТНЫМИ путями,
# чтобы запуск работал из любой папки (в т.ч. когда ~/bin ещё не в PATH)
APP_DIR="$(pwd)"
mkdir -p "$HOME/.local/bin" 2>/dev/null || true
{
  echo '#!/usr/bin/env bash'
  echo "# avito — запуск парсера Avito (сгенерировано install.sh)"
  echo 'cd "'"$APP_DIR"'" || { echo "[!] Папка $APP_DIR не найдена — переустановите:"; echo "    curl -fsSL https://raw.githubusercontent.com/openasteria/avito-phone-parser/main/install.sh | bash"; exit 1; }'
  if [ -x "$APP_DIR/.venv/bin/python" ]; then
    echo 'exec "'"$APP_DIR"'/.venv/bin/python" "'"$APP_DIR"'/avito_phone_parser.py" "$@"'
  else
    echo 'exec python3 "'"$APP_DIR"'/avito_phone_parser.py" "$@"'
  fi
} > "$HOME/.local/bin/avito"
chmod +x "$HOME/.local/bin/avito"

# добавляем ~/.local/bin в PATH для bash и zsh (идемпотентно)
for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
    if ! grep -qs '.local/bin' "$rc" 2>/dev/null; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$rc"
    fi
done

# симлинк в /usr/local/bin (если есть права) — тоже рабочая обёртка, а не битый скрипт
if [ -d /usr/local/bin ]; then
    $SUDO cp -f "$HOME/.local/bin/avito" /usr/local/bin/avito 2>/dev/null || true
    $SUDO chmod +x /usr/local/bin/avito 2>/dev/null || true
fi

echo ""
echo "[✔] Установка завершена."
echo "    Запуск меню:                   ./run.sh   или команда: avito   (новый терминал или: source ~/.zshrc)"
echo "    CLI-режим:                     ./run.sh --model \"iPhone 15 Pro Max\" --count 50"
echo ""
exec ./run.sh "$@"
