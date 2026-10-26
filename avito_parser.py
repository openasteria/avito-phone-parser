"""
avito_parser.py — ядро парсера Avito (терминальная утилита для Linux / Kali Linux)

Стратегия обхода защиты Авито (439 / антибот):
  1. Пытаемся получить страницу через requests + свежую cookie-сессию.
  2. Если заблокировано — пробуем мобильный сайт m.avito.ru.
  3. Если и это заблокировано — используем системный curl (другой TLS-fingerprint).
  4. Если всё заблокировано — запускаем headless браузер, если он установлен:
        - curl_cffi (подделка Chrome TLS отпечатка, ставится из requirements)
        - playwright / chromium (apt install chromium)
        - selenium
  5. Парсинг: JSON-ldata (__NEXT_DATA__ / js-registry-search-app), затем
     fallback на HTML-карточки (item-a / ListingItem...).

Дополнительно: поиск объявлений через DuckDuckGo (site:avito.ru) как резервный
источник ссылок, если прямой доступ к сайту полностью закрыт с текущей сети.
"""

from __future__ import annotations

import html
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from urllib.parse import quote_plus, urljoin

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover
    BeautifulSoup = None

AVITO_BASE = "https://www.avito.ru"
CAT_TELEFONY = "/moskva/telefony"  # категория «Телефоны»

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
]

# Слова, по которым объявление считается «не хорошим состоянием»
BAD_CONDITION_WORDS = [
    "разбит", "не работает", "не включается", "не загружается", "утоплен",
    "утоп", "битый", "в ремонте", "на запчасти", "запчасти", "поломан",
    "трещина", "разбился экран", "не сенсор", "мертв", "для запчастей",
    "корпус бит", "сильные царапины", "царапан", "потерян", "крашен",
]
GOOD_CONDITION_WORDS = [
    "отличном", "отличное состояние", "хорошем", "хорошее состояние",
    "идеальном", "как новый", "новое", "без повреждений", "оригинал",
]


@dataclass
class Listing:
    title: str
    price: int | None
    url: str
    location: str = ""
    snippet: str = ""
    condition_score: int = 0          # >0 — признаки хорошего состояния
    bad_condition: bool = False       # найдены слова о плохом состоянии

    @property
    def good(self) -> bool:
        return not self.bad_condition


@dataclass
class ScanResult:
    model: str
    query: str
    listings: list[Listing] = field(default_factory=list)
    total_found: int = 0
    method: str = ""
    error: str = ""

    # ---------------- аналитика ----------------
    def priced(self) -> list[Listing]:
        return [l for l in self.listings if l.price and l.price > 0]

    def avg_price(self) -> float | None:
        p = self.priced()
        if not p:
            return None
        return sum(x.price for x in p) / len(p)

    def median_price(self) -> float | None:
        p = sorted(x.price for x in self.priced())
        if not p:
            return None
        n = len(p)
        mid = n // 2
        if n % 2:
            return float(p[mid])
        return (p[mid - 1] + p[mid]) / 2

    def min_price(self) -> int | None:
        p = self.priced()
        return min(x.price for x in p) if p else None

    def cheapest_good(self, count: int = 5) -> list[Listing]:
        """Самые дешёвые объявления в хорошем состоянии."""
        good = [l for l in self.priced() if l.good]
        good.sort(key=lambda l: (l.price, -l.condition_score))
        return good[:count]

    def below_avg_good(self) -> list[Listing]:
        avg = self.avg_price()
        if avg is None:
            return []
        res = [l for l in self.priced() if l.good and l.price < avg]
        res.sort(key=lambda l: l.price)
        return res


# ---------------------------------------------------------------------------
# HTTP-слой
# ---------------------------------------------------------------------------

