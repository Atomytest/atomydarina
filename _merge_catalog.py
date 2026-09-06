# -*- coding: utf-8 -*-
import json
import re
from pathlib import Path

ROOT = Path(r"C:\Users\aomar\Desktop\Atomy")
OCR = ROOT / "_ocr"

KEEP = [
    "id", "title", "promo", "favorites", "priceGuest", "priceMember",
    "pv", "image", "image2", "category", "categoryName",
]

raw = json.loads((ROOT / "data" / "products.json").read_text(encoding="utf-8"))
# keep original shop items only
shop = []
for p in raw:
    if p.get("section") == "korea":
        continue
    shop.append({k: p.get(k) for k in KEEP})


def catalog_page(pdf_n: int) -> int:
    return pdf_n - 2


def normalize(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKC", s or "")
    s = s.lower().replace("ё", "е")
    s = s.replace("ивининг", "ивнинг").replace("селлактив", "селл актив")
    s = s.replace("посуды+", "посуды")
    s = s.replace("витамин c", "витамин с")
    s = s.replace("омега 3", "омега 3")
    s = re.sub(r"[^a-zа-я0-9+#]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


STOP = {
    "атоми", "atomy", "набор", "шт", "мл", "гр", "для", "и", "с", "из", "по",
    "на", "в", "к", "от", "the", "of", "цвет", "размер",
}


KEEP_SHORT = {"c", "bb", "b", "d3", "k2", "rtg", "o2"}


def tokens(title: str):
    words = []
    for w in normalize(title).split():
        if w in STOP:
            continue
        if len(w) > 2 or w in KEEP_SHORT:
            words.append(w)
    return words


def phrase(title: str) -> str:
    t = normalize(re.sub(r"^атоми\s+", "", title, flags=re.I))
    t = re.sub(r"\b(набор|шт|мл|гр)\b", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def is_toc(text: str) -> bool:
    t = text.lower()
    if "оглавление" in t:
        return True
    # lots of dotted leaders / page numbers
    if t.count(" .") + t.count(" _") > 25:
        return True
    return False


def extract_fields(text: str, title_tokens) -> dict:
    sku = None
    m = re.search(r"номер продукта\s*([0-9]{4,6})", text, re.I)
    if m:
        sku = m.group(1)
    volume = None
    m = re.search(r"(?:объем|вес)[:\s]+(.{8,90})", text, re.I)
    if m:
        volume = re.sub(r"\s+", " ", m.group(1))
        volume = re.split(r"\d[\d\s]{0,8}\s*(RUB|kZT|KZT|kGS|PV)", volume, maxsplit=1)[0]
        volume = volume.strip(" .,/")
    usage = None
    m = re.search(
        r"((?:способ применения|принимать)[:\s].{8,180})",
        text,
        re.I,
    )
    if m:
        usage = re.sub(r"\s+", " ", m.group(1)).strip(" .")
    composition = None
    m = re.search(r"состав[:\s]+(.{20,550})", text, re.I)
    if m:
        composition = re.sub(r"\s+", " ", m.group(1))
        composition = re.split(
            r"БАД|условия хранения|меры предосторожности|кому ",
            composition,
            maxsplit=1,
            flags=re.I,
        )[0].strip(" .")
    body = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[.!?])\s+", body)
    good = []
    joined_toks = title_tokens[:3]
    for part in parts:
        cyr = len(re.findall(r"[А-Яа-яЁё]", part))
        if cyr < 22 or len(part) < 40:
            continue
        low = part.lower()
        if is_toc(part) or "оглавление" in low:
            continue
        if "бад" in low and "не является" in low:
            continue
        if re.search(r"\b(rub|kzt|kgs)\b", low) and cyr < 40:
            continue
        # prefer sentences that mention the product
        good.append(part.strip())
    # rank sentences that contain a title token
    ranked = sorted(
        good,
        key=lambda s: -sum(1 for t in joined_toks if t in s.lower()),
    )
    desc = " ".join(ranked[:5]).strip()
    if len(desc) > 850:
        desc = desc[:850].rsplit(" ", 1)[0] + "…"
    return {
        "sku": sku,
        "volume": volume if volume and len(volume) < 80 else None,
        "usage": usage,
        "composition": composition or None,
        "description": desc or None,
    }


def parse_pv(text: str):
    ms = re.findall(r"(\d{1,3}(?:\s\d{3}){0,2}|\d{3,5})\s*pv\b", text, re.I)
    vals = []
    for m in ms:
        n = int(re.sub(r"\s", "", m))
        if 200 <= n <= 300000:
            vals.append(n)
    return min(vals) if vals else None


def korea_title(text: str):
    m = re.search(
        r"Атоми\s+([А-Яа-яЁёA-Za-z0-9№#\- ]{3,55}?)\s+(?:Объем|Вес|Номер продукта)",
        text,
    )
    if m:
        t = "Атоми " + re.sub(r"\s+", " ", m.group(1)).strip(" .")
        if 8 < len(t) < 70 and t.count(" ") <= 8:
            return t
    return None


pages = []
for p in sorted(OCR.glob("p*.txt")):
    n = int(re.search(r"\d+", p.name).group())
    text = p.read_text(encoding="utf-8")
    pages.append({
        "pdf": n,
        "page": catalog_page(n),
        "text": text,
        "norm": normalize(text),
        "toc": is_toc(text),
    })

# CIS product pages
cis_pages = [pg for pg in pages if 8 <= pg["page"] <= 133 and not pg["toc"] and pg["pdf"] >= 10]
korea_pages = [pg for pg in pages if 134 <= pg["page"] <= 230 and not pg["toc"]]

unmatched = []
for p in shop:
    toks = tokens(p["title"])
    key = phrase(p["title"])
    best, best_s = None, 0
    for pg in cis_pages:
        if not toks:
            continue
        hits = sum(1 for w in toks if w in pg["norm"])
        s = hits / max(len(toks), 1)
        full = normalize(p["title"])
        if len(full) >= 10 and full in pg["norm"]:
            s += 1.5
        if key and len(key) >= 6 and key in pg["norm"]:
            s += 1.2
        elif key and len(key) >= 8:
            # partial: first 2 meaningful words as phrase
            bits = key.split()[:2]
            if len(" ".join(bits)) >= 6 and " ".join(bits) in pg["norm"]:
                s += 0.35
        if s > best_s:
            best_s, best = s, pg
    ok = best and best_s >= 0.7
    if ok:
        fields = extract_fields(best["text"], toks)
        p["catalogPage"] = best["page"]
        p["section"] = "cis"
        for k, v in fields.items():
            if v:
                p[k] = v
        if fields.get("description") and "оглавление" in fields["description"].lower():
            p.pop("description", None)
    else:
        unmatched.append((p["title"], round(best_s, 2), best["page"] if best else None))

print("shop matched", sum(1 for p in shop if p.get("catalogPage")), "/", len(shop))
print("unmatched", len(unmatched))
for row in unmatched:
    print(" ", row)

korea_items = []
seen = {normalize(p["title"]) for p in shop}
for pg in korea_pages:
    title = korea_title(pg["text"])
    if not title:
        continue
    key = normalize(title)
    if key in seen:
        continue
    toks = tokens(title)
    fields = extract_fields(pg["text"], toks)
    item = {
        "id": None,
        "title": title,
        "promo": None,
        "favorites": 0,
        "priceGuest": None,
        "priceMember": None,
        "pv": parse_pv(pg["text"]),
        "image": f"catalog-thumbs/p{pg['pdf']:03d}.jpg",
        "image2": "",
        "category": "korea",
        "categoryName": "Корейский раздел",
        "catalogPage": pg["page"],
        "section": "korea",
        **{k: v for k, v in fields.items() if v},
    }
    korea_items.append(item)
    seen.add(key)

print("korea", len(korea_items))
for k in korea_items:
    print(" ", k["catalogPage"], k["title"], k.get("sku"), k.get("pv"))

nid = max(p["id"] for p in shop) + 1
for i, k in enumerate(korea_items):
    k["id"] = nid + i
    shop.append(k)

(ROOT / "data" / "products.json").write_text(
    json.dumps(shop, ensure_ascii=False, indent=2), encoding="utf-8"
)
(ROOT / "products.js").write_text(
    "window.PRODUCTS = " + json.dumps(shop, ensure_ascii=False) + ";\n",
    encoding="utf-8",
)
print("total", len(shop))
