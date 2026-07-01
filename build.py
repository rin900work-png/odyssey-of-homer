# -*- coding: utf-8 -*-
"""Сборка статического сайта-разбора «Одиссеи» в папку docs/.

Без внешних зависимостей — только стандартная библиотека Python 3.
Запуск:  python3 build.py
Результат:  docs/index.html, docs/song-01.html … song-24.html, docs/style.css

Папка называется docs/, потому что так её умеет раздавать GitHub Pages
(Settings → Pages → ветка main, папка /docs). Подойдёт и любой другой
статический хостинг (Cloudflare Pages, Netlify, Vercel) — раздаётся docs/.
"""

import html
import os
import shutil

import content as C

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "docs")
STATIC = os.path.join(ROOT, "static")
TEXTS = os.path.join(ROOT, "texts")

STANZA = 10      # стихов в одной визуальной строфе
NUM_EVERY = 10   # показывать номер стиха каждые N строк


def e(text):
    """Экранирование для HTML."""
    return html.escape(str(text))


def read_verses(n):
    """Читает полный текст песни из texts/song-NN.txt (один стих на строку).

    Возвращает список стихов или None, если файла нет.
    """
    path = os.path.join(TEXTS, "song-%02d.txt" % n)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        verses = [ln.rstrip() for ln in f.read().split("\n")]
    return [v for v in verses if v.strip() != ""]


def render_reader(n):
    """Раскрывающийся блок с полным текстом песни: строфы + нумерация стихов."""
    verses = read_verses(n)
    if not verses:
        return ""

    def verse_html(i, v):
        show = (i == 1) or (i % NUM_EVERY == 0)
        return (
            '        <p class="verse"><span class="vn">%s</span>'
            '<span class="vt">%s</span></p>' % (str(i) if show else "", e(v))
        )

    stanzas = []
    for start in range(0, len(verses), STANZA):
        chunk = verses[start:start + STANZA]
        rows = "\n".join(verse_html(start + 1 + j, v) for j, v in enumerate(chunk))
        stanzas.append('      <div class="stanza">\n%s\n      </div>' % rows)

    return (
        '  <section class="reader">\n'
        '    <details class="reader-details">\n'
        '      <summary class="reader-toggle">\n'
        '        <span class="reader-toggle-label">Читать полный текст песни</span>\n'
        '        <span class="reader-toggle-meta">перевод В. А. Жуковского'
        " · %d стихов</span>\n"
        "      </summary>\n"
        '      <div class="poem">\n%s\n      </div>\n'
        '      <p class="reader-source">Источник: Викитека (ru.wikisource.org), '
        "перевод В. А. Жуковского. Общественное достояние.</p>\n"
        "    </details>\n"
        "  </section>\n"
    ) % (len(verses), "\n".join(stanzas))


def song_href(n):
    return "song-%02d.html" % n


def song_by_n(n):
    for s in C.SONGS:
        if s["n"] == n:
            return s
    raise KeyError(n)


def layout(title, body):
    """Общий каркас страницы."""
    return (
        "<!doctype html>\n"
        '<html lang="ru">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n"
        '<link rel="stylesheet" href="style.css">\n'
        "</head>\n"
        "<body>\n"
        '<header class="site-header">\n'
        '  <a class="brand" href="index.html">Одиссея Гомера</a>\n'
        '  <span class="brand-sub">%s</span>\n'
        "</header>\n"
        '<main class="wrap">\n'
        "%s\n"
        "</main>\n"
        '<footer class="site-footer">\n'
        "  <p>Гомер · «Одиссея» · 24 песни · краткий разбор</p>\n"
        "</footer>\n"
        "</body>\n"
        "</html>\n"
    ) % (e(title), e(C.META["subtitle"]), body)


