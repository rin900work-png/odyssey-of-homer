# -*- coding: utf-8 -*-
"""Сборка статического сайта-разбора Гомера в папку docs/.

Сайт двухчастный: «Одиссея» и «Илиада». Титульная страница (index.html) —
выбор поэмы, дальше у каждой своя страница-оглавление и свои 24 песни.

Без внешних зависимостей — только стандартная библиотека Python 3.
Запуск:  python3 build.py
Результат:
    docs/index.html                — титульная, выбор поэмы
    docs/odyssey.html              — оглавление «Одиссеи»
    docs/odyssey-song-01..24.html  — песни «Одиссеи»
    docs/iliad.html                — оглавление «Илиады»
    docs/iliad-song-01..24.html    — песни «Илиады»
    docs/song-01..24.html          — заглушки-редиректы со старых адресов
    docs/style.css, docs/img/, docs/.nojekyll

Папка называется docs/, потому что так её умеет раздавать GitHub Pages
(Settings → Pages → ветка main, папка /docs). Подойдёт и любой другой
статический хостинг (Cloudflare Pages, Netlify, Vercel) — раздаётся docs/.
"""

import html
import os
import shutil

import content_iliad
import content_odyssey

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "docs")
STATIC = os.path.join(ROOT, "static")
TEXTS = os.path.join(ROOT, "texts")

STANZA = 10      # стихов в одной визуальной строфе
NUM_EVERY = 10   # показывать номер стиха каждые N строк

SITE_TITLE = "Гомер"
SITE_SUB = "«Одиссея» и «Илиада» — краткий разбор по песням"

# Описание поэм. Тексты и картинки лежат в texts/<slug>/ и static/img/<slug>/.
BOOKS = [
    {
        "slug": "odyssey",
        "content": content_odyssey,
        "short": "Одиссея",
        "translator": "В. А. Жуковского",
        "cover": "song-12.jpg",
        "card": "Возвращение домой после Троянской войны: десять лет странствий, киклоп "
                "и Цирцея, царство мёртвых, сирены — и расправа над женихами на Итаке.",
        # У «Одиссеи» песни раньше лежали по адресам song-NN.html — оставляем редиректы.
        "legacy": True,
    },
    {
        "slug": "iliad",
        "content": content_iliad,
        "short": "Илиада",
        "translator": "Н. И. Гнедича",
        "cover": "song-01.jpg",
        "card": "Пятьдесят дней десятого года осады Трои: гнев Ахиллеса, гибель Патрокла "
                "и Гектора — и старик Приам, целующий руки убийцы сына.",
        "legacy": False,
    },
]


def e(text):
    """Экранирование для HTML."""
    return html.escape(str(text))


def read_verses(book, n):
    """Читает полный текст песни из texts/<slug>/song-NN.txt (один стих на строку).

    Возвращает список стихов или None, если файла нет.
    """
    path = os.path.join(TEXTS, book["slug"], "song-%02d.txt" % n)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        verses = [ln.rstrip() for ln in f.read().split("\n")]
    return [v for v in verses if v.strip() != ""]


def render_reader(book, n):
    """Раскрывающийся блок с полным текстом песни: строфы + нумерация стихов."""
    verses = read_verses(book, n)
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
        '        <span class="reader-toggle-meta">перевод %s · %d стихов</span>\n'
        "      </summary>\n"
        '      <div class="poem">\n%s\n      </div>\n'
        '      <p class="reader-source">Источник: Викитека (ru.wikisource.org), '
        "перевод %s. Общественное достояние.</p>\n"
        "    </details>\n"
        "  </section>\n"
    ) % (book["translator"], len(verses), "\n".join(stanzas), book["translator"])


def book_href(book):
    return "%s.html" % book["slug"]


def song_href(book, n):
    return "%s-song-%02d.html" % (book["slug"], n)


def img_src(book, filename):
    return "img/%s/%s" % (book["slug"], filename)


def song_by_n(book, n):
    for s in book["content"].SONGS:
        if s["n"] == n:
            return s
    raise KeyError(n)


