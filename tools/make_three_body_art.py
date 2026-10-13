# -*- coding: utf-8 -*-
"""Рисует свои иллюстрации к «Задаче трёх тел» (SVG) для глав, к которым нет фото.

Два вида рисунков:
- orbit-NN.svg — траектории трёх солнц: честно считается задача трёх тел (три равные
  массы, ньютоновское тяготение, интегратор «чехарда»), у каждой главы свои начальные
  условия и своя палитра. Только для глав о самой задаче трёх тел (ORBITS).
- art-NN.svg — сюжетные сцены (SCENES): записка Ян Дун, отсчёт на плёнке, модель
  Мо-цзы, распечатка «Не отвечайте!», три солнца Трисоляриса, развёрнутый протон.

Только стандартная библиотека. Результат: static/img/three-body/.
Запуск:  python3 tools/make_three_body_art.py
"""

import math
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "static", "img", "three-body")

W, H = 1200, 640
# Палитры орбит: фон (два цвета градиента) и цвета трёх солнц
ORBITS = {
    16: ("#0c2024", "#1d4f57", ("#f2b46b", "#e8834a", "#f6d39a")),   # ночная бирюза
    18: ("#0b1324", "#22345c", ("#9cc7ff", "#e3f0ff", "#6f9be0")),   # холодная синь
    24: ("#1c0b0b", "#4f1d1d", ("#ff8a5c", "#ffd08a", "#e8433a")),   # тревожный красный
    29: ("#140c22", "#3b2357", ("#d8a7ff", "#ffc98a", "#9f7be8")),   # фиолетовый
}
SOFT = 0.05      # смягчение тяготения, чтобы тесные сближения не «взрывались»
DT = 0.002
STEPS = 14000
SAMPLE = 7       # каждый N-й шаг идёт в рисунок


def simulate(rng):
    """Три тела единичной массы, суммарный импульс и центр масс — в нуле."""
    pos = [[rng.uniform(-1, 1), rng.uniform(-1, 1)] for _ in range(3)]
    vel = [[rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5)] for _ in range(3)]
    for arr in (pos, vel):
        cx = sum(p[0] for p in arr) / 3
        cy = sum(p[1] for p in arr) / 3
        for p in arr:
            p[0] -= cx
            p[1] -= cy

    def acc(ps):
        a = [[0.0, 0.0] for _ in range(3)]
        for i in range(3):
            for j in range(3):
                if i == j:
                    continue
                dx = ps[j][0] - ps[i][0]
                dy = ps[j][1] - ps[i][1]
                r2 = dx * dx + dy * dy + SOFT * SOFT
                f = 1.0 / (r2 * math.sqrt(r2))
                a[i][0] += dx * f
                a[i][1] += dy * f
        return a

    tracks = [[] for _ in range(3)]
    a = acc(pos)
    for step in range(STEPS):
        for i in range(3):
            vel[i][0] += 0.5 * DT * a[i][0]
            vel[i][1] += 0.5 * DT * a[i][1]
            pos[i][0] += DT * vel[i][0]
            pos[i][1] += DT * vel[i][1]
        a = acc(pos)
        for i in range(3):
            vel[i][0] += 0.5 * DT * a[i][0]
            vel[i][1] += 0.5 * DT * a[i][1]
        if step % SAMPLE == 0:
            for i in range(3):
                tracks[i].append((pos[i][0], pos[i][1]))
    return tracks


def bounded(tracks):
    """Сколько тел остались «в системе», а не улетели — для отбора красивых сюжетов."""
    far = 0
    for t in tracks:
        if max(math.hypot(x, y) for x, y in t) > 3:
            far += 1
    return far


