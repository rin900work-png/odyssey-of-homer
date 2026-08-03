# -*- coding: utf-8 -*-
"""Подбирает иллюстрации к песням и персонажам «Илиады» на Wikimedia Commons.

Берёт только файлы с лицензией «общественное достояние», скачивает уменьшенную
копию (макс. 1400 px) в static/img/ и печатает готовые строки для _SONG_IMG /
_CHAR_IMG в content.py.

Запуск:  python3 tools/fetch_images.py
"""

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "static", "img")
API = "https://commons.wikimedia.org/w/api.php"
UA = "IliadStaticSite/1.0 (personal offline reading site; python-urllib)"
WIDTH = 1400

# Что искать: ключ -> список запросов (пробуем по очереди, берём первый годный файл).
SONG_QUERIES = {
    1: ['Drolling Wrath of Achilles', 'David Anger of Achilles', 'Tiepolo Achilles Agamemnon'],
    2: ['Flaxman Iliad Greek ships', 'Homer catalogue of ships', 'Flaxman Iliad assembly'],
    3: ['Moreau Helen on the walls of Troy', 'David Paris and Helen', 'Menelaus Paris duel vase'],
    4: ['Pandarus shoots Menelaus', 'Wounded Menelaus Machaon', 'Flaxman Iliad Agamemnon army'],
    5: ['Ingres Venus wounded by Diomedes', 'Diomedes Ares Flaxman', 'Diomedes battle Aeneas'],
    6: ['Kauffmann Hector Andromache', 'Hector taking leave of Andromache', 'Farewell of Hector'],
    7: ['Hector and Ajax duel', 'Flaxman Ajax Hector combat', 'Ajax Hector exchange gifts'],
    8: ['Jupiter on Mount Ida golden scales', 'Flaxman Iliad Jupiter scales', 'Zeus Ida Iliad'],
    9: ['Ingres Ambassadors of Agamemnon', 'Embassy to Achilles', 'Achilles lyre embassy'],
    10: ['Dolon Odysseus Diomedes', 'Rhesus horses Diomedes', 'Flaxman Iliad Dolon'],
    11: ['Flaxman Iliad Agamemnon battle', 'Agamemnon wounded Iliad', 'Nestor Machaon chariot'],
    12: ['Sarpedon storming the wall', 'Hector breaking the gate Iliad', 'Flaxman Iliad wall battle'],
    13: ['Neptune Poseidon Iliad battle ships', 'Idomeneus Iliad', 'Flaxman Iliad battle ships'],
    14: ['Barry Jupiter and Juno on Mount Ida', 'Juno seduces Jupiter', 'Romano Jupiter Juno Ida'],
    15: ['Apollo aegis Iliad ships', 'Ajax defends the ships', 'Hector fire ships Iliad'],
    16: ['Fuseli Sleep and Death Sarpedon', 'Death of Sarpedon vase Euphronios',
         'Death of Patroclus Iliad'],
    17: ['Fight over the body of Patroclus', 'Menelaus carrying body of Patroclus',
         'Menelaus Patroclus statue'],
    18: ['Van Dyck Thetis receiving the armour of Achilles', 'Shield of Achilles Flaxman',
         'Vulcan forging armour Achilles'],
    19: ['Benjamin West Thetis bringing armour to Achilles', 'Achilles reconciliation Agamemnon',
         'Thetis armour Achilles painting'],
    20: ['Battle of the gods Iliad', 'Flaxman Iliad gods battle', 'Aeneas Achilles combat'],
    21: ['Achilles fighting the river Scamander', 'Achilles Scamander Rubens',
         'Flaxman Iliad Scamander'],
    22: ['Matsch Triumph of Achilles', 'Achilles dragging the body of Hector',
         'Rubens death of Hector'],
    23: ['David Funeral games of Patroclus', 'Funeral of Patroclus', 'Flaxman Iliad funeral games'],
    24: ['Ivanov Priam asking Achilles for the body of Hector', 'Priam pleading with Achilles',
         'Ransom of Hector'],
}