def layout(title, body, book=None):
    """Общий каркас страницы. book=None — титульная."""
    if book is None:
        theme = "theme-site"
        header = (
            '<header class="site-header">\n'
            '  <span class="brand">%s</span>\n'
            '  <span class="brand-sub">%s</span>\n'
            "</header>\n"
        ) % (e(SITE_TITLE), e(SITE_SUB))
        footer = "Гомер · «Одиссея» и «Илиада» · по 24 песни · краткий разбор"
    else:
        theme = "theme-%s" % book["slug"]
        header = (
            '<header class="site-header">\n'
            '  <a class="brand" href="%s">%s</a>\n'
            '  <span class="brand-sub">%s</span>\n'
            '  <a class="brand-home" href="index.html">%s</a>\n'
            "</header>\n"
        ) % (
            e(book_href(book)),
            e(book["content"].META["title"]),
            e(book["content"].META["subtitle"]),
            e("Гомер: обе поэмы"),
        )
        footer = "Гомер · «%s» · 24 песни · краткий разбор" % e(book["short"])

    return (
        "<!doctype html>\n"
        '<html lang="ru">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n"
        '<link rel="stylesheet" href="style.css">\n'
        "</head>\n"
        '<body class="%s">\n'
        "%s"
        '<main class="wrap">\n'
        "%s\n"
        "</main>\n"
        '<footer class="site-footer">\n'
        "  <p>%s</p>\n"
        "</footer>\n"
        "</body>\n"
        "</html>\n"
    ) % (e(title), theme, header, body, footer)


def build_landing():
    """Титульная страница: выбор поэмы."""
    cards = []
    for b in BOOKS:
        m = b["content"].META
        cover = ""
        if b.get("cover"):
            cover = (
                '  <img class="card-art" src="%s" alt="%s" loading="lazy">\n'
                % (e(img_src(b, b["cover"])), e(m["title"]))
            )
        cards.append(
            '<a class="card card-%s" href="%s">\n'
            "%s"
            '  <div class="card-text">\n'
            "    <h2>%s</h2>\n"
            '    <p class="card-blurb">%s</p>\n'
            '    <p class="card-meta">24 песни · полный текст в переводе %s</p>\n'
            "  </div>\n"
            "</a>"
            % (
                e(b["slug"]),
                e(book_href(b)),
                cover,
                e(m["title"]),
                e(b["card"]),
                b["translator"],
            )
        )

    body = (
        '<section class="hero hero-site">\n'
        "  <h1>%s</h1>\n"
        '  <p class="lede">%s</p>\n'
        "  <p>Две поэмы, приписываемые Гомеру (ок. VIII в. до н. э.), — разбор каждой "
        "песни и полный текст в классическом русском переводе. «Илиада» — о гневе "
        "Ахиллеса на десятом году осады Трои; «Одиссея» — о десятилетнем возвращении "
        "домой после её падения.</p>\n"
        "</section>\n\n"
        '<div class="cards">\n%s\n</div>\n'
    ) % (e(SITE_TITLE), e(SITE_SUB), "\n".join(cards))
    return layout("%s — «Одиссея» и «Илиада»" % SITE_TITLE, body, book=None)