def to_svg(tracks, rng, palette):
    sky0, sky1, colors = palette
    # Масштаб по перцентилям: улетевшее тело не должно сжимать картинку в точку
    # Центр масс неподвижен в нуле — его и ставим в центр кадра
    ax = sorted(abs(p[0]) for t in tracks for p in t)
    ay = sorted(abs(p[1]) for t in tracks for p in t)
    rx = ax[int(len(ax) * 0.98)]
    ry = ay[int(len(ay) * 0.98)]
    k = min(W / (2 * rx), H / (2 * ry)) * 0.85
    cx = cy = 0.0

    def pt(p):
        return (W / 2 + (p[0] - cx) * k, H / 2 - (p[1] - cy) * k)

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">'
        % (W, H, W, H),
        "<defs>",
        '<linearGradient id="sky" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/>' % (sky0, sky1) +
        "</linearGradient>",
        '<radialGradient id="glow"><stop offset="0" stop-color="#fff3d6"/>'
        '<stop offset="1" stop-color="#fff3d6" stop-opacity="0"/></radialGradient>',
        "</defs>",
        '<rect width="%d" height="%d" fill="url(#sky)"/>' % (W, H),
    ]
    # Фоновые звёзды
    for _ in range(140):
        parts.append('<circle cx="%.0f" cy="%.0f" r="%.1f" fill="#ffffff" opacity="%.2f"/>'
                     % (rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.4, 1.3),
                        rng.uniform(0.15, 0.6)))
    # Траектории: старые отрезки бледнее, свежие ярче
    chunks = 12
    for t, color in zip(tracks, colors):
        n = len(t)
        size = max(2, n // chunks)
        for c in range(chunks):
            seg = t[c * size:(c + 1) * size + 1]
            if len(seg) < 2:
                continue
            d = "M" + " L".join("%.1f %.1f" % pt(p) for p in seg)
            op = 0.12 + 0.75 * (c + 1) / chunks
            parts.append('<path d="%s" fill="none" stroke="%s" stroke-width="1.6" '
                         'stroke-linecap="round" stroke-linejoin="round" opacity="%.2f"/>'
                         % (d, color, op))
    # Сами солнца — в последней точке
    for t, color in zip(tracks, colors):
        x, y = pt(t[-1])
        if -50 < x < W + 50 and -50 < y < H + 50:
            parts.append('<circle cx="%.1f" cy="%.1f" r="26" fill="url(#glow)" opacity="0.55"/>'
                         % (x, y))
            parts.append('<circle cx="%.1f" cy="%.1f" r="9" fill="%s"/>' % (x, y, color))
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


# ---------- сюжетные сцены ----------

def svg_open(bg_defs=""):
    return ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">'
            % (W, H, W, H), "<defs>%s</defs>" % bg_defs]


def stars(rng, n=120, color="#ffffff", y_max=H):
    return ['<circle cx="%.0f" cy="%.0f" r="%.1f" fill="%s" opacity="%.2f"/>'
            % (rng.uniform(0, W), rng.uniform(0, y_max), rng.uniform(0.4, 1.3), color,
               rng.uniform(0.15, 0.6)) for _ in range(n)]


def scene_note(rng):
    """Глава 4: предсмертная записка Ян Дун на тёмном столе."""
    p = svg_open('<linearGradient id="desk" x1="0" y1="0" x2="1" y2="1">'
                 '<stop offset="0" stop-color="#1b1714"/><stop offset="1" stop-color="#3a2e25"/>'
                 '</linearGradient>'
                 '<filter id="sh"><feDropShadow dx="0" dy="10" stdDeviation="14" '
                 'flood-color="#000" flood-opacity=".5"/></filter>')
    p.append('<rect width="%d" height="%d" fill="url(#desk)"/>' % (W, H))
    p.append('<g transform="rotate(-4 600 320)" filter="url(#sh)">')
    p.append('<rect x="300" y="110" width="600" height="420" fill="#f4efe4"/>')
    for y in range(190, 520, 34):
        p.append('<line x1="330" y1="%d" x2="870" y2="%d" stroke="#c9d6e3" stroke-width="1"/>' % (y, y))
    p.append('<line x1="370" y1="110" x2="370" y2="530" stroke="#e7b3a8" stroke-width="1.2"/>')
    p.append('<text x="600" y="290" text-anchor="middle" font-family="Georgia, serif" '
             'font-style="italic" font-size="40" fill="#2a3550">Физики никогда не было</text>')
    p.append('<text x="600" y="356" text-anchor="middle" font-family="Georgia, serif" '
             'font-style="italic" font-size="40" fill="#2a3550">и не будет.</text>')
    p.append('</g></svg>')
    return "\n".join(p)


