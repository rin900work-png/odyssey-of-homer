# -*- coding: utf-8 -*-
"""Скачивает иллюстрации к «Задаче трёх тел» с Wikimedia Commons — по точным именам файлов.

В отличие от fetch_images.py здесь нет автопоиска: файлы подобраны вручную (реальные
места, приборы и исторические фигуры, которые упоминаются в романе), лицензии —
общественное достояние, CC0, CC BY или CC BY-SA. Подписи для сайта пишутся вручную
в content_three_body.py (_SONG_IMG), здесь только скачивание.

Для глав без реальной «опоры» рисунки делает tools/make_three_body_art.py.

Commons жёстко ограничивает частоту запросов (см. brain/lessons.md): пауза между
запросами и экспоненциальный backoff, уже скачанные файлы пропускаются.
Запуск:  python3 tools/fetch_images_three_body.py
"""

import json
import os
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "static", "img", "three-body")
UA = "OdysseyStaticSite/1.0 (personal reading site; python-urllib)"
WIDTH = 1400
PAUSE = 3

# номер главы -> файл на Commons
FILES = {
    2: "Rachel-Carson.jpg",
    3: "Radio Telescope Effelsberg - 36956392190.jpg",
    5: "Billard Break Shot.jpg",
    7: "Portraits of Famous Men - King Wen of Zhou.jpg",
    9: "WMAP 2012.png",  # сохранено в song-09.jpg (пережато из PNG)
    13: "Arecibo Observatory Aerial.jpg",
    15: "Copernican heliocentrism diagram-2.jpg",
    17: "Qin Terracotta Army, Pit 1 18.jpg",
    19: "Wanda von Debschitz-Kunowski Albert Einstein beim Geigenspiel 1927.jpg",
    20: "Hubble's Best Image of Alpha Centauri A and B (29327410501).jpg",
    22: "Full disk view of the sun June 21, 2010 (4721839258).jpg",
    27: "Oil spill Mobile - Briefings & Oiled Bird cleaning 077 oiled brown pelican before cleaning (5014727141).jpg",
    28: "Supertanker AbQaiq.jpg",
    30: "Views of the LHC tunnel sector 3-4, tirage 2.jpg",
    31: "SS Kentuckian, Panama Canal.jpg",
    34: "CSIRO ScienceImage 7007 Plague locusts on the move.jpg",
}


def get(url):
    delay = 20
    while True:
        time.sleep(PAUSE)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read()
        except Exception as ex:  # 429 и сетевые сбои — ждём и повторяем
            if delay > 320:
                raise
            print("   повтор через %d с (%s)" % (delay, ex), flush=True)
            time.sleep(delay)
            delay *= 2


def main():
    os.makedirs(OUT, exist_ok=True)
    meta = {}
    for n, title in FILES.items():
        ext = ".png" if title.lower().endswith(".png") else ".jpg"
        dest = os.path.join(OUT, "song-%02d%s" % (n, ext))
        if os.path.exists(dest):
            print("%02d уже есть" % n)
            continue
        q = urllib.parse.urlencode({
            "action": "query", "format": "json", "titles": "File:" + title,
            "prop": "imageinfo", "iiprop": "url|extmetadata", "iiurlwidth": WIDTH,
        })
        page = next(iter(json.loads(get("https://commons.wikimedia.org/w/api.php?" + q))
                         ["query"]["pages"].values()))
        info = page["imageinfo"][0]
        url = info.get("thumburl") or info["url"]
        data = get(url)
        with open(dest, "wb") as f:
            f.write(data)
        m = info.get("extmetadata", {})
        meta[n] = {"file": title, "license": m.get("LicenseShortName", {}).get("value"),
                   "page": info.get("descriptionurl")}
        print("%02d ← %s  (%d КБ, %s)" % (n, title, len(data) // 1024, meta[n]["license"]),
              flush=True)
    with open(os.path.join(OUT, "credits.json"), "a", encoding="utf-8") as f:
        f.write(json.dumps(meta, ensure_ascii=False, indent=1) + "\n")


if __name__ == "__main__":
    main()
