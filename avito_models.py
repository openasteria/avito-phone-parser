"""
Справочник моделей телефонов для парсера Авито.

Покрыты:
  - Apple iPhone     — все вплоть до iPhone 18 Pro Max
  - Google Pixel     — все вплоть до Pixel 11 Pro XL
  - Samsung Galaxy   — все вплоть до Galaxy S26 Ultra
  - Xiaomi           — все вплоть до Xiaomi 18 Pro Max
  - Другие бренды    — последние модели (Honor, OnePlus, Realme, Motorola,
                       Nothing, Sony, ASUS, Vivo, Oppo, Tecno, Infinix, Nokia...)
"""

# ---------------------------------------------------------------------------
# Основные категории ("до последней модели включительно")
# ---------------------------------------------------------------------------

IPHONE = [
    # Старые (встречаются на вторичке)
    "iPhone SE", "iPhone SE 2020", "iPhone SE 2022",
    "iPhone 6", "iPhone 6 Plus", "iPhone 6s", "iPhone 6s Plus",
    "iPhone 7", "iPhone 7 Plus",
    "iPhone 8", "iPhone 8 Plus",
    "iPhone X", "iPhone XR", "iPhone XS", "iPhone XS Max",
    "iPhone 11", "iPhone 11 Pro", "iPhone 11 Pro Max",
    "iPhone 12 mini", "iPhone 12", "iPhone 12 Pro", "iPhone 12 Pro Max",
    "iPhone 13 mini", "iPhone 13", "iPhone 13 Pro", "iPhone 13 Pro Max",
    "iPhone 14", "iPhone 14 Plus", "iPhone 14 Pro", "iPhone 14 Pro Max",
    "iPhone 15", "iPhone 15 Plus", "iPhone 15 Pro", "iPhone 15 Pro Max",
    "iPhone 16", "iPhone 16 Plus", "iPhone 16 Pro", "iPhone 16 Pro Max",
    "iPhone 16e",
    "iPhone 17", "iPhone 17 Pro", "iPhone 17 Pro Max", "iPhone 17e",
    "iPhone Air",
    "iPhone 18", "iPhone 18 Pro", "iPhone 18 Pro Max",
]

PIXEL = [
    "Pixel", "Pixel XL",
    "Pixel 2", "Pixel 2 XL",
    "Pixel 3", "Pixel 3 XL", "Pixel 3a", "Pixel 3a XL",
    "Pixel 4", "Pixel 4 XL", "Pixel 4a", "Pixel 4a 5G",
    "Pixel 5", "Pixel 5a",
    "Pixel 6", "Pixel 6 Pro", "Pixel 6a",
    "Pixel 7", "Pixel 7 Pro", "Pixel 7a",
    "Pixel 8", "Pixel 8 Pro", "Pixel Fold", "Pixel 8a",
    "Pixel 9", "Pixel 9 Pro", "Pixel 9 Pro XL", "Pixel 9 Pro Fold", "Pixel 9a",
    "Pixel 10", "Pixel 10 Pro", "Pixel 10 Pro XL", "Pixel 10 Pro Fold", "Pixel 10a",
    "Pixel 11", "Pixel 11 Pro", "Pixel 11 Pro XL", "Pixel 11 Pro Fold",
]

