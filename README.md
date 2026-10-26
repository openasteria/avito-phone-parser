# 📱 Avito Phone Parser — терминальный парсер Авито с меню выбора телефона

Терминальная утилита для **Linux / Kali Linux**: сканирует объявления Авито по
выбранной модели телефона, считает **среднюю цену** и ищет **самые дешёвые
объявления в хорошем состоянии**, выводя **прямые ссылки на товар на Avito**.

## Покрытие моделей (меню)

| Категория | Охват |
|---|---|
| 🍎 Apple iPhone | все модели вплоть до **iPhone 18 Pro Max** (+ Air, 17e, SE) |
| 🟢 Google Pixel | все вплоть до **Pixel 11 Pro XL** (+ Fold, a-серия) |
| 🔵 Samsung Galaxy | все вплоть до **Galaxy S26 Ultra** (+ Note, Z Fold/Flip, A-серия) |
| 🟠 Xiaomi | все вплоть до **Xiaomi 18 Pro Max** (+ Redmi Note, POCO) |
| ⚡ Другие | Honor, OnePlus, Realme, Motorola, Nothing, Sony, ASUS, Vivo, Oppo, Tecno, Infinix, Nubia — до последних моделей |

## Возможности

- Интерактивное **меню выбора телефона** (TUI на textual или текстовое меню);
- Сканирование **50 объявлений** (настраивается: 50/100/200 или `--count N`);
- Расчёт **средней и медианной цены**, минимальной цены;
- Фильтр «хорошее состояние»: отсев объявлений *«на запчасти / разбит / не работает / утоплен…»*;
- Вывод топ-10 самых дешёвых хороших предложений **+ ссылка на товар**;
- Режим `--brand samsung` — обзор всего бренда сразу с итоговой таблицей;
- Экспорт результатов `--json out.json`;
- Обход антибота: requests → curl_cffi (Chrome TLS-fingerprint) → curl → m.avito.ru → headless Chromium; резервный поиск через DuckDuckGo (`site:avito.ru`).

## 🚀 Быстрая установка (одна команда)

**Вариант 1 — одна команда (всё скачает и запустит меню):**
```bash
curl -fsSL https://raw.githubusercontent.com/openasteria/avito-phone-parser/main/install.sh | bash
```

**Вариант 2 — через git clone:**
```bash
git clone https://github.com/openasteria/avito-phone-parser.git && \
cd avito-phone-parser && chmod +x install.sh run.sh && ./install.sh
```

Скрипт `install.sh`: ставит системные зависимости (apt/dnf/pacman), создаёт
`.venv`, ставит Python-зависимости, добавляет команду `avito` в PATH и
**сразу запускает меню выбора телефона**.

### Ручная установка

```bash
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
./run.sh                    # ← меню выбора телефона
```

На Kali Linux при проблемах с PEP 668: `sudo pip install -r requirements.txt --break-system-packages`.

## Использование

```bash
./run.sh                                   # интерактивное меню выбора телефона
./run.sh --tui                             # графическое TUI-меню (дерево моделей)
./run.sh --model "iPhone 15 Pro Max"       # без меню, сразу скан 50 объявлений
./run.sh -m "Pixel 9 Pro" -n 100           # просканировать 100 объявлений
./run.sh --brand xiaomi                    # все Xiaomi + Redmi/POCO одним отчётом
./run.sh -m "Galaxy S26 Ultra" --location spb --json s26.json
```

Флаги: `--count/-n` (по умолчанию 50), `--location` (moskva/spb/…),
`--show-all` (все объявления), `--quiet`, `--json FILE`.

## Пример вывода

```
📱 iPhone 15 Pro Max   [запрос: «iPhone 15 Pro Max» · метод: curl_cffi(chrome-tls)]
────────────────────────────────────────
  Просканировано объявлений: 50 (всего в выдаче: 1284)
  💰 Средняя цена: 78 450 ₽   Медиана: 77 000 ₽   Минимум: 52 000 ₽
  ✔ В хорошем состоянии: 41 из 50
────────────────────────────────────────
🏆 САМЫЕ ДЕШЁВЫЕ ОБЪЯВЛЕНИЯ В ХОРОШЕМ СОСТОЯНИИ:
   1. 52 000 ₽ ✅ ↓34% от средней
      iPhone 15 Pro Max 256 ГБ, отличное состояние, полный комплект
      https://www.avito.ru/moskva/telefony/apple_iphone_15_pro_max_...
```

## Если Авито блокирует запросы (код 439 / капча)

Авито агрессивно фильтрует ботов. Утилита использует несколько обходов, но если
ваш IP/сеть помечены:

1. Поставьте headless-браузер: `sudo apt install chromium` (Kali: входит) —
   программа сама его подхватит; либо `playwright install chromium`.
2. Смените IP (мобильный интернет/VPN/прокси Tor):  
   `export HTTPS_PROXY=socks5://127.0.0.1:9050` (Tor: `sudo apt install tor && sudo systemctl start tor`).
3. Резервный канал DuckDuckGo включается автоматически.

## Структура проекта

```
avito_phone_parser.py  — главный скрипт (меню + CLI + отчёты)
avito_parser.py        — HTTP-слой, обход антибота, парсинг, аналитика цен
avito_models.py        — справочник всех моделей телефонов для меню
install.sh             — установка одной командой + запуск меню
run.sh                 — запуск (или команда `avito` после установки)
requirements.txt       — зависимости
```

## Юридическая оговорка

Инструмент предназначен для личного использования. Соблюдайте правила
использования Avito и не создавайте избыточной нагрузки на серверы (между
запросами выдерживаются случайные паузы).
