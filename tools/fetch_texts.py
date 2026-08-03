# -*- coding: utf-8 -*-
"""Скачивает «Илиаду» в переводе Н. И. Гнедича (1829, общественное достояние)
с Викитеки и чистит вики-разметку. Результат: texts/song-NN.txt, один стих на строку.
"""

import os
import re
import time
import urllib.parse
import urllib.request

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "texts")
BASE = "https://ru.wikisource.org/w/index.php?title=%s&action=raw"
ROOT = "Илиада (Гомер; Гнедич)/"

ORD = [
    "Песнь первая", "Песнь вторая", "Песнь третья", "Песнь четвертая",
    "Песнь пятая", "Песнь шестая", "Песнь седьмая", "Песнь восьмая",
    "Песнь девятая", "Песнь десятая", "Песнь одиннадцатая", "Песнь двенадцатая",
    "Песнь тринадцатая", "Песнь четырнадцатая", "Песнь пятнадцатая",
    "Песнь шестнадцатая", "Песнь семнадцатая", "Песнь восемнадцатая",
    "Песнь девятнадцатая", "Песнь двадцатая", "Песнь двадцать первая",
    "Песнь двадцать вторая", "Песнь двадцать третья", "Песнь двадцать четвертая",
]

UA = "IliadStaticSite/1.0 (personal offline reading site; python-urllib)"


def fetch(title):
    url = BASE % urllib.parse.quote(title, safe="")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def strip_templates(s):
    """Убирает {{...}} с учётом вложенности, сохраняя полезный текст из {{lang|..}} и т.п."""
    out = []
    i = 0
    while i < len(s):
        if s.startswith("{{", i):
            depth = 0
            j = i
            while j < len(s):
                if s.startswith("{{", j):
                    depth += 1
                    j += 2
                elif s.startswith("}}", j):
                    depth -= 1
                    j += 2
                    if depth == 0:
                        break
                else:
                    j += 1
            inner = s[i + 2:j - 2]
            name = inner.split("|", 1)[0].strip().lower()
            if name in ("разрядка", "razr", "lang", "нобр"):
                out.append(inner.split("|")[-1])
            # остальные шаблоны ({{№|N}}, {{Отексте}}, сноски) — выбрасываем
            i = j
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


def clean(raw):
    # тело стихотворения — внутри {{poemx|Заголовок|  ...  |}}
    m = re.search(r"\{\{poemx\s*\|", raw)
    if m:
        start = m.end()
        # пропускаем параметр-заголовок до следующего "|" верхнего уровня
        depth = 0
        k = start
        while k < len(raw):
            if raw.startswith("{{", k):
                depth += 1
                k += 2
            elif raw.startswith("}}", k):
                depth -= 1
                k += 2
            elif raw[k] == "|" and depth == 0:
                break
            else:
                k += 1
        body = raw[k + 1:]
        # до закрывающего "|}}"
        end = body.rfind("|}}")
        if end != -1:
            body = body[:end]
    else:
        body = raw

    body = re.sub(r"<ref[^>]*/>", "", body)
    body = re.sub(r"<ref[^>]*>.*?</ref>", "", body, flags=re.S)
    body = re.sub(r"<br\s*/?>", "\n", body, flags=re.I)
    body = re.sub(r"<[^>]+>", "", body)
    body = strip_templates(body)
    # вики-ссылки: [[цель|текст]] -> текст, [[текст]] -> текст
    body = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", body)
    body = re.sub(r"\[\[([^\]]*)\]\]", r"\1", body)
    body = re.sub(r"'''?", "", body)
    body = body.replace("&nbsp;", " ")

    lines = []
    for ln in body.split("\n"):
        ln = ln.strip()
        if not ln:
            continue
        if ln.startswith(("[[", "{{", "==", "----", "*", "|", "Категория:")):
            continue
        lines.append(ln)
    return lines


def main():
    os.makedirs(OUT, exist_ok=True)
    total = 0
    for n, name in enumerate(ORD, 1):
        raw = fetch(ROOT + name)
        lines = clean(raw)
        path = os.path.join(OUT, "song-%02d.txt" % n)
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        total += len(lines)
        print("песнь %2d: %5d стихов  %s" % (n, len(lines), name))
        time.sleep(1)
    print("Итого стихов: %d" % total)


if __name__ == "__main__":
    main()
