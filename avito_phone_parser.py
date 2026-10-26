#!/usr/bin/env python3
"""
avito_phone_parser — терминальный парсер Авито с меню выбора телефона.

  🍎 iPhone (все до 18 Pro Max) · 🟢 Pixel (до 11 Pro XL)
  🔵 Samsung Galaxy (до S26 Ultra) · 🟠 Xiaomi (до 18 Pro Max) · ⚡ Другие бренды

Сканирует объявления (по умолчанию 50), считает СРЕДНЮЮ цену и ищет
самые дешёвые предложения в ХОРОШЕМ состоянии, выводит ссылки на Avito.

Запуск без аргументов → интерактивное меню.
Режимы:  TUI (rich/textual если есть) / простой текстовый menu / CLI-флаги.

Примеры:
  ./avito_phone_parser.py                          # меню выбора телефона
  ./avito_phone_parser.py --model "iPhone 15 Pro" --count 50
  ./avito_phone_parser.py --brand samsung          # все Samsung одним отчётом
  ./avito_phone_parser.py --cli --model "Pixel 9 Pro" --json out.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import textwrap
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from avito_models import build_menu, normalize_query  # noqa: E402
from avito_parser import Listing, ScanResult, scan_model  # noqa: E402

# ----------------------------- оформление -----------------------------------
USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None

def c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text

BOLD = lambda t: c("1", t)
DIM = lambda t: c("2", t)
GREEN = lambda t: c("32", t)
RED = lambda t: c("31", t)
YELLOW = lambda t: c("33", t)
CYAN = lambda t: c("36", t)
MAGENTA = lambda t: c("35", t)
BLUE = lambda t: c("34", t)


def fmt_price(p) -> str:
    if p is None:
        return "?"
    return f"{int(round(p)):,}".replace(",", " ") + " ₽"


BANNER = r"""
    _                                            ____  _
   / \   __ _ _____   _ _ __ ___  (_)___  ___   |  _ \| |__  _ __  _ __  ___ _ __
  / _ \ / _` |_ -\ \ / / | '_ ` _ \| / __|/ _ \  | |_) | '_ \| '_ \| '_ \/ _ \ '__|
 / ___ \ (_| |/ _\\ V /| | | | | | | \__ \  __/  |  __/| | | | |_) | |_) |  __/ |
/_/   \_\__,_/____|_| |_|_| |_| |_|_|___/\___|  |_|   |_|.__/| .__/| .__/ \___|_|
                                                            |_|   |_|