def build_index():
    m = C.META
    parts_html = []
    for p in C.PARTS:
        items = []
        for n in p["songs"]:
            s = song_by_n(n)
            items.append(
                '    <li><a href="%s"><span class="song-n">%d</span>'
                '<span class="song-t">%s</span></a></li>'
                % (song_href(n), n, e(s["title"]))
            )
        parts_html.append(
            '<section class="part">\n'
            '  <h3 class="part-h"><span class="part-num">%s</span> %s '
            '<span class="part-range">%s</span></h3>\n'
            '  <p class="part-blurb">%s</p>\n'
            '  <ol class="song-list">\n%s\n  </ol>\n'
            "</section>"
            % (e(p["num"]), e(p["name"]), e(p["range"]), e(p["blurb"]), "\n".join(items))
        )

    char_items = []
    for c in C.CHARACTERS:
        if c.get("img"):
            art = (
                '<figure class="char-art"><img src="img/%s" alt="%s" loading="lazy">'
                "<figcaption>%s</figcaption></figure>"
                % (e(c["img"]), e(c["name"]), e(c.get("credit", "")))
            )
            char_items.append(
                '    <li class="char has-art">%s'
                '<div class="char-text"><strong>%s.</strong> %s</div></li>'
                % (art, e(c["name"]), e(c["desc"]))
            )
        else:
            char_items.append(
                '    <li class="char">'
                '<div class="char-text"><strong>%s.</strong> %s</div></li>'
                % (e(c["name"]), e(c["desc"]))
            )
    chars = "\n".join(char_items)
    themes = "\n".join(
        "    <li><strong>%s.</strong> %s</li>" % (e(name), e(desc))
        for name, desc in C.THEMES
    )

    body = (
        '<section class="hero">\n'
        "  <h1>%s</h1>\n"
        '  <p class="lede">%s</p>\n'
        "  <p>%s</p>\n"
        "  <p>%s</p>\n"
        "</section>\n\n"
        '<h2 class="sec-h">Композиция</h2>\n'
        "%s\n\n"
        '<h2 class="sec-h">Главные герои</h2>\n'
        '<ul class="chars">\n%s\n</ul>\n\n'
        '<h2 class="sec-h">Сквозные темы</h2>\n'
        '<ul class="plain">\n%s\n</ul>\n'
    ) % (
        e(m["title"]),
        e(m["subtitle"]),
        e(m["intro"]),
        e(m["in_medias_res"]),
        "\n".join(parts_html),
        chars,
        themes,
    )
    return layout(m["title"], body)


def build_song(s):
    n = s["n"]
    moments = "\n".join("    <li>%s</li>" % e(mm) for mm in s["moments"])
    reader_html = render_reader(n)

    art_html = ""
    if s.get("img"):
        art_html = (
            '  <figure class="art">\n'
            '    <img src="img/%s" alt="%s" loading="lazy">\n'
            "    <figcaption>%s</figcaption>\n"
            "  </figure>\n"
        ) % (e(s["img"]), e(s["title"]), e(s.get("credit", "")))

    prev_link = (
        '<a class="nav-prev" href="%s">← Песнь %d</a>' % (song_href(n - 1), n - 1)
        if n > 1
        else '<span class="nav-prev nav-off">←</span>'
    )
    next_link = (
        '<a class="nav-next" href="%s">Песнь %d →</a>' % (song_href(n + 1), n + 1)
        if n < len(C.SONGS)
        else '<span class="nav-next nav-off">→</span>'
    )

    body = (
        '<p class="crumb"><a href="index.html">← Все песни</a></p>\n'
        '<article class="song">\n'
        '  <p class="song-eyebrow">Песнь %d из 24</p>\n'
        "  <h1>%s</h1>\n"
        "%s"
        '  <dl class="song-meta">\n'
        "    <dt>Где</dt><dd>%s</dd>\n"
        "    <dt>Кто</dt><dd>%s</dd>\n"
        "  </dl>\n"
        '  <h2 class="sec-h">Кратко</h2>\n'
        "  <p>%s</p>\n"
        '  <h2 class="sec-h">Главные моменты</h2>\n'
        '  <ul class="moments">\n%s\n  </ul>\n'
        '  <h2 class="sec-h">Значение</h2>\n'
        '  <p class="significance">%s</p>\n'
        "</article>\n"
        "%s"
        '<nav class="song-nav">%s%s</nav>\n'
    ) % (
        n,
        e(s["title"]),
        art_html,
        e(s["where"]),
        e(s["who"]),
        e(s["summary"]),
        moments,
        e(s["significance"]),
        reader_html,
        prev_link,
        next_link,
    )
    return layout("Песнь %d — %s" % (n, s["title"]), body)


def write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    # Чистая пересборка docs/
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    write(os.path.join(OUT, "index.html"), build_index())
    for s in C.SONGS:
        write(os.path.join(OUT, song_href(s["n"])), build_song(s))

    # Стили рядом со страницами
    shutil.copyfile(os.path.join(STATIC, "style.css"), os.path.join(OUT, "style.css"))
    # Иллюстрации (общественное достояние)
    img_src = os.path.join(STATIC, "img")
    if os.path.isdir(img_src):
        shutil.copytree(img_src, os.path.join(OUT, "img"))
    # Отключаем обработку Jekyll на GitHub Pages — раздаём файлы как есть
    write(os.path.join(OUT, ".nojekyll"), "")

    print("Готово: %d страниц песен + index.html в %s" % (len(C.SONGS), OUT))


if __name__ == "__main__":
    main()
