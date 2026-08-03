# -*- coding: utf-8 -*-
"""Переносит подобранные картинки из static/img/credits.json в content.py.

Перезаписывает блоки _SONG_IMG и _CHAR_IMG в конце content.py — руками их
править не нужно. Подписи чистятся от служебной разметки Wikidata.

Запуск:  python3 tools/apply_images.py
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_images import tidy  # noqa: E402  — общая чистка подписей

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "static", "img", "credits.json")
CONTENT = os.path.join(ROOT, "content.py")


def clean_credit(credit):
    """Чистит уже записанную подпись: убирает QS-хвосты в каждой её части."""
    parts = [tidy(p) for p in credit.replace(". Общественное достояние.", "").split(" · ")]
    parts = [p for p in parts if p]
    seen, uniq = set(), []
    for p in parts:
        if p.lower() not in seen:
            seen.add(p.lower())
            uniq.append(p)
    return " · ".join(uniq) + ". Общественное достояние."


def py_str(s):
    return '"%s"' % s.replace("\\", "\\\\").replace('"', "'")


def main():
    with open(MANIFEST, encoding="utf-8") as f:
        man = json.load(f)

    songs = man.get("songs", {})
    chars = man.get("chars", {})

    song_lines = ["_SONG_IMG = {"]
    for n in sorted(songs, key=int):
        v = songs[n]
        song_lines.append("    %s: (%s,\n        %s),"
                          % (n, py_str(v["file"]), py_str(clean_credit(v["credit"]))))
    song_lines.append("}")

    char_lines = ["_CHAR_IMG = {"]
    for k, v in chars.items():
        char_lines.append("    %s: (%s,\n        %s),"
                          % (py_str(k), py_str(v["file"]), py_str(clean_credit(v["credit"]))))
    char_lines.append("}")

    with open(CONTENT, encoding="utf-8") as f:
        src = f.read()

    src, n1 = re.subn(r"_SONG_IMG = \{.*?\n\}", "\n".join(song_lines), src, flags=re.S)
    src, n2 = re.subn(r"_CHAR_IMG = \{.*?\n\}", "\n".join(char_lines), src, flags=re.S)
    if not (n1 and n2):
        raise SystemExit("не нашли блоки _SONG_IMG / _CHAR_IMG в content.py")

    with open(CONTENT, "w", encoding="utf-8") as f:
        f.write(src)
    print("Вписано в content.py: %d песней, %d персонажей" % (len(songs), len(chars)))


if __name__ == "__main__":
    main()
