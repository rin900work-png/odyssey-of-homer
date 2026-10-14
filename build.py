# -*- coding: utf-8 -*-
"""Сборка статического сайта-разбора в папку docs/.

На сайте четыре книги: «Одиссея», «Илиада», «Энеида» и роман Лю Цысиня
«Задача трёх тел». Титульная страница (index.html) — выбор книги, дальше у
каждой своё оглавление и свои песни (у романа — главы).

Без внешних зависимостей — только стандартная библиотека Python 3.
Запуск:  python3 build.py
Результат:
    docs/index.html                — титульная, выбор поэмы
    docs/names.html                — справочник: греческие имена ↔ латинские
    docs/odyssey.html              — оглавление «Одиссеи»
    docs/odyssey-song-01..24.html  — песни «Одиссеи»
    docs/iliad.html                — оглавление «Илиады»
    docs/iliad-song-01..24.html    — песни «Илиады»
    docs/aeneid.html               — оглавление «Энеиды»
    docs/aeneid-song-01..12.html   — песни «Энеиды»
    docs/three-body.html           — оглавление «Задачи трёх тел»
    docs/three-body-song-01..35.html — главы «Задачи трёх тел»
    docs/three-body-science.html   — «Наука в книге: правда или вымысел»
    docs/song-01..24.html          — заглушки-редиректы со старых адресов
    docs/style.css, docs/img/, docs/.nojekyll

Папка называется docs/, потому что так её умеет раздавать GitHub Pages
(Settings → Pages → ветка main, папка /docs). Подойдёт и любой другой
статический хостинг (Cloudflare Pages, Netlify, Vercel) — раздаётся docs/.
"""

import html
import os
import shutil

import content_aeneid
import content_iliad
import content_names
import content_odyssey
import content_three_body

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "docs")
STATIC = os.path.join(ROOT, "static")
TEXTS = os.path.join(ROOT, "texts")

STANZA = 10      # стихов в одной визуальной строфе
NUM_EVERY = 10   # показывать номер стиха каждые N строк

SITE_TITLE = "Гомер и Вергилий"
SITE_SUB = "«Одиссея», «Илиада», «Энеида» и «Задача трёх тел» — краткий разбор"
NAMES_LINK_TEXT = "Боги: кто есть кто"

# Как называются части книги: у поэм — песни, у романа — главы.
# forms — для склонения под число (1 песнь / 2 песни / 5 песен).
UNITS = {
    "song": {"forms": ("песнь", "песни", "песен"), "label": "Песнь", "all": "Все песни"},
    "chapter": {"forms": ("глава", "главы", "глав"), "label": "Глава", "all": "Все главы"},
}

# Описание книг. Тексты и картинки лежат в texts/<slug>/ и static/img/<slug>/.
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
    {
        "slug": "aeneid",
        "content": content_aeneid,
        "short": "Энеида",
        "cover": "song-01.jpg",
        # Единственный полный дореволюционный (PD) перевод — И. Г. Шершеневича — на
        # Викитеке не расшифрован для песен I—II, поэтому режима чтения пока нет.
        "translator": None,
        "card": "Троянец Эней после гибели Трои семь лет скитается по морю и приводит "
                "уцелевших спутников в Италию, где ради судьбы будущего Рима переживает "
                "любовь Дидоны, войну с Турном и нисхождение в царство мёртвых.",
        "legacy": False,
    },
    {
        "slug": "three-body",
        "content": content_three_body,
        "short": "Задача трёх тел",
        "unit": "chapter",
        "cover": "orbit-16.svg",
        # Роман 2006/2008 года и перевод О. Глушковой (2017) под авторским правом —
        # полного текста на сайте не будет, только разбор.
        "translator": None,
        "no_text": "без полного текста: книга под авторским правом",
        # Справочник имён богов к роману не относится — ссылку в шапке не показываем.
        "names_link": False,
        "card": "Китайская научная фантастика: дочь убитого в Культурную революцию "
                "физика отвечает на сигнал из космоса, а через сорок лет учёный "
                "расследует самоубийства физиков и игру о мире с тремя солнцами.",
        "legacy": False,
    },
]


def unit(book):
    return UNITS[book.get("unit", "song")]