def scene_countdown(rng):
    """Глава 6: обратный отсчёт на кадрах фотоплёнки."""
    p = svg_open()
    p.append('<rect width="%d" height="%d" fill="#120d09"/>' % (W, H))
    p.append('<g transform="rotate(-6 600 320)">')
    p.append('<rect x="-60" y="170" width="1320" height="300" fill="#3b2412"/>')
    for x in range(-50, 1270, 34):
        for y in (184, 436):
            p.append('<rect x="%d" y="%d" width="18" height="20" rx="3" fill="#120d09"/>' % (x, y))
    t = 1194 * 3600 + 16 * 60 + 37
    for i, x in enumerate(range(-10, 1250, 260)):
        v = t - i
        label = "%d:%02d:%02d" % (v // 3600, v // 60 % 60, v % 60)
        p.append('<rect x="%d" y="218" width="230" height="204" fill="#d9c6a0" opacity=".9"/>' % x)
        # бледный «пейзаж» на кадре
        p.append('<path d="M%d 360 Q%d 300 %d 340 T%d 330 L%d 422 L%d 422 Z" fill="#a8916a"/>'
                 % (x, x + 60, x + 120, x + 230, x + 230, x))
        p.append('<text x="%d" y="330" text-anchor="middle" font-family="Menlo, Consolas, monospace" '
                 'font-size="36" font-weight="bold" fill="#fffaf0" stroke="#1a120a" stroke-width="1">%s</text>'
                 % (x + 115, label))
    p.append('</g></svg>')
    return "\n".join(p)


def scene_mozi(rng):
    """Глава 11: модель Мо-цзы — вселенная из вложенных сфер, за ними пламя."""
    p = svg_open('<radialGradient id="fire"><stop offset=".55" stop-color="#ffb347"/>'
                 '<stop offset="1" stop-color="#7a2a10"/></radialGradient>')
    p.append('<rect width="%d" height="%d" fill="#eadfc6"/>' % (W, H))
    cx, cy = 600, 290
    p.append('<circle cx="%d" cy="%d" r="265" fill="url(#fire)" opacity=".85"/>' % (cx, cy))
    for i, rr in enumerate((230, 185, 140, 95)):
        p.append('<circle cx="%d" cy="%d" r="%d" fill="%s" stroke="#2b2118" stroke-width="3"/>'
                 % (cx, cy, rr, ("#1d1813", "#2a221b", "#352b22", "#40342a")[i]))
        for _ in range(14 + i * 4):   # дырочки в сфере — так Мо-цзы объясняет звёзды
            a = rng.uniform(0, 2 * math.pi)
            d = rng.uniform(rr - 40, rr - 8)
            p.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#ffd27a"/>'
                     % (cx + d * math.cos(a), cy + d * math.sin(a), rng.uniform(1.5, 3.2)))
    p.append('<circle cx="%d" cy="%d" r="30" fill="#6d8a5a" stroke="#2b2118" stroke-width="3"/>' % (cx, cy))
    p.append('<text x="%d" y="612" text-anchor="middle" font-family="Georgia, serif" '
             'font-style="italic" font-size="22" fill="#4a3b2b">модель Мо-цзы: мир внутри '
             'вложенных сфер, свет звёзд — огонь, видный сквозь отверстия</text>' % cx)
    p.append('</svg>')
    return "\n".join(p)


def scene_signal(rng):
    """Глава 23: распечатка принятого сигнала на перфорированной бумаге."""
    p = svg_open()
    p.append('<rect width="%d" height="%d" fill="#1a1d1c"/>' % (W, H))
    p.append('<g transform="rotate(3 600 320)">')
    p.append('<rect x="250" y="-40" width="700" height="720" fill="#f3f1e6"/>')
    for y in range(-40, 680, 64):
        p.append('<rect x="290" y="%d" width="620" height="32" fill="#dfeedd"/>' % y)
    for y in range(-30, 680, 24):
        for x in (266, 934):
            p.append('<circle cx="%d" cy="%d" r="6" fill="#1a1d1c"/>' % (x, y))
    mono = 'font-family="Menlo, Consolas, monospace"'
    p.append('<text x="310" y="70" %s font-size="17" fill="#555">ПРИЁМ · ИСТОЧНИК ≈ 4 СВ. ГОДА · '
             'ВЫСШИЙ ПРИОРИТЕТ</text>' % mono)
    p.append('<text x="310" y="100" %s font-size="17" fill="#555">РАСШИФРОВКА:</text>' % mono)
    for i in range(3):
        p.append('<text x="600" y="%d" text-anchor="middle" %s font-size="54" font-weight="bold" '
                 'fill="#1f2b2a">НЕ ОТВЕЧАЙТЕ!</text>' % (215 + i * 110, mono))
    p.append('<text x="310" y="560" %s font-size="17" fill="#555">-- КОНЕЦ СООБЩЕНИЯ --</text>' % mono)
    p.append('</g></svg>')
    return "\n".join(p)


