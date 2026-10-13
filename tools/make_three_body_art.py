# -*- coding: utf-8 -*-
"""Рисует свои иллюстрации к «Задаче трёх тел»: траектории трёх солнц в SVG.

Для каждой главы честно считается задача трёх тел (три равные массы, ньютоновское
тяготение, интегратор «чехарда»), у каждой главы свои начальные условия, поэтому
и рисунок свой. Траектории хаотичны — как и должно быть.

Только стандартная библиотека. Результат: static/img/three-body/orbit-NN.svg.
Запуск:  python3 tools/make_three_body_art.py
"""

import math
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "static", "img", "three-body")

W, H = 1200, 640
COLORS = ("#f2b46b", "#e8834a", "#f6d39a")   # три солнца
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


def to_svg(tracks, rng):
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
        '<stop offset="0" stop-color="#0c2024"/><stop offset="1" stop-color="#1d4f57"/>'
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
    for t, color in zip(tracks, COLORS):
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
    for t, color in zip(tracks, COLORS):
        x, y = pt(t[-1])
        if -50 < x < W + 50 and -50 < y < H + 50:
            parts.append('<circle cx="%.1f" cy="%.1f" r="26" fill="url(#glow)" opacity="0.55"/>'
                         % (x, y))
            parts.append('<circle cx="%.1f" cy="%.1f" r="9" fill="%s"/>' % (x, y, color))
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main():
    os.makedirs(OUT, exist_ok=True)
    for n in range(1, 36):
        # Ищем начальные условия, при которых все три солнца остаются рядом
        seed = n * 1000
        while True:
            rng = random.Random(seed)
            tracks = simulate(rng)
            if bounded(tracks) == 0:
                break
            seed += 1
        svg = to_svg(tracks, random.Random(seed + 7))
        path = os.path.join(OUT, "orbit-%02d.svg" % n)
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print("orbit-%02d.svg  seed=%d  %.0f КБ" % (n, seed, os.path.getsize(path) / 1024))


if __name__ == "__main__":
    main()