# Справки «правда или вымысел» (SCIENCE в content_*.py — пока только у романа)
SCIENCE_LINK_TEXT = "Наука: правда или вымысел"
VERDICTS = {
    "real": "правда",
    "partly": "отчасти правда",
    "fiction": "вымысел",
}


def science(book):
    return getattr(book["content"], "SCIENCE", None)


def science_href(book):
    return "%s-science.html" % book["slug"]


def plural(n, forms):
    """Склонение под число: forms = (1, 2–4, 5+), например ("песнь", "песни", "песен")."""
    one, few, many = forms
    if 11 <= n % 100 <= 14:
        return many
    tail = n % 10
    if tail == 1:
        return one
    if 2 <= tail <= 4:
        return few
    return many


def book_list_str(books):
    """«Одиссея», «Илиада», «Энеида» и … — с союзом перед последним пунктом."""
    names = ['«%s»' % b["short"] for b in books]
    if len(names) == 1:
        return names[0]
    return "%s и %s" % (", ".join(names[:-1]), names[-1])


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
        '        <span class="reader-toggle-meta">перевод %s · %d стихов</span>\n'
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
            '  <a class="brand-home" href="names.html">%s</a>\n'
            "</header>\n"
        ) % (e(SITE_TITLE), e(SITE_SUB), e(NAMES_LINK_TEXT))
        footer = "%s · %s · краткий разбор" % (e(SITE_TITLE), e(book_list_str(BOOKS)))
    else:
        theme = "theme-%s" % book["slug"]
        names_link = ""
        if book.get("names_link", True):
            names_link = '  <a class="brand-names" href="names.html">%s</a>\n' % e(NAMES_LINK_TEXT)
        if science(book):
            names_link += '  <a class="brand-names" href="%s">%s</a>\n' % (
                e(science_href(book)), e(SCIENCE_LINK_TEXT))
        header = (
            '<header class="site-header">\n'
            '  <a class="brand" href="%s">%s</a>\n'
            '  <span class="brand-sub">%s</span>\n'
            '  <a class="brand-home" href="index.html">%s</a>\n'
            "%s"
            "</header>\n"
        ) % (
            e(book_href(book)),
            e(book["content"].META["title"]),
            e(book["content"].META["subtitle"]),
            e(SITE_TITLE),
            names_link,
        )
        count = len(book["content"].SONGS)
        footer = "%s · «%s» · %d %s · краткий разбор" % (
            e(SITE_TITLE), e(book["short"]), count, plural(count, unit(book)["forms"])
        )

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
        count = len(b["content"].SONGS)
        # Без обложки — нейтральная плашка той же высоты, чтобы карточки не прыгали
        cover = '  <div class="card-art card-art-blank" aria-hidden="true"></div>\n'
        if b.get("cover"):
            cover = (
                '  <img class="card-art" src="%s" alt="%s" loading="lazy">\n'
                % (e(img_src(b, b["cover"])), e(m["title"]))
            )
        word = plural(count, unit(b)["forms"])
        if b.get("translator"):
            meta_line = "%d %s · полный текст в переводе %s" % (count, word, b["translator"])
        else:
            meta_line = "%d %s · %s" % (count, word, b.get("no_text", "без полного текста (пока)"))
        cards.append(
            '<a class="card card-%s" href="%s">\n'
            "%s"
            '  <div class="card-text">\n'
            "    <h2>%s</h2>\n"
            '    <p class="card-blurb">%s</p>\n'
            '    <p class="card-meta">%s</p>\n'
            "  </div>\n"
            "</a>"
            % (
                e(b["slug"]),
                e(book_href(b)),
                cover,
                e(m["title"]),
                e(b["card"]),
                e(meta_line),
            )
        )

    body = (
        '<section class="hero hero-site">\n'
        "  <h1>%s</h1>\n"
        '  <p class="lede">%s</p>\n'
        "  <p>Три поэмы античного эпоса — разбор каждой песни, а для «Одиссеи» и «Илиады» "
        "ещё и полный текст в классическом русском переводе. Гомеровские «Илиада» — о гневе "
        "Ахиллеса на десятом году осады Трои, «Одиссея» — о десятилетнем возвращении домой "
        "после её падения; «Энеида» Вергилия — о том, как уцелевший троянец приводит "
        "спутников в Италию, чтобы стать родоначальником Рима.</p>\n"
        "  <p>И одна книга совсем из другой эпохи — «Задача трёх тел» Лю Цысиня, "
        "научно-фантастический роман о первом контакте человечества с иным разумом, "
        "разобранный по главам.</p>\n"
        "</section>\n\n"
        '<div class="cards">\n%s\n</div>\n'
    ) % (e(SITE_TITLE), e(SITE_SUB), "\n".join(cards))
    return layout("%s — %s" % (SITE_TITLE, book_list_str(BOOKS)), body, book=None)