"""


def print_banner():
    print(CYAN(BANNER))
    print(BOLD("  Парсер Avito · телефоны · средняя цена · поиск лучших цен"))
    print(DIM(f"  Linux/Kali ready · {datetime.now():%d.%m.%Y %H:%M}"))
    print()


# ------------------------------ вывод отчёта ----------------------------------

def print_report(res: ScanResult, count: int, show_all: bool = False):
    line = "─" * 72
    print()
    print(BOLD(f"📱 {res.model}") + DIM(f"   [запрос: «{res.query}» · метод: {res.method or '?'}]"))
    print(line)
    if res.error and not res.listings:
        print(RED("✖ ") + res.error)
        return
    n = len(res.listings)
    priced = res.priced()
    good = [l for l in priced if l.good]
    print(f"  Просканировано объявлений: {BOLD(str(n))}"
          + (f" (всего в выдаче: {res.total_found})" if res.total_found else ""))
    if not priced:
        print(YELLOW("  ⚠ Цены не удалось извлечь (страница могла быть заблокирована антиботом)."))
        return
    avg, med, mn = res.avg_price(), res.median_price(), res.min_price()
    print(f"  💰 Средняя цена: {BOLD(GREEN(fmt_price(avg)))}   "
          f"Медиана: {BOLD(fmt_price(med))}   Минимум: {BOLD(fmt_price(mn))}")
    print(f"  ✔ В хорошем состоянии: {len(good)} из {len(priced)}")
    print(line)

    cheapest = res.cheapest_good(10)
    print(BOLD("🏆 САМЫЕ ДЕШЁВЫЕ ОБЪЯВЛЕНИЯ В ХОРОШЕМ СОСТОЯНИИ:"))
    if not cheapest:
        print(YELLOW("  Нет объявлений, помеченных как «хорошее состояние» — смотрите общий список ниже."))
    for i, l in enumerate(cheapest, 1):
        tag = ""
        if avg and l.price < avg:
            diff_pct = (avg - l.price) / avg * 100
            tag = GREEN(f" ↓{diff_pct:.0f}% от средней")
        badge = " ✅" if l.condition_score >= 2 else " ✔"
        print(f"  {i:>2}. {BOLD(fmt_price(l.price))}{badge}{tag}")
        print(f"      {l.title[:70]}{(' · ' + DIM(l.location)) if l.location else ''}")
        print(f"      {CYAN(l.url)}")
    print(line)

    below = [l for l in res.below_avg_good() if l not in cheapest][:10]
    if below:
        print(BOLD("💡 Также дешевле средней цены (хорошее состояние):"))
        for l in below:
            print(f"   • {fmt_price(l.price):>12}  {l.title[:48]:<48} {CYAN(l.url)}")
        print(line)

    if show_all:
        print(BOLD("📋 Все просканированные объявления:"))
        for l in sorted(priced, key=lambda x: x.price):
            mark = RED(" ✖плох.") if l.bad_condition else ""
            print(f"   {fmt_price(l.price):>12}{mark}  {l.title[:50]:<50} {DIM(l.url)}")
    print(line)


def result_to_dict(res: ScanResult) -> dict:
    return {
        "model": res.model,
        "query": res.query,
        "method": res.method,
        "scanned": len(res.listings),
        "total_in_search": res.total_found,
        "avg_price": res.avg_price(),
        "median_price": res.median_price(),
        "min_price": res.min_price(),
        "error": res.error,
        "listings": [
            {"title": l.title, "price": l.price, "url": l.url,
             "location": l.location, "good_condition": l.good,
             "condition_score": l.condition_score}
            for l in res.listings
        ],
    }


# --------------------------- простое текстовое меню ---------------------------

def simple_menu() -> tuple[str, str] | None:
    """Возвращает (категория, модель) или None."""
    menu = build_menu()
    cats = list(menu.keys())
    while True:
        print(BOLD("Выберите категорию:"))
        for i, cat in enumerate(cats, 1):
            print(f"  {i:>2}. {cat} {DIM(f'({len(menu[cat])})')}")
        print("   0. Выход")
        sel = input(YELLOW("\nКатегория> ")).strip()
        if sel == "0":
            return None
        try:
            idx = int(sel) - 1
            assert 0 <= idx < len(cats)
        except Exception:
            print(RED("Неверный выбор."))
            continue
        cat = cats[idx]
        models = menu[cat]
        # постраничный показ моделей
        page, per = 0, 20
        while True:
            start = page * per
            chunk = models[start:start + per]
            print(BOLD(f"\n{cat} — стр. {page + 1}/{max(1, (len(models) + per - 1) // per)}:"))
            for j, m in enumerate(chunk, start + 1):
                print(f"  {j:>3}. {m}")
            print("    n/p — страницы, b — назад к категориям, 0 — выход")
            sel = input(YELLOW("\nМодель> ")).strip().lower()
            if sel in ("b",):
                break
            if sel == "0":
                return None
            if sel in ("n", "p"):
                if sel == "n" and start + per < len(models):
                    page += 1
                if sel == "p" and page > 0:
                    page -= 1
                continue
            try:
                num = int(sel)
                assert 1 <= num <= len(models)
                return cat, models[num - 1]
            except Exception:
                print(RED("Неверный номер модели."))


# ------------------------------- TUI (textual) --------------------------------

def textual_app():
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal, Vertical
    from textual.widgets import Header, Footer, Tree, Static, Button, Input, Label
    from textual.reactive import reactive
    from textual import work

    class AvitoApp(App):
        CSS = """
        #main { layout: horizontal; }
        #tree { width: 34%; border: round $primary; }
        #right { width: 1fr; }
        #status { height: auto; padding: 1; background: $panel; }
        #report { height: 1fr; border: round $secondary; padding: 1; }
        #controls { height: auto; padding: 1; }
        Button { margin-right: 1; }
        """
        BINDINGS = [("q", "quit", "Quit"), ("r", "rescan", "Rescan")]

        def __init__(self):
            super().__init__()
            self.menu = build_menu()
            self.selected_model: str | None = None

        def compose(self) -> ComposeResult:
            yield Header()
            with Vertical(id="controls"):
                yield Label("Количество объявлений для сканирования:")
                with Horizontal():
                    yield Button("50 (default)", id="c50", variant="primary")
                    yield Button("100", id="c100")
                    yield Button("200", id="c200")
                    yield Button("▶ Сканировать", id="scan", variant="success")
            with Horizontal(id="main"):
                yield Tree("Выберите телефон", id="tree")
                with Vertical(id="right"):
                    yield Static("Ожидание выбора модели…", id="status")
                    yield Static("", id="report")
            yield Footer()

        def on_mount(self):
            tree = self.query_one("#tree", Tree)
            tree.show_root = False
            tree.auto_expand = False
            for cat, models in self.menu.items():
                node = tree.add_node(cat, data=("cat", cat))
                for m in models:
                    node.add_leaf(m, data=("model", m))

        def on_tree_node_selected(self, event: Tree.NodeSelected):
            data = event.node.data
            if data and data[0] == "model":
                self.selected_model = data[1]
                self.query_one("#status", Static).update(
                    f"Выбрано: [bold]{data[1]}[/bold] — нажмите [green]▶ Сканировать[/green]")

        def on_button_pressed(self, event: Button.Pressed) -> None:
            bid = event.button.id
            if bid in ("c50", "c100", "c200"):
                self.scan_count = int(bid[1:])
                for b in ("c50", "c100", "c200"):
                    self.query_one(f"#{b}", Button).variant = "primary" if b == bid else "default"
            elif bid == "scan":
                self.do_scan()

        @work(thread=False)
        async def do_scan(self):
            if not self.selected_model:
                self.notify("Сначала выберите модель в дереве слева!", severity="warning")
                return
            status = self.query_one("#status", Static)
            report = self.query_one("#report", Static)
            count = getattr(self, "scan_count", 50)
            status.update(f"⏳ Сканирую Avito по [bold]{self.selected_model}[/bold] ({count} объявлений)…")
            report.update("")
            res = await self.run_in_thread(
                scan_model, self.selected_model,
                normalize_query(self.selected_model), count)
            md = self.result_markdown(res, count)
            status.update(f"✔ Готово: {self.selected_model} · метод: {res.method or '?'}")
            report.update(md)

        def action_rescan(self):
            self.do_scan()

        def result_markdown(self, res: ScanResult, count: int) -> str:
            if res.error and not res.listings:
                return f"❌ {res.error}"
            lines = [
                f"# 📱 {res.model}",
                f"- Просканировано: **{len(res.listings)}**",
                f"- 💰 Средняя цена: **{fmt_price(res.avg_price())}**",
                f"- Медиана: {fmt_price(res.median_price())} · Мин.: {fmt_price(res.min_price())}",
                "",
                "## 🏆 Самые дешёвые в хорошем состоянии",
            ]
            for i, l in enumerate(res.cheapest_good(10), 1):
                ok = "✅" if l.condition_score >= 2 else "✔"
                lines.append(f"{i}. **{fmt_price(l.price)}** {ok} [{l.title[:60]}]({l.url})")
            return "\n".join(lines)

    AvitoApp().run()


# ------------------------------- CLI main -------------------------------------

BRAND_ALIASES = {
    "iphone": "🍎 APPLE iPhone (все до 18 Pro Max)", "apple": "🍎 APPLE iPhone (все до 18 Pro Max)",
    "pixel": "🟢 GOOGLE Pixel (все до 11 Pro XL)", "google": "🟢 GOOGLE Pixel (все до 11 Pro XL)",
    "samsung": "🔵 SAMSUNG Galaxy (все до S26 Ultra)",
    "xiaomi": "🟠 XIAOMI (все до 18 Pro Max + Redmi/POCO)", "mi": "🟠 XIAOMI (все до 18 Pro Max + Redmi/POCO)",
}


def main():
    ap = argparse.ArgumentParser(description="Парсер Avito: телефоны, средняя цена, лучшие предложения")
    ap.add_argument("--model", "-m", help="Конкретная модель, напр. \"iPhone 15 Pro Max\"")
    ap.add_argument("--brand", "-b", help="Бренд целиком: iphone|pixel|samsung|xiaomi|honor|oneplus|...")
    ap.add_argument("--category", "-c", help="Точное имя категории из меню")
    ap.add_argument("--count", "-n", type=int, default=50, help="Сколько объявлений сканировать (default 50)")
    ap.add_argument("--location", default="moskva", help="Город (moskva|spb|ekaterinburg|… пусто=россия)")
    ap.add_argument("--json", dest="json_out", help="Сохранить результат в JSON")
    ap.add_argument("--save-html", action="store_true", help="Сохранять полученный HTML для отладки")
    ap.add_argument("--show-all", action="store_true", help="Показать все объявления")
    ap.add_argument("--quiet", "-q", action="store_true", help="Без подробного вывода")
    ap.add_argument("--tui", action="store_true", help="Force textual TUI")
    ap.add_argument("--cli", action="store_true", help="Без меню: сразу печать (нужен --model/--brand)")
    args = ap.parse_args()

    # ---- режим: конкретная модель / бренд ----
    targets: list[tuple[str, str]] = []  # (категория, модель)
    if args.model:
        targets = [("CLI", args.model)]
    elif args.brand:
        menu = build_menu()
        key = args.brand.lower()
        if key in BRAND_ALIASES:
            cat = BRAND_ALIASES[key]
            targets = [(cat, m) for m in menu[cat]]
        else:
            for cat, models in menu.items():
                if key in cat.lower():
                    targets = [(cat, m) for m in models]
                    break
        if not targets:
            print(RED(f"Бренд «{args.brand}» не найден."))
            sys.exit(1)
    elif args.category:
        menu = build_menu()
        if args.category not in menu:
            print(RED("Категории: " + ", ".join(menu)))
            sys.exit(1)
        targets = [(args.category, m) for m in menu[args.category]]

    # ---- интерактивный запуск ----
    if not targets:
        print_banner()
        use_tui = args.tui
        if not use_tui and not args.cli:
            try:
                import textual  # noqa: F401
                if sys.stdout.isatty():
                    use_tui = True
            except ImportError:
                pass
        if use_tui:
            try:
                textual_app()
                return
            except Exception as e:
                print(YELLOW(f"TUI недоступен ({e}), переключаюсь на текстовое меню…"))
        choice = simple_menu()
        if not choice:
            print("Выход.")
            return
        targets = [choice]

    # ---- сканирование ----
    print_banner() if not args.quiet else None
    results: list[ScanResult] = []
    for cat, model in targets:
        query = normalize_query(model)
        if not args.quiet:
            print(BOLD(f"\n→ Сканирую «{model}» (запрос: {query}) — до {args.count} объявлений…"))
        res = scan_model(model, query, per_page=args.count, location=args.location,
                         verbose=not args.quiet)
        results.append(res)
        print_report(res, args.count, show_all=args.show_all)
        if args.save_html:
            pass  # html сохраняется внутри fetcher при --debug
        if len(targets) > 1:
            time.sleep(1.2)  # вежливость к сайту

    # итог по бренду
    if len(results) > 1:
        print(BOLD("\n═══ ИТОГОВАЯ ТАБЛИЦА ПО БРЕНДУ ═══"))
        rows = []
        for r in results:
            avg = r.avg_price()
            ch = r.cheapest_good(1)
            rows.append((r.model, avg, ch[0].price if ch else None,
                         ch[0].url if ch else ""))
        rows.sort(key=lambda x: (x[1] is None, x[1]))
        for model, avg, best, url in rows:
            print(f"  {model:<28} сред: {fmt_price(avg):>12}  мин(хор): {fmt_price(best):>12}")
            if url:
                print(f"  {'':<28} {CYAN(url)}")

    if args.json_out:
        data = [result_to_dict(r) for r in results]
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(GREEN(f"\n💾 JSON сохранён: {args.json_out}"))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nПрервано пользователем.")
        sys.exit(130)