class Fetcher:
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.proxy = os.environ.get("AVITO_PROXY") or os.environ.get("HTTPS_PROXY") or None
        self.session = requests.Session() if requests else None
        if self.session and self.proxy:
            self.session.proxies = {"http": self.proxy, "https": self.proxy}
            self.log(f"через прокси: {self.proxy}")
        self._curl_cffi = None
        try:
            from curl_cffi import requests as cffi_requests  # type: ignore
            self._curl_cffi = cffi_requests
        except Exception:
            pass
        self._playwright_page = None
        self.last_method = ""

    def log(self, msg: str):
        if self.verbose:
            print(f"  · {msg}", file=sys.stderr)

    # -------- низкие методы --------
    def _headers(self, referer: str = AVITO_BASE) -> dict:
        ua = random.choice(USER_AGENTS)
        return {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": referer,
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "sec-ch-ua": '"Chromium";v="126", "Google Chrome";v="126", "Not.A/Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
        }

    def _warmup(self):
        """Запрос главной страницы, чтобы получить anti-bot cookies."""
        try:
            if self.session:
                self.session.get(AVITO_BASE, headers=self._headers(), timeout=15)
        except Exception:
            pass

    def fetch_requests(self, url: str) -> str | None:
        if not self.session:
            return None
        try:
            r = self.session.get(url, headers=self._headers(), timeout=20)
            if r.status_code == 200 and len(r.text) > 2000:
                return r.text
            self.log(f"requests: HTTP {r.status_code}")
        except Exception as e:
            self.log(f"requests: {e}")
        return None

    def fetch_curl_cffi(self, url: str) -> str | None:
        if not self._curl_cffi:
            return None
        try:
            r = self._curl_cffi.get(url, impersonate="chrome124", timeout=25,
                                    proxies={"https": self.proxy} if self.proxy else None)
            if r.status_code == 200 and len(r.text) > 2000:
                return r.text
            self.log(f"curl_cffi: HTTP {r.status_code}")
        except Exception as e:
            self.log(f"curl_cffi: {e}")
        return None

    def fetch_curl(self, url: str) -> str | None:
        if not shutil.which("curl"):
            return None
        ua = random.choice(USER_AGENTS)
        cmd = [
            "curl", "-sL", "--compressed", "--max-time", "25",
            "-A", ua,
            "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "-H", "Accept-Language: ru-RU,ru;q=0.9",
            "-b", "/tmp/.avito_cookies.txt", "-c", "/tmp/.avito_cookies.txt",
            url,
        ]
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout
            if out and len(out) > 2000:
                return out
            self.log("curl: пустой/блокированный ответ")
        except Exception as e:
            self.log(f"curl: {e}")
        return None

    def fetch_playwright(self, url: str) -> str | None:
        """Headless Chromium через Python-playwright или бинарь chromium/chrome."""
        # 1) python playwright
        try:
            from playwright.sync_api import sync_playwright  # type: ignore
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
                ctx = browser.new_context(
                    user_agent=random.choice(USER_AGENTS),
                    locale="ru-RU",
                )
                page = ctx.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(3500)
                content = page.content()
                browser.close()
                if content and len(content) > 2000:
                    return content
        except Exception as e:
            self.log(f"playwright(py): {e}")
        # 2) системный chromium headless dump
        for bin_name in ("chromium", "chromium-browser", "google-chrome", "chrome"):
            path = shutil.which(bin_name)
            if not path:
                continue
            try:
                out = subprocess.run(
                    [path, "--headless=new", "--disable-gpu", "--no-sandbox",
                     "--virtual-time-budget=8000", "--dump-dom", url],
                    capture_output=True, text=True, timeout=60,
                ).stdout
                if out and len(out) > 2000:
                    self.log(f"{bin_name} --headless получен HTML")
                    return out
            except Exception as e:
                self.log(f"{bin_name}: {e}")
        return None

    # -------- публичный метод --------
    def fetch(self, url: str) -> str | None:
        self._warmup()
        attempts = [
            ("requests", self.fetch_requests),
            ("curl_cffi(chrome-tls)", self.fetch_curl_cffi),
            ("curl-cli", self.fetch_curl),
            ("m.avito.ru", lambda u: self.fetch_requests(u.replace("www.avito.ru", "m.avito.ru")) or self.fetch_curl(u.replace("www.avito.ru", "m.avito.ru"))),
            ("headless-browser", self.fetch_playwright),
        ]
        for name, fn in attempts:
            html_text = fn(url)
            if html_text and "js-registry-search-app" in html_text or (html_text and "_oid" in html_text and "item-link" in html_text):
                self.last_method = name
                return html_text
            if html_text and len(html_text) > 50000 and "captcha" not in html_text[:3000].lower():
                self.last_method = name
                return html_text
            time.sleep(random.uniform(0.7, 1.6))
        return None


# ---------------------------------------------------------------------------
# Парсинг результатов поиска
# ---------------------------------------------------------------------------

PRICE_NUM_RE = re.compile(r"(\d[\d\s\u2009\u00a0\u202f]*\d|\d)")