def build_names_page():
    """Справочник: греческие имена богов (Гомер) ↔ латинские (Вергилий)."""
    rows = "\n".join(
        '    <tr><td>%s</td><td>%s</td><td>%s</td><td class="names-where">%s</td></tr>'
        % (e(gr), e(la), e(desc), e(where))
        for gr, la, desc, where in content_names.GODS
    )
    heroes = "\n".join(
        '    <li><strong>%s → %s.</strong> %s</li>' % (e(gr), e(la), e(desc))
        for gr, la, desc in content_names.HEROES
    )
    body = (
        '<p class="crumb"><a href="index.html">← Все книги</a></p>\n'
        '<section class="hero">\n'
        "  <h1>%s</h1>\n"
        '  <p class="lede">%s</p>\n'
        "</section>\n\n"
        '<h2 class="sec-h">Боги</h2>\n'
        '<div class="table-wrap">\n'
        '<table class="names-table">\n'
        "  <thead>\n"
        "    <tr><th>У Гомера (по-гречески)</th><th>У Вергилия (по-латыни)</th>"
        "<th>Кто такой(-ая)</th><th>Где на сайте</th></tr>\n"
        "  </thead>\n"
        "  <tbody>\n%s\n  </tbody>\n"
        "</table>\n"
        "</div>\n\n"
        '<h2 class="sec-h">Герои и другие персонажи</h2>\n'
        '<ul class="plain">\n%s\n</ul>\n'
    ) % (
        e("Боги и герои: греческие имена и латинские"),
        e(content_names.INTRO),
        rows,
        heroes,
    )
    return layout("Боги и герои — греческие и латинские имена", body, book=None)


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

    others = [b for b in BOOKS if b is not book]
    other_links = ", ".join(
        '<a href="%s">%s</a>' % (e(book_href(o)), e(o["content"].META["title"]))
        for o in others
    )
    science_teaser = ""
    if science(book):
        science_teaser = (
            '<a class="sci-teaser" href="%s"><strong>%s</strong> — %d справок: что в книге '
            "настоящая наука, а что придумано для сюжета →</a>\n\n"
            % (e(science_href(book)), e(SCIENCE_LINK_TEXT), len(science(book)))
        )
    other_label = "Читать другую книгу" if len(others) == 1 else "Другие книги на сайте"
    body = (
        '<p class="crumb"><a href="index.html">← Все книги</a></p>\n'
        '<section class="hero">\n'
        "  <h1>%s</h1>\n"
        '  <p class="lede">%s</p>\n'
        "  <p>%s</p>\n"
        "  <p>%s</p>\n"
        "</section>\n\n"
        "%s"
        '<h2 class="sec-h">Композиция</h2>\n'
        "%s\n\n"
        '<h2 class="sec-h">Главные герои</h2>\n'
        '<ul class="chars">\n%s\n</ul>\n\n'
        '<h2 class="sec-h">Сквозные темы</h2>\n'
        '<ul class="plain">\n%s\n</ul>\n\n'
        '<p class="other-book">%s: %s</p>\n'
    ) % (
        e(m["title"]),
        e(m["subtitle"]),
        e(m["intro"]),
        e(m["in_medias_res"]),
        science_teaser,
        "\n".join(parts_html),
        chars,
        themes,
        other_label,
        other_links,
    )
    return layout(m["title"], body, book=book)