CHAR_QUERIES = {
    "Ахиллес": ['Achilles Thetis Styx painting', 'Wounded Achilles statue', 'Achilles Skyros'],
    "Гектор": ['Hector reproaching Paris', 'Hector statue Louvre', 'Hector Iliad painting'],
    "Агамемнон": ['Agamemnon painting', 'Mask of Agamemnon', 'Sacrifice of Iphigenia Agamemnon'],
    "Патрокл": ['David Patroclus', 'Patroclus statue', 'Achilles mourning Patroclus'],
    "Приам": ['Priam painting', 'Priam Achilles Ivanov', 'Death of Priam'],
    "Елена": ['De Morgan Helen of Troy', 'Helen of Troy painting', 'Abduction of Helen'],
    "Андромаха": ['David Andromache mourning Hector', 'Andromache painting', 'Andromache Astyanax'],
    "Диомед, Аяксы, Одиссей, Нестор": ['Ajax Odysseus vase', 'Nestor Iliad', 'Diomedes statue'],
    "Зевс": ['Ingres Jupiter and Thetis', 'Zeus statue Olympia', 'Jupiter painting'],
    "Гера, Афина, Посейдон": ['Athena Parthenos', 'Hera Juno painting', 'Poseidon Neptune painting'],
    "Аполлон, Афродита, Арес": ['Apollo Belvedere', 'Venus de Milo', 'Ares Mars painting'],
    "Фетида": ['Thetis Iliad painting', 'Thetis nereid', 'Thetis Vulcan armour'],
}


PAUSE = 2.0        # пауза между любыми обращениями к Wikimedia
MAX_TRIES = 5      # попыток при HTTP 429


def _get(url, timeout=90):
    """GET с уважением к лимитам Wikimedia: пауза + экспоненциальный backoff на 429."""
    delay = 20
    for attempt in range(MAX_TRIES):
        time.sleep(PAUSE)
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == MAX_TRIES - 1:
                raise
            print("      429 — ждём %d с…" % delay)
            time.sleep(delay)
            delay *= 2
    raise RuntimeError("недостижимо")


def api(params):
    params = dict(params, format="json")
    url = API + "?" + urllib.parse.urlencode(params)
    return json.loads(_get(url, timeout=60).decode("utf-8"))


