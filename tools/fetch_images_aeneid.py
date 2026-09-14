# -*- coding: utf-8 -*-
"""Подбирает иллюстрации к песням и персонажам «Энеиды» на Wikimedia Commons.

То же самое, что fetch_images.py делает для «Илиады», но:
- пишет в static/img/aeneid/ (а не в static/img/ напрямую);
- свой список запросов под сюжеты и героев «Энеиды».

Берёт только файлы с лицензией «общественное достояние», скачивает уменьшенную
копию (макс. 1400 px) и печатает готовые строки для _SONG_IMG / _CHAR_IMG.

Запуск:  python3 tools/fetch_images_aeneid.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_images import run, load_manifest  # noqa: E402

import fetch_images  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fetch_images.IMG = os.path.join(ROOT, "static", "img", "aeneid")

# Что искать: номер песни -> варианты запросов (пробуем по очереди).
SONG_QUERIES = {
    1: ['Guerin Aeneas telling Dido misfortunes Troy', 'Rubens Neptune calms the storm Quos Ego',
        'Tiepolo Aeneas Dido banquet'],
    2: ['Barocci Aeneas flight from Troy', 'Tiepolo procession Trojan horse',
        'Aeneas carrying Anchises painting'],
    3: ['Claude Lorrain Aeneas at Delos', 'Harpies Aeneas painting Strophades',
        'Aeneas Polyphemus Achaemenides'],
    4: ['Turner Dido and Aeneas', 'Death of Dido painting', 'Guercino death of Dido'],
    5: ['Aeneid funeral games Anchises Sicily', 'Trojan women burning ships Aeneid',
        'Aeneas funeral games ship race'],
    6: ['Turner Golden Bough', 'Aeneas and the Sibyl painting', 'Aeneas underworld Charon Aeneid'],
    7: ['Aeneas landing Latium painting', 'Allecto fury painting Aeneid',
        'Amata fury Aeneid painting'],
    8: ['Boucher Venus at the forge of Vulcan', 'Venus Vulcan armour Aeneas',
        'Aeneas Evander Pallanteum painting'],
    9: ['Nisus and Euryalus sculpture', 'Death of Euryalus painting', 'Nisus Euryalus Aeneid'],
    10: ['Death of Pallas painting Aeneid', 'Mezentius Lausus painting', 'Aeneas battle Turnus painting'],
    11: ['Camilla queen of the Volsci painting', 'Death of Camilla Aeneid', 'Camilla Aeneid Diana huntress'],
    12: ['Giordano Aeneas defeats Turnus', 'Death of Turnus painting', 'Aeneas Turnus duel painting'],
}

CHAR_QUERIES = {
    "Эней": ['Aeneas carrying Anchises statue Bernini', 'Aeneas painting Troy', 'Flight of Aeneas painting'],
    "Дидона": ['Death of Dido painting', 'Dido queen of Carthage painting', 'Dido and Aeneas painting'],
    "Турн": ['Turnus Aeneid painting', 'Death of Turnus Aeneid', 'Turnus Rutuli painting'],
    "Анхис": ['Aeneas carrying Anchises painting', 'Anchises Aeneid painting', 'Bernini Aeneas Anchises'],
    "Асканий (Юл)": ['Ascanius Aeneid painting', 'Cupid disguised as Ascanius painting', 'Iulus Aeneid painting'],
    "Латин и Лавиния": ['Latinus king painting Aeneid', 'Lavinia Aeneid painting', 'King Latinus Aeneas painting'],
    "Эвандр и Паллант": ['Evander Pallas Aeneid painting', 'Pallas son of Evander painting',
                         'Death of Pallas Turnus'],
    "Низ и Эвриал": ['Nisus and Euryalus sculpture', 'Nisus Euryalus painting Aeneid',
                     'Death of Euryalus painting'],
    "Камилла": ['Camilla queen of the Volsci painting', 'Camilla Aeneid warrior painting'],
    "Мезенций": ['Mezentius Aeneid painting', 'Death of Mezentius painting', 'Mezentius Lausus painting'],
    "Венера": ['Venus goddess painting Botticelli', 'Venus Aeneid painting', 'Venus and Aeneas painting'],
    "Юнона": ['Juno goddess painting', 'Juno Aeneid painting', 'Juno queen of gods painting'],
}


def main():
    man = load_manifest()
    print("=== Песни ===")
    songs = run(SONG_QUERIES, lambda n: "song-%02d" % n, "songs", man)
    print("\n=== Персонажи ===")
    chars = run(CHAR_QUERIES, lambda k: "char-%02d" % (list(CHAR_QUERIES).index(k) + 1),
                "chars", man)

    print("\n\n# ---- вставить в content_aeneid.py ----")
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