def build_song(book, s):
    C = book["content"]
    n = s["n"]
    total = len(C.SONGS)
    u = unit(book)
    moments = "\n".join("    <li>%s</li>" % e(mm) for mm in s["moments"])
    reader_html = render_reader(book, n)

    sci_html = ""
    topics = [t for t in (science(book) or []) if n in t["chapters"]]
    if topics:
        sci_html = (
            '  <h2 class="sec-h">Наука в этой главе</h2>\n'
            '  <ul class="sci-links">\n%s\n  </ul>\n'
            % "\n".join(
                '    <li><a href="%s#%s">%s</a> <span class="verdict verdict-%s">%s</span></li>'
                % (e(science_href(book)), e(t["id"]), e(t["title"]), e(t["verdict"]),
                   e(VERDICTS[t["verdict"]]))
                for t in topics
            )
        )

    art_html = ""
    if s.get("img"):
        art_html = (
            '  <figure class="art">\n'
            '    <img src="%s" alt="%s" loading="lazy">\n'
            "    <figcaption>%s</figcaption>\n"
            "  </figure>\n"
        ) % (e(img_src(book, s["img"])), e(s["title"]), e(s.get("credit", "")))

    prev_link = (
        '<a class="nav-prev" href="%s">← %s %d</a>' % (song_href(book, n - 1), u["label"], n - 1)
        if n > 1
        else '<span class="nav-prev nav-off">←</span>'
    )
    next_link = (
        '<a class="nav-next" href="%s">%s %d →</a>' % (song_href(book, n + 1), u["label"], n + 1)
        if n < total
        else '<span class="nav-next nav-off">→</span>'
    )

    body = (
        '<p class="crumb"><a href="%s">← %s</a> · '
        '<a href="index.html">все книги</a></p>\n'
        '<article class="song">\n'
        '  <p class="song-eyebrow">%s · %s %d из %d</p>\n'
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
        "%s"
        "</article>\n"
        "%s"
        '<nav class="song-nav">%s%s</nav>\n'
    ) % (
        e(book_href(book)),
        e(u["all"]),
        e(book["short"]),
        e(u["forms"][0]),
        n,
        total,
        e(s["title"]),
        art_html,
        e(s["where"]),
        e(s["who"]),
        e(s["summary"]),
        moments,
        e(s["significance"]),
        sci_html,
        reader_html,
        prev_link,
        next_link,
    )
    return layout("%s — %s %d, %s" % (book["short"], u["forms"][0], n, s["title"]), body, book=book)


def build_science_page(book):
    """Справки «правда или вымысел» по науке в книге."""
    C = book["content"]
    cards = []
    for t in science(book):
        art = ""
        if t.get("img"):
            art = '  <img class="sci-art" src="%s" alt="%s" loading="lazy">\n' % (
                e(img_src(book, t["img"])), e(t["title"]))
        chapters = ", ".join(
            '<a href="%s">%d</a>' % (e(song_href(book, n)), n) for n in t["chapters"])
        cards.append(
            '<section class="sci-card" id="%s">\n'
            "%s"
            '  <div class="sci-body">\n'
            '    <p class="sci-head"><span class="verdict verdict-%s">%s</span></p>\n'
            "    <h2>%s</h2>\n"
            "    <p>%s</p>\n"
            '    <p class="sci-ch">%s: %s</p>\n'
            "  </div>\n"
            "</section>"
            % (e(t["id"]), art, e(t["verdict"]), e(VERDICTS[t["verdict"]]), e(t["title"]),
               e(t["text"]), e(unit(book)["all"]), chapters)
        )
    counts = {v: sum(1 for t in science(book) if t["verdict"] == v) for v in VERDICTS}
    legend = " · ".join(
        '<span class="verdict verdict-%s">%s</span> %d' % (v, e(label), counts[v])
        for v, label in VERDICTS.items()
    )
    body = (
        '<p class="crumb"><a href="%s">← %s</a> · <a href="index.html">все книги</a></p>\n'
        '<section class="hero">\n'
        "  <h1>Наука в книге: правда или вымысел</h1>\n"
        "  <p>%s</p>\n"
        '  <p class="sci-legend">%s</p>\n'
        "</section>\n\n"
        '<div class="sci-list">\n%s\n</div>\n'
    ) % (e(book_href(book)), e(C.META["title"]), e(C.SCIENCE_INTRO), legend, "\n".join(cards))
    return layout("%s — наука: правда или вымысел" % book["short"], body, book=book)


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
    write(os.path.join(OUT, "names.html"), build_names_page())

    pages = 0
    for book in BOOKS:
        write(os.path.join(OUT, book_href(book)), build_book_index(book))
        if science(book):
            write(os.path.join(OUT, science_href(book)), build_science_page(book))
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

    print("Готово: титульная + %d страниц оглавления + %d страниц песен и глав в %s"
          % (len(BOOKS), pages, OUT))


if __name__ == "__main__":
    main()
