"""Lädt für jede PLZ-Region die Rohdaten von PVGIS (EU-Kommission): typisches Jahr mit Stundenwerten und Monatsmittel 2005 bis 2023.
Aufruf im Ordner werkzeuge/pvdaten:  python3 holen.py   (legt raw/ an, rund 120 MB, dauert etwa 10 Minuten)"""
import os, subprocess, time
from regionen import R
B = 'https://re.jrc.ec.europa.eu/api/v5_3/'
os.makedirs('raw', exist_ok=True)


def get(url, f):
    if os.path.exists(f) and os.path.getsize(f) > 5000:
        return True
    for k in range(4):
        r = subprocess.run(['curl', '-sS', '-m', '90', '-o', f, '-w', '%{http_code}', url], capture_output=True, text=True)
        if r.stdout.strip() == '200' and os.path.getsize(f) > 5000:
            time.sleep(0.4)
            return True
        time.sleep(3 + 4 * k)
    print('FEHLER', f, r.stdout, r.stderr[:200], flush=True)
    return False


ok = 0
for k, (n, lat, lon) in sorted(R.items()):
    a = get(f'{B}tmy?lat={lat}&lon={lon}&outputformat=json&usehorizon=0', f'raw/tmy{k}.json')
    b = get(f'{B}MRcalc?lat={lat}&lon={lon}&horirrad=1&d2g=1&outputformat=json&usehorizon=0', f'raw/mr{k}.json')
    ok += a and b
    print(k, n, a, b, flush=True)
print('FERTIG', ok, 'von', len(R), flush=True)