def build_book_index(book):
    C = book["content"]
    m = C.META
    parts_html = []
    for p in C.PARTS:
        items = []
        for n in p["songs"]:
            s = song_by_n(book, n)
            items.append(
                '    <li><a href="%s"><span class="song-n">%d</span>'
                '<span class="song-t">%s</span></a></li>'
                % (song_href(book, n), n, e(s["title"]))
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
                '<figure class="char-art"><img src="%s" alt="%s" loading="lazy">'
                "<figcaption>%s</figcaption></figure>"
                % (e(img_src(book, c["img"])), e(c["name"]), e(c.get("credit", "")))
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

    other = [b for b in BOOKS if b is not book][0]
    body = (
        '<p class="crumb"><a href="index.html">← Обе поэмы</a></p>\n'
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
        '<ul class="plain">\n%s\n</ul>\n\n'
        '<p class="other-book">Читать вторую поэму: <a href="%s">%s</a></p>\n'
    ) % (
        e(m["title"]),
        e(m["subtitle"]),
        e(m["intro"]),
        e(m["in_medias_res"]),
        "\n".join(parts_html),
        chars,
        themes,
        e(book_href(other)),
        e(other["content"].META["title"]),
    )
    return layout(m["title"], body, book=book)


def build_song(book, s):
    C = book["content"]
    n = s["n"]
    moments = "\n".join("    <li>%s</li>" % e(mm) for mm in s["moments"])
    reader_html = render_reader(book, n)

    art_html = ""
    if s.get("img"):
        art_html = (
            '  <figure class="art">\n'
            '    <img src="%s" alt="%s" loading="lazy">\n'
            "    <figcaption>%s</figcaption>\n"
            "  </figure>\n"
        ) % (e(img_src(book, s["img"])), e(s["title"]), e(s.get("credit", "")))

    prev_link = (
        '<a class="nav-prev" href="%s">← Песнь %d</a>' % (song_href(book, n - 1), n - 1)
        if n > 1
        else '<span class="nav-prev nav-off">←</span>'
    )
    next_link = (
        '<a class="nav-next" href="%s">Песнь %d →</a>' % (song_href(book, n + 1), n + 1)
        if n < len(C.SONGS)
        else '<span class="nav-next nav-off">→</span>'
    )

    body = (
        '<p class="crumb"><a href="%s">← Все песни</a> · '
        '<a href="index.html">обе поэмы</a></p>\n'
        '<article class="song">\n'
        '  <p class="song-eyebrow">%s · песнь %d из 24</p>\n'
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
        e(book_href(book)),
        e(book["short"]),
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
    return layout("%s — песнь %d, %s" % (book["short"], n, s["title"]), body, book=book)


def build_redirect(target, title):
    """Заглушка со старого адреса: и для браузера, и для поисковика."""
    return (
        "<!doctype html>\n"
        '<html lang="ru">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta http-equiv="refresh" content="0; url=%s">\n'
        '<link rel="canonical" href="%s">\n'
        "<title>%s</title>\n"
        "</head>\n"
        "<body>\n"
        '<p>Страница переехала: <a href="%s">%s</a></p>\n'
        "</body>\n"
        "</html>\n"
    ) % (e(target), e(target), e(title), e(target), e(title))


def write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    # Чистая пересборка docs/
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    write(os.path.join(OUT, "index.html"), build_landing())

    pages = 0
    for book in BOOKS:
        write(os.path.join(OUT, book_href(book)), build_book_index(book))
        for s in book["content"].SONGS:
            write(os.path.join(OUT, song_href(book, s["n"])), build_song(book, s))
            pages += 1
        # Старые адреса песен «Одиссеи» (song-NN.html) не должны отваливаться
        if book.get("legacy"):
            for s in book["content"].SONGS:
                n = s["n"]
                write(
                    os.path.join(OUT, "song-%02d.html" % n),
                    build_redirect(song_href(book, n),
                                   "%s — песнь %d" % (book["short"], n)),
                )

    # Стили рядом со страницами
    shutil.copyfile(os.path.join(STATIC, "style.css"), os.path.join(OUT, "style.css"))
    # Иллюстрации (общественное достояние), по папке на поэму
    img_src_dir = os.path.join(STATIC, "img")
    if os.path.isdir(img_src_dir):
        shutil.copytree(img_src_dir, os.path.join(OUT, "img"),
                        ignore=shutil.ignore_patterns("credits.json"))
    # Отключаем обработку Jekyll на GitHub Pages — раздаём файлы как есть
    write(os.path.join(OUT, ".nojekyll"), "")

    print("Готово: титульная + %d страниц оглавления + %d страниц песен в %s"
          % (len(BOOKS), pages, OUT))


if __name__ == "__main__":
    main()