def parse_price(text: str) -> int | None:
    if not text:
        return None
    m = PRICE_NUM_RE.search(text)
    if not m:
        return None
    digits = re.sub(r"\D", "", m.group(1))
    if not digits:
        return None
    val = int(digits)
    # защита от мусора: телефоны не стоят дешевле 500 руб. и дороже 5 млн
    if val < 300:
        return None
    if val > 5_000_000:
        return None
    return val


def _abs_url(href: str) -> str:
    href = html.unescape(href.strip())
    if href.startswith("//"):
        href = "https:" + href
    if href.startswith("/"):
        return AVITO_BASE + href
    if href.startswith("http"):
        return href
    return AVITO_BASE + "/" + href


def parse_html_search(html_text: str) -> tuple[list[Listing], int]:
    """Разбирает страницу выдачи Авито: сначала JSON, потом HTML-карточки."""
    listings: list[Listing] = []
    total = 0
    seen: set[str] = set()

    def add(l: Listing):
        key = l.url.split("?")[0]
        if key in seen or not key.rstrip("/").startswith(AVITO_BASE):
            return
        seen.add(key)
        listings.append(l)

    # ---------- 1. JSON в <script type="application/json" id="json-..."> ----------
    if BeautifulSoup:
        soup = BeautifulSoup(html_text, "html.parser")
        for script in soup.find_all("script", type="application/json"):
            raw = script.string or script.get_text() or ""
            if '"items"' not in raw or '"price"' not in raw:
                continue
            try:
                data = json.loads(raw)
            except Exception:
                continue
            stack = [data]
            items_container = None
            while stack:
                obj = stack.pop()
                if isinstance(obj, dict):
                    if "items" in obj and isinstance(obj["items"], list) and obj["items"]:
                        cand = obj["items"]
                        if isinstance(cand[0], dict) and ("location" in cand[0] or "title" in cand[0]):
                            items_container = cand
                            total = obj.get("totalItems") or obj.get("total_items") or 0
                            break
                    stack.extend(obj.values())
                elif isinstance(obj, list):
                    stack.extend(obj)
            if items_container:
                for it in items_container:
                    try:
                        title = _flat_val(it.get("title") or it.get("name") or "")
                        price_meta = it.get("price") or {}
                        price_val = None
                        if isinstance(price_meta, dict):
                            price_val = price_meta.get("value") or parse_price(str(price_meta.get("formatted") or price_meta.get("display")))
                        elif isinstance(price_meta, (int, float)):
                            price_val = int(price_meta)
                        if price_val is None:
                            price_val = parse_price(json.dumps(it, ensure_ascii=False)[:2000])
                        link = it.get("link") or it.get("url") or it.get("uri") or ""
                        if isinstance(link, dict):
                            link = link.get("url") or ""
                        if not link:
                            oid = it.get("_oid") or it.get("id")
                            if oid:
                                link = f"/{oid}"
                        loc = it.get("location") or {}
                        loc_name = _flat_val(loc.get("region") or loc.get("area") or loc.get("zone") or "") if isinstance(loc, dict) else str(loc)
                        desc = _flat_val((it.get("description") or it.get("snippet") or {}).get("html")
                                         or (it.get("description") or it.get("snippet") or {}).get("value")
                                         if isinstance(it.get("description") or it.get("snippet"), dict)
                                         else (it.get("description") or it.get("snippet") or ""))
                        url = _abs_url(str(link))
                        cond_bad, cond_score = rate_condition(title + " " + desc)
                        add(Listing(title=title, price=int(price_val) if price_val else None,
                                    url=url, location=loc_name, snippet=desc[:200],
                                    condition_score=cond_score, bad_condition=cond_bad))
                    except Exception:
                        continue
        if listings:
            return listings, int(total or len(listings))

        # ---------- 2. HTML-карточки ----------
        card_sels = ["div[item-type='ListItem']", "div.js-catalog-item-enum",
                     "article.i-item", "li.seller-listing-item",
                     "div[data-target='search-results.ItemParams']",
                     "div[data-analytics='Search Results;']",
                     "div.c-virtual-list-cells > div"]
        cards: list = []
        for sel in card_sels:
            cards = soup.select(sel)
            if cards:
                break
        if not cards:
            # универсальный эвристический проход по ссылкам на объявления
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if re.search(r"/(mobile|telefony|smartfony)?/?[-\w]*\d{7,}(/|$|\?)", href) or "/-" in href and re.search(r"\d{7,}", href):
                    title = a.get_text(" ", strip=True)
                    if not title or len(title) < 5:
                        parent = a.find_parent(["div", "li", "article"])
                        title = parent.get_text(" ", strip=True)[:200] if parent else title
                    price = parse_price((parent.get_text() if (parent := a.find_parent(["div", "li", "article"])) else "") or "")
                    cond_bad, cond_score = rate_condition(title)
                    add(Listing(title=title[:200], price=price, url=_abs_url(href),
                                condition_score=cond_score, bad_condition=cond_bad))
        else:
            for c in cards:
                a = c.select_one("a[href*='/'], a.js-offer-url, .item-title a") or c.find("a", href=True)
                if not a:
                    continue
                title_el = c.select_one(".item-title, [itemprop='name'], .c-virtual-list-cell-title, a.js-offer-url")
                title = (title_el.get_text(" ", strip=True) if title_el else a.get_text(" ", strip=True))[:200]
                price_el = c.select_one(".item-price, [itemprop='price'], .c-virtual-list-cell-price, div[itemprop='price']")
                price_txt = price_el.get_text(" ", strip=True) if price_el else c.get_text(" ", strip=True)
                price = parse_price(price_txt)
                loc_el = c.select_one(".item-location, .c-virtual-list-cell-address")
                loc = loc_el.get_text(" ", strip=True) if loc_el else ""
                cond_bad, cond_score = rate_condition(title + " " + price_txt[:300])
                add(Listing(title=title, price=price, url=_abs_url(a["href"]),
                            location=loc, condition_score=cond_score, bad_condition=cond_bad))
    return listings, total or len(listings)