def scene_trisolaris(rng):
    """Глава 32: пост прослушивания под тремя солнцами Трисоляриса."""
    p = svg_open('<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
                 '<stop offset="0" stop-color="#2a0f1f"/><stop offset=".7" stop-color="#b8502c"/>'
                 '<stop offset="1" stop-color="#f2a65a"/></linearGradient>'
                 '<radialGradient id="sun"><stop offset="0" stop-color="#fff6dc"/>'
                 '<stop offset=".35" stop-color="#ffd27a"/>'
                 '<stop offset="1" stop-color="#ffd27a" stop-opacity="0"/></radialGradient>')
    p.append('<rect width="%d" height="%d" fill="url(#sky)"/>' % (W, H))
    p += stars(rng, 50, y_max=200)
    for x, y, r_ in ((300, 170, 120), (760, 260, 80), (1010, 120, 44)):
        p.append('<circle cx="%d" cy="%d" r="%d" fill="url(#sun)"/>' % (x, y, r_))
    p.append('<path d="M0 470 Q180 420 360 460 T760 450 T1200 440 L1200 640 L0 640 Z" fill="#3a1a14"/>')
    p.append('<path d="M0 540 Q240 500 520 530 T1200 520 L1200 640 L0 640 Z" fill="#1c0c0a"/>')
    # антенна поста 1379
    p.append('<path d="M880 520 L900 430 L920 520 Z" fill="#0e0605"/>')
    p.append('<path d="M850 420 Q900 470 950 420" fill="none" stroke="#0e0605" stroke-width="8"/>')
    p.append('<line x1="900" y1="445" x2="900" y2="395" stroke="#0e0605" stroke-width="4"/>')
    p.append('</svg>')
    return "\n".join(p)


def scene_sophon(rng):
    """Глава 33: протон, развёрнутый в плоскость, на которую наносят схемы."""
    p = svg_open('<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
                 '<stop offset="0" stop-color="#05060f"/><stop offset="1" stop-color="#1a1440"/>'
                 '</linearGradient>'
                 '<radialGradient id="pt"><stop offset="0" stop-color="#ffffff"/>'
                 '<stop offset="1" stop-color="#9fd8ff" stop-opacity="0"/></radialGradient>')
    p.append('<rect width="%d" height="%d" fill="url(#bg)"/>' % (W, H))
    p += stars(rng, 90)

    def proj(u, v):   # плоскость в перспективе: u, v ∈ [0, 1]
        y = 300 + 300 * v
        half = 260 + 560 * v
        return 600 + (u - 0.5) * 2 * half, y

    for i in range(0, 21):
        a, b = proj(i / 20, 0), proj(i / 20, 1)
        p.append('<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" stroke="#3d6fa8" stroke-width="1" '
                 'opacity=".45"/>' % (a + b))
        a, b = proj(0, i / 20), proj(1, i / 20)
        p.append('<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" stroke="#3d6fa8" stroke-width="1" '
                 'opacity=".45"/>' % (a + b))
    # «схемы» — ломаные дорожки по сетке с узлами
    for _ in range(26):
        u, v = rng.randint(0, 20), rng.randint(0, 20)
        pts = [proj(u / 20, v / 20)]
        for _ in range(rng.randint(3, 7)):
            if rng.random() < 0.5:
                u = min(20, max(0, u + rng.choice((-3, -2, 2, 3))))
            else:
                v = min(20, max(0, v + rng.choice((-3, -2, 2, 3))))
            pts.append(proj(u / 20, v / 20))
        d = "M" + " L".join("%.0f %.0f" % q for q in pts)
        p.append('<path d="%s" fill="none" stroke="#7fe0ff" stroke-width="2" opacity=".8"/>' % d)
        p.append('<circle cx="%.0f" cy="%.0f" r="4" fill="#c9f3ff"/>' % pts[-1])
    p.append('<circle cx="600" cy="150" r="60" fill="url(#pt)"/>')
    p.append('<circle cx="600" cy="150" r="5" fill="#ffffff"/>')
    p.append('</svg>')
    return "\n".join(p)


SCENES = {4: scene_note, 6: scene_countdown, 11: scene_mozi, 23: scene_signal,
          32: scene_trisolaris, 33: scene_sophon}


def write(name, svg):
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg + ("" if svg.endswith("\n") else "\n"))
    print("%s  %.0f КБ" % (name, os.path.getsize(path) / 1024))


def main():
    os.makedirs(OUT, exist_ok=True)
    for n, palette in ORBITS.items():
        # Ищем начальные условия, при которых все три солнца остаются рядом
        seed = n * 1000
        while True:
            rng = random.Random(seed)
            tracks = simulate(rng)
            if bounded(tracks) == 0:
                break
            seed += 1
        write("orbit-%02d.svg" % n, to_svg(tracks, random.Random(seed + 7), palette))
    for n, fn in SCENES.items():
        write("art-%02d.svg" % n, fn(random.Random(n)))


if __name__ == "__main__":
    main()