SAMSUNG = [
    # Легенды прошлых лет
    "Galaxy S III", "Galaxy S4", "Galaxy S5", "Galaxy S6", "Galaxy S6 Edge",
    "Galaxy S7", "Galaxy S7 Edge", "Galaxy S8", "Galaxy S8+",
    "Galaxy S9", "Galaxy S9+", "Galaxy S10", "Galaxy S10+", "Galaxy S10e",
    "Galaxy Note 8", "Galaxy Note 9", "Galaxy Note 10", "Galaxy Note 10+", "Galaxy Note 20", "Galaxy Note 20 Ultra",
    # A-серия популярна на вторичке
    "Galaxy A50", "Galaxy A51", "Galaxy A52", "Galaxy A53", "Galaxy A54", "Galaxy A55",
    "Galaxy A34", "Galaxy A35", "Galaxy A36",
    "Galaxy A13", "Galaxy A14", "Galaxy A15", "Galaxy A16",
    "Galaxy A73", "Galaxy A24", "Galaxy A25", "Galaxy A26",
    # S-серия
    "Galaxy S20", "Galaxy S20+", "Galaxy S20 Ultra", "Galaxy S20 FE",
    "Galaxy S21", "Galaxy S21+", "Galaxy S21 Ultra", "Galaxy S21 FE",
    "Galaxy S22", "Galaxy S22+", "Galaxy S22 Ultra",
    "Galaxy S23", "Galaxy S23+", "Galaxy S23 Ultra", "Galaxy S23 FE",
    "Galaxy S24", "Galaxy S24+", "Galaxy S24 Ultra", "Galaxy S24 FE",
    "Galaxy S25", "Galaxy S25+", "Galaxy S25 Ultra", "Galaxy S25 Edge",
    "Galaxy S26", "Galaxy S26+", "Galaxy S26 Ultra",
    # Складни
    "Galaxy Z Fold3", "Galaxy Z Fold4", "Galaxy Z Fold5", "Galaxy Z Fold6", "Galaxy Z Fold7",
    "Galaxy Z Flip3", "Galaxy Z Flip4", "Galaxy Z Flip5", "Galaxy Z Flip6", "Galaxy Z Flip7",
]

XIAOMI = [
    "Mi 9", "Mi 9T", "Mi 10", "Mi 10T", "Mi 11", "Mi 11 Lite", "Mi 11 Ultra",
    "Xiaomi 12", "Xiaomi 12 Pro", "Xiaomi 12S Ultra", "Xiaomi 12T Pro", "Xiaomi 12 Lite",
    "Xiaomi 13", "Xiaomi 13 Pro", "Xiaomi 13 Lite", "Xiaomi 13T", "Xiaomi 13T Pro", "Xiaomi 13 Ultra",
    "Xiaomi 14", "Xiaomi 14 Pro", "Xiaomi 14T", "Xiaomi 14T Pro", "Xiaomi 14 Ultra",
    "Xiaomi 15", "Xiaomi 15 Pro", "Xiaomi 15 Ultra", "Xiaomi 15T", "Xiaomi 15T Pro",
    "Xiaomi 16", "Xiaomi 16 Pro", "Xiaomi 16 Ultra", "Xiaomi 16T", "Xiaomi 16T Pro",
    "Xiaomi 17", "Xiaomi 17 Pro", "Xiaomi 17 Ultra", "Xiaomi 17 Pro Max",
    "Xiaomi 18", "Xiaomi 18 Pro", "Xiaomi 18 Pro Max",
    # Бюджетки
    "Redmi Note 10", "Redmi Note 11", "Redmi Note 12", "Redmi Note 13",
    "Redmi Note 14", "Redmi Note 15", "Redmi Note 16",
    "Redmi 10", "Redmi 12", "Redmi 13", "Redmi 14",
    "POCO X5 Pro", "POCO X6 Pro", "POCO X7 Pro", "POCO F5", "POCO F6", "POCO F7 Ultra",
]