def _flat_val(x) -> str:
    """Разворачивает {value:...}/{html:...}/{text:...} и любые словари в чистый текст."""
    if x is None:
        return ""
    if isinstance(x, dict):
        for k in ("value", "html", "text", "display", "formatted"):
            if k in x and isinstance(x[k], (str, int, float)):
                return re.sub(r"<[^>]+>", " ", str(x[k])).strip()
        parts = [_flat_val(v) for v in x.values()]
        return " ".join(p for p in parts if p).strip()
    if isinstance(x, list):
        return " ".join(_flat_val(i) for i in x).strip()
    return re.sub(r"<[^>]+>", " ", str(x)).strip()


def _flat(x) -> str:
    return _flat_val(x)


def rate_condition(text: str) -> tuple[bool, int]:
    t = text.lower()
    bad = any(w in t for w in BAD_CONDITION_WORDS)
    score = sum(2 for w in GOOD_CONDITION_WORDS if w in t)
    if "бу" in t or "оригинал" in t or "комплект" in t:
        score += 1
    return bad, score


# ---------------------------------------------------------------------------
# Резервный канал: DuckDuckGo site:avito.ru
# ---------------------------------------------------------------------------

def se_fallback(query: str, limit: int = 50) -> list[Listing]:
    """Резервный поиск ссылок на объявления Avito через Bing / DuckDuckGo."""
    listings: dict[str, Listing] = {}
    if not (requests and BeautifulSoup):
        return []

    def harvest(html_text: str):
        soup = BeautifulSoup(html_text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            # Bing редирект-ссылки /ck/a?...&u=a1<base64url> — декодируем
            if "/ck/a" in href:
                m2 = re.search(r"[&?]u=(?:a1)?([\w\-]+)", href)
                if not m2:
                    continue
                tok = m2.group(1)
                if tok.startswith("a1"):
                    tok = tok[2:]
                import base64
                try:
                    href = base64.urlsafe_b64decode(tok + "==").decode("utf-8", "ignore")
                except Exception:
                    continue
            m = re.search(r"uddg=([^&]+)", href)
            if m:
                from urllib.parse import unquote
                href = unquote(m.group(1))
            if "avito.ru" not in href or not href.startswith("http"):
                continue
            # только страницы объявлений: slug заканчивается числовым id
            if not re.search(r"\d{6,}", href.split("?")[0]):
                continue
            container = a.find_parent(["li", "div", "article"]) or a
            text = container.get_text(" ", strip=True)
            title = a.get_text(" ", strip=True)[:200]
            if len(title) < 8:
                title = text[:120]
            price = parse_price(text)
            bad, score = rate_condition(title + " " + text[:400])
            key = href.split("?")[0]
            if key not in listings:
                listings[key] = Listing(title=title, price=price, url=key,
                                        snippet=text[:200], condition_score=score,
                                        bad_condition=bad)

    variants = [f'site:avito.ru "{query}"', f"site:avito.ru {query} купить",
                f'avito {query} купить']
    bing_session = requests.Session()
    bing_session.headers.update({"User-Agent": random.choice(USER_AGENTS),
                                 "Accept-Language": "ru-RU,ru;q=0.9"})
    try:
        bing_session.get("https://www.bing.com/?mkt=ru-RU&setlang=ru", timeout=15)  # cookie MUID/SRCH*
    except Exception:
        pass
    for q in variants:
        urls = []
        for bq in (q, q + " купить цена бу"):
            e = quote_plus(bq)
            for pg in ("", "&first=11", "&first=21"):
                urls.append("https://www.bing.com/search?q=" + e + pg + "&mkt=ru-RU&setlang=ru")
        urls += [
            "https://html.duckduckgo.com/html/?q=" + quote_plus(q),
            "https://lite.duckduckgo.com/lite/?q=" + quote_plus(q),
        ]
        for url in urls:
            try:
                if "bing.com" in url:
                    r = bing_session.get(url, timeout=20)
                else:
                    r = requests.get(url, timeout=20,
                                     headers={"User-Agent": random.choice(USER_AGENTS),
                                              "Accept-Language": "ru-RU,ru;q=0.9"})
                if r.status_code in (200, 202) and len(r.text) > 5000:
                    harvest(r.text)
            except Exception:
                pass
            if len(listings) >= limit:
                break
            time.sleep(random.uniform(0.5, 1.2))
        if len(listings) >= max(5, limit // 3):
            break
    return list(listings.values())[:limit]


# совместность со старым именем
ddg_fallback = se_fallback


# ---------------------------------------------------------------------------
# Сканирование
# ---------------------------------------------------------------------------

def scan_model(model: str, query: str, per_page: int = 50, pages: int = 1,
               location: str = "moskva", verbose: bool = True) -> ScanResult:
    """
    Сканирует выдачу Авито по модели.
    per_page — сколько объявлений просканировать (по умолчанию 50, максимум Авито 36/стр → берём несколько страниц).
    """
    result = ScanResult(model=model, query=query)
    fetcher = Fetcher(verbose=verbose)
    all_listings: dict[str, Listing] = {}
    total = 0

    loc_prefix = f"/{location}" if location else ""
    search_path = f"{loc_prefix}/telefony" if location else "/telefony"

    need_pages = max(1, (per_page + 35) // 36) if per_page <= 200 else pages
    urls = []
    for p in range(1, min(need_pages, 6) + 1):
        u = f"{AVITO_BASE}{search_path}?q={quote_plus(query)}&n=36&p={p}&s=102"  # s=102 — по возрастанию цены? оставим дефолт
        urls.append(f"{AVITO_BASE}{search_path}?q={quote_plus(query)}&p={p}")

    got_html = False
    for u in urls:
        html_text = fetcher.fetch(u)
        if not html_text:
            continue
        got_html = True
        lst, tot = parse_html_search(html_text)
        if tot:
            total = tot
        for l in lst:
            key = l.url.split("?")[0]
            if key not in all_listings:
                all_listings[key] = l
        if len(all_listings) >= per_page:
            break
        time.sleep(random.uniform(1.5, 3.0))

    result.method = fetcher.last_method
    if not got_html or not all_listings:
        # резервный канал — DuckDuckGo
        if verbose:
            fetcher.log("Прямой доступ к Авито ограничен → DuckDuckGo site:avito.ru")
        fb = ddg_fallback(query, per_page)
        for l in fb:
            all_listings.setdefault(l.url, l)
        result.method = result.method or "ddg-fallback"

    result.listings = list(all_listings.values())[:per_page]
    result.total_found = total or len(result.listings)
    if not result.listings:
        result.error = ("Не удалось получить объявления: Авито блокирует запросы (антибот 439/капча) "
                        "с этой сети/IP.\n"
                        "   ➤ Решение 1: установите Chromium — `sudo apt install chromium` "
                        "(в Kali часто уже есть) и запустите снова: программа задействует headless-браузер.\n"
                        "   ➤ Решение 2: Tor (Kali: `sudo apt install tor && sudo systemctl start tor`), "
                        "затем: AVITO_PROXY=socks5://127.0.0.1:9050 ./run.sh\n"
                        "   ➤ Решение 3: смените сеть (мобильный интернет / другой IP).")
    return result
