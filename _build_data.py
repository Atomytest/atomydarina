import json
import re
import shutil
from collections import Counter
from pathlib import Path

src = Path(r"C:\Users\aomar\Desktop\Atomy\_raw.json")
raw = json.loads(src.read_text(encoding="utf-8"))

# Order matters: first match wins
CATS = [
    ("oral", "Уход за зубами", [
        "зубн", "оралкеар", "орал", "ополаскиватель", "ершик",
        "дентал соник", "насадки",
    ]),
    ("sun", "Солнцезащита", ["солнцезащит"]),
    ("makeup", "Макияж", [
        "тушь", "кушон", "помада", "блеск для губ", "блеск для",
        "пудра",
        "подводк", "тени", "консилер", "румяна", "хайлайтер",
        "бронзер", "бров", "bb", "бб крем", "скульптор",
        "набор кистей", "mood-on",
    ]),
    ("hair", "Волосы", [
        "шампунь", "кондиционер", "скалп", "рут вайтал",
        "масло для волос", "эссенция для волос", "эссенция для кудряв",
        "тритмент", "протеиновая эссенция", "хербал",
    ]),
    ("health", "Здоровье", [
        "витамин", "пробиотик", "омега", "спирулина", "хемохим",
        "нони", "лютеин", "женьшень", "слим боди", "протеин",
        "железо", "халал", "похудение", "хэлси", "банаба",
        "чай пуэр", "здоровье", "аляска", "турмацин",
    ]),
    ("food", "Еда и напитки", [
        "кофе", "рамен", "печенье", "бульдак", "токпок",
        "напиток", "морская капуста", "лапша", "орео",
        "пеперо", "лотте", "милкис", "летс би", "баскин",
    ]),
    ("home", "Дом и быт", [
        "стирал", "стирк", "посуд", "губк", "перчатк", "отбелива",
        "зип", "пленк", "чистящ", "мыло для рук", "пятновывод",
        "кислородн", "листовой порошок", "хозяйствен",
    ]),
    ("body", "Тело и гигиена", [
        "гель для душа", "лосьон для тела", "скраб", "прокладк",
        "крем для рук", "бальзам для рук", "крем для ног",
        "интимн", "мочалка", "серабэби", "ультра рич",
        "колготк", "мыло", "терапия для рук", "лосьон",
    ]),
    ("face", "Уход за лицом", [
        "ивнинг", "ивининг", "гидра", "абсолют", "центелла",
        "фэйм", "акне", "маска", "тонер", "пенка", "пилинг",
        "гидрофильн", "скин бустер", "очищение", "сыворотк",
        "эссенц", "ампул", "патч", "акропасс", "бальзам для губ",
        "крем-мист", "спрей мгновен", "майлд", "снмодан",
        "снемодан", "тоник", "ночная маска", "корректор",
        "снятия макияжа", "увлажнение для мужчин", "суперэнергия",
    ]),
    ("sets", "Наборы", ["набор", "сет "]),
    ("biz", "Бизнес и прочее", [
        "футболка", "сумка", "каталог", "журнал", "сценарий",
        "бизнес-бук", "пакет", "термобутыл", "go sales",
    ]),
]


def parse_money(s):
    if s is None or s == "":
        return None
    t = str(s).replace("\xa0", " ").replace(" ", "").replace(",", ".")
    t = re.sub(r"[^\d.]", "", t)
    if not t:
        return None
    try:
        return int(round(float(t)))
    except ValueError:
        return None


def parse_fav(s):
    if not s:
        return 0
    m = re.search(r"(\d[\d\s]*)", str(s))
    if not m:
        return 0
    return int(re.sub(r"\s", "", m.group(1)))


def promo_and_title(title):
    title = (title or "").replace("\u00a0", " ").strip()
    m = re.match(r"^\[([^\]]+)\]\s*(.*)$", title)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return None, title


def classify(title):
    t = title.lower()
    if t.startswith("сет ") or t.startswith('сет"') or t.startswith("сет «"):
        return "sets", "Наборы"
    for cid, cname, kws in CATS:
        if any(k in t for k in kws):
            return cid, cname
    return "other", "Другое"


products = []
for i, d in enumerate(raw, 1):
    promo, title = promo_and_title(d.get("title"))
    cid, cname = classify(title)
    products.append({
        "id": i,
        "title": title,
        "promo": promo,
        "favorites": parse_fav(d.get("data")),
        "priceGuest": parse_money(d.get("data2")),
        "priceMember": parse_money(d.get("data3")),
        "pv": parse_money(d.get("data4")),
        "image": d.get("image") or "",
        "image2": d.get("image2") or "",
        "category": cid,
        "categoryName": cname,
    })

print(dict(Counter(p["categoryName"] for p in products)))
print("no member price", sum(1 for p in products if not p["priceMember"]))

out_dir = Path(r"C:\Users\aomar\Desktop\Atomy")
(out_dir / "data").mkdir(exist_ok=True)
(out_dir / "data" / "products.json").write_text(
    json.dumps(products, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

logo_src = Path(
    r"C:\Users\aomar\.cursor\projects\c-Users-aomar-Desktop-Atomy\assets"
    r"\c__Users_aomar_AppData_Roaming_Cursor_User_workspaceStorage_"
    r"754cc3d99abff83bc8bfa08c8e9db32e_images_sub0107_slogan-e9305035-d090-44cb-94c4-a6477a774086.png"
)
# find logo
assets = Path(r"C:\Users\aomar\.cursor\projects\c-Users-aomar-Desktop-Atomy\assets")
if assets.exists():
    for p in assets.glob("*.png"):
        dest = out_dir / "logo.png"
        shutil.copy(p, dest)
        print("copied logo", p.name, "->", dest)
        break

js_path = out_dir / "products.js"
js_path.write_text(
    "window.PRODUCTS = " + json.dumps(products, ensure_ascii=False) + ";\n",
    encoding="utf-8",
)
print("saved", len(products))