def strip_html(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = s.replace("&amp;", "&").replace("&nbsp;", " ").replace("&quot;", '"')
    return re.sub(r"\s+", " ", s).strip()


def is_public_domain(meta):
    lic = (meta.get("LicenseShortName", {}).get("value") or "").lower()
    usage = (meta.get("UsageTerms", {}).get("value") or "").lower()
    blob = lic + " " + usage
    if "public domain" in blob or blob.strip() in ("pd", "pd-art"):
        return True
    # CC0 тоже годится — свободнее некуда
    return "cc0" in blob


def search(query, limit=12):
    data = api({
        "action": "query", "generator": "search", "gsrsearch": query,
        "gsrnamespace": 6, "gsrlimit": limit,
        "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": WIDTH,
    })
    pages = (data.get("query") or {}).get("pages") or {}
    out = []
    for p in pages.values():
        ii = (p.get("imageinfo") or [{}])[0]
        title = p.get("title", "")
        if not re.search(r"\.(jpg|jpeg|png)$", title, re.I):
            continue
        meta = ii.get("extmetadata") or {}
        if not is_public_domain(meta):
            continue
        if (ii.get("width") or 0) < 700:
            continue
        out.append({
            "title": title,
            "url": ii.get("thumburl") or ii.get("url"),
            "artist": strip_html(meta.get("Artist", {}).get("value")),
            "name": strip_html(meta.get("ObjectName", {}).get("value")) or
                    strip_html(title[5:].rsplit(".", 1)[0]),
            "date": strip_html(meta.get("DateTimeOriginal", {}).get("value")),
            "index": p.get("index", 999),
        })
    out.sort(key=lambda d: d["index"])
    return out


def tidy(s):
    """Убирает служебные хвосты Wikidata из полей Commons.

    В extmetadata часто попадает structured-разметка вида
    «Название title QS:P1476,en:"Название" label QS:Len,"Название"» — режем по ней.
    """
    s = re.sub(r"\s*(title|label)\s+QS:.*$", "", s or "", flags=re.I | re.S)
    s = re.sub(r"\s*\bQS:[^\s]*", "", s)
    s = re.sub(r"^\s*(Author|Illustrator|Artist)\s*:\s*", "", s, flags=re.I)
    return re.sub(r"\s+", " ", s).strip(" ,;:")


def credit_line(hit):
    artist = tidy(hit["artist"])
    artist = re.sub(r"\s*\(.*?\)\s*", " ", artist).strip(" ,")
    # «Author: X Illustrator: Y» → берём того, кто рисовал
    m = re.search(r"Illustrator\s*:\s*(.+)$", hit["artist"] or "", re.I)
    if m:
        artist = tidy(m.group(1))
    if len(artist) > 60:
        artist = artist[:60].rsplit(" ", 1)[0]
    name = tidy(hit["name"])
    if len(name) > 90:
        name = name[:90].rsplit(" ", 1)[0] + "…"
    date = re.sub(r"[^0-9]", "", (hit["date"] or ""))[:4]
    parts = [p for p in (artist, name, date) if p]
    return " · ".join(parts) + ". Общественное достояние."


def download(url, dest):
    data = _get(url, timeout=180)
    with open(dest, "wb") as f:
        f.write(data)
    return len(data)


def load_manifest():
    """Уже подобранные картинки: позволяет докачивать после обрыва, не начиная заново."""
    path = os.path.join(IMG, "credits.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {"songs": {}, "chars": {}}


def save_manifest(man):
    os.makedirs(IMG, exist_ok=True)
    with open(os.path.join(IMG, "credits.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=2, sort_keys=True)


def run(queries, keyfmt, bucket, man):
    os.makedirs(IMG, exist_ok=True)
    store = man[bucket]
    for key, variants in queries.items():
        fname = keyfmt(key) + ".jpg"
        if str(key) in store and os.path.exists(os.path.join(IMG, fname)):
            print("%-30s уже есть — пропускаем" % str(key))
            continue
        hit = None
        for q in variants:
            try:
                hits = search(q)
            except Exception as exc:
                print("  ! ошибка поиска %r: %s" % (q, exc))
                hits = []
            if hits:
                hit = hits[0]
                break
        if not hit:
            print("%-30s — не нашли PD-картинку" % str(key))
            continue
        try:
            size = download(hit["url"], os.path.join(IMG, fname))
        except Exception as exc:
            print("%-30s — не скачалось: %s" % (str(key), exc))
            continue
        store[str(key)] = {"file": fname, "credit": credit_line(hit), "source": hit["title"]}
        save_manifest(man)     # пишем сразу, чтобы обрыв не стоил уже сделанного
        print("%-30s %-28s %6d КБ  %s" % (str(key), fname, size // 1024, hit["title"]))
    return store


def main():
    man = load_manifest()
    print("=== Песни ===")
    songs = run(SONG_QUERIES, lambda n: "song-%02d" % n, "songs", man)
    print("\n=== Персонажи ===")
    chars = run(CHAR_QUERIES, lambda k: "char-%02d" % (list(CHAR_QUERIES).index(k) + 1),
                "chars", man)

    print("\n\n# ---- вставить в content.py ----")
    print("_SONG_IMG = {")
    for n in sorted(songs, key=int):
        v = songs[n]
        print('    %s: ("%s", "%s"),' % (n, v["file"], v["credit"].replace('"', "'")))
    print("}\n")
    print("_CHAR_IMG = {")
    for k, v in chars.items():
        print('    "%s": ("%s", "%s"),' % (k, v["file"], v["credit"].replace('"', "'")))
    print("}")


if __name__ == "__main__":
    main()