OTHER = {
    "HONOR": [
        "Honor 20", "Honor 30", "Honor 50", "Honor 60", "Honor 70", "Honor 80", "Honor 90",
        "Honor 200", "Honor 300", "Honor 400",
        "Honor Magic4 Pro", "Honor Magic5 Pro", "Honor Magic6 Pro", "Honor Magic7 Pro", "Honor Magic8 Pro",
        "Honor X9b", "Honor X9c",
    ],
    "ONEPLUS": [
        "OnePlus 7 Pro", "OnePlus 8", "OnePlus 8 Pro", "OnePlus 9", "OnePlus 9 Pro",
        "OnePlus 10 Pro", "OnePlus 11", "OnePlus 12", "OnePlus 13", "OnePlus 14",
        "OnePlus Nord 3", "OnePlus Nord 4", "OnePlus Nord CE4",
    ],
    "REALME": [
        "Realme GT 2 Pro", "Realme GT Neo 3", "Realme GT 5", "Realme GT 6", "Realme GT 7 Pro",
        "Realme 11", "Realme 12 Pro", "Realme 13 Pro", "Realme 14 Pro",
    ],
    "MOTOROLA": [
        "Moto G60", "Moto G71", "Moto G82", "Moto G100", "Moto G200",
        "Edge 30", "Edge 40", "Edge 50 Ultra", "Edge 60",
        "Razr 40", "Razr 50 Ultra", "Razr 60",
    ],
    "NOTHING": ["Phone (1)", "Phone (2)", "Phone (2a)", "Phone (3a)", "Phone (3)"],
    "SONY": [
        "Xperia 1 IV", "Xperia 1 V", "Xperia 1 VI",
        "Xperia 5 IV", "Xperia 5 V", "Xperia 10 V", "Xperia 10 VI",
    ],
    "ASUS": [
        "Zenfone 9", "Zenfone 10", "Zenfone 11 Ultra",
        "ROG Phone 6", "ROG Phone 7", "ROG Phone 8 Pro", "ROG Phone 9 Pro",
    ],
    "VIVO": ["Vivo X80 Pro", "Vivo X90 Pro", "Vivo X100 Pro", "Vivo X200 Pro", "Vivo X300 Pro"],
    "OPPO": ["Oppo Find X3 Pro", "Oppo Find X5 Pro", "Oppo Find X6 Pro", "Oppo Find X7 Ultra", "Oppo Find X8 Pro", "Oppo Reno 12", "Oppo Reno 14"],
    "TECNO": ["Tecno Camon 20", "Tecno Camon 30", "Tecno Phantom V Fold", "Tecno Spark 20 Pro"],
    "INFINIX": ["Infinix Note 30", "Infinix Note 40", "Infinix Zero 30", "Infinix GT 20 Pro"],
    "NUBIA": ["Nubia Z50 Ultra", "Nubia Z60 Ultra", "Nubia Z70 Ultra", "Nubia Z80 Ultra"],
    "GOOGLE_OTHER": ["Nexus 5X", "Nexus 6P"],
}

# ---------------------------------------------------------------------------
# Меню: категория -> список отображаемых позиций
# ---------------------------------------------------------------------------

def build_menu() -> dict[str, list[str]]:
    """Возвращает меню вида { '🍎 APPLE iPhone': ['iPhone 18 Pro Max', ...] }"""
    menu: dict[str, list[str]] = {}
    menu["🍎 APPLE iPhone (все до 18 Pro Max)"] = list(reversed(IPHONE))
    menu["🟢 GOOGLE Pixel (все до 11 Pro XL)"] = list(reversed(PIXEL))
    menu["🔵 SAMSUNG Galaxy (все до S26 Ultra)"] = list(reversed(SAMSUNG))
    menu["🟠 XIAOMI (все до 18 Pro Max + Redmi/POCO)"] = list(reversed(XIAOMI))
    for brand, models in OTHER.items():
        label = brand.replace("_OTHER", "")
        menu[f"⚡ ДРУГИЕ · {label}"] = list(reversed(models))
    return menu


def normalize_query(model: str) -> str:
    """Приводит название модели к поисковому запросу Авито."""
    m = model.strip()
    if m.lower().startswith("iphone"):
        return m
    if m.lower().startswith("pixel"):
        return f"Google {m}"
    if m.lower().startswith("galaxy"):
        return f"Samsung {m}"
    if m.lower().startswith(("xiaomi", "mi ", "redmi", "poco")):
        if m.lower().startswith("mi "):
            return f"Xiaomi {m}"
        return m
    if m.lower().startswith(("honor", "oneplus", "realme", "oppo", "vivo",
                             "tecno", "infinix", "nubia", "asus", "sony",
                             "nothing", "moto", "edge", "razr", "xperia",
                             "zenfone", "rog phone", "nexus")):
        return m
    return m
