"""Baut aus raw/ die Dateien assets/pv/<PLZ2>.json für alle Regionen.  Aufruf: python3 alle.py"""
import json, os, pathlib
from regionen import R
from kodieren import build
ZIEL = pathlib.Path(__file__).resolve().parent.parent.parent / 'assets' / 'pv'
ZIEL.mkdir(parents=True, exist_ok=True)
g = []
for k, (n, lat, lon) in sorted(R.items()):
    out, info = build(f'raw/tmy{k}.json', f'raw/mr{k}.json', k, n)
    json.dump(out, open(ZIEL / f'{k}.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    g.append((out['ghi'], k, n))
    err = max(abs(i[0] - i[1]) for i in info)
    if err > 0.6:
        print('Abweichung Monatssumme', k, n, err)
g.sort()
print('Regionen', len(g), '| Sonne pro m2 und Jahr: min', g[0], 'max', g[-1], 'Median', g[len(g) // 2])
print('In bkw-planer.js stehen GHI_MIN und GHI_MAX: bei neuen Daten anpassen.')
