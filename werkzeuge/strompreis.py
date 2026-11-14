"""Strom-Daheim: Börsenstrompreise für strompreis-heute.html holen.

Quelle: Bundesnetzagentur | SMARD.de (Day-Ahead-Preis der Gebotszone Deutschland/Luxemburg, Stundenwerte), Lizenz CC BY 4.0.
Die Quellenangabe steht auf der Seite und muss dort bleiben.

Aufruf im Repository-Ordner:  python3 werkzeuge/strompreis.py
Schreibt assets/strompreis.json (die letzten 8 Tage, heute und, sobald veröffentlicht, morgen; Werte in Cent pro kWh ohne Steuern
und Abgaben), den Textblock zwischen <!--SP--> und <!--/SP--> in strompreis-heute.html (für Leser ohne JavaScript und für
Suchmaschinen) und das Datum der Seite in sitemap.xml. Läuft mehrmals täglich über .github/workflows/strompreis.yml,
Agenten müssen nichts tun. Liefert SMARD nichts, bleibt alles, wie es ist (Fehlercode 0, damit der Lauf nicht rot wird).
"""
import json, re, sys, pathlib, datetime, urllib.request
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = 'https://www.smard.de/app/chart_data/4169/DE-LU/'
TZ = ZoneInfo('Europe/Berlin')
TAGE = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'strom-daheim.de (Strompreis-Seite)'})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def holen():
    """Gibt {datum: [24 Werte in ct/kWh oder None]} für die letzten Wochen zurück."""
    idx = get(BASE + 'index_hour.json')['timestamps']
    roh = {}
    for ts in idx[-3:]:
        for t, v in get(BASE + '4169_DE-LU_hour_%d.json' % ts)['series']:
            if v is not None:
                roh[t] = v
    tage = {}
    for t, v in sorted(roh.items()):
        d = datetime.datetime.fromtimestamp(t / 1000, TZ)
        tage.setdefault(d.date().isoformat(), {}).setdefault(d.hour, []).append(v / 10)      # Euro je MWh -> Cent je kWh
    return {k: [round(sum(h[i]) / len(h[i]), 2) if i in h else None for i in range(24)] for k, h in tage.items()}


def zahl(v):
    return ('%.1f' % v).replace('.', ',').replace('-', '−')


def satz(datum, werte, wort):
    w = [(v, i) for i, v in enumerate(werte) if v is not None]
    if len(w) < 20:
        return ''
    mittel = sum(v for v, _ in w) / len(w)
    lo, hi = min(w), max(w)
    d = datetime.date.fromisoformat(datum)
    return ('<b>%s, %s, %s:</b> Strom kostet an der Börse im Schnitt %s&nbsp;ct pro kWh. Am günstigsten ist die Stunde von %d bis %d&nbsp;Uhr '
            '(%s&nbsp;ct), am teuersten die von %d bis %d&nbsp;Uhr (%s&nbsp;ct).'
            % (wort, TAGE[d.weekday()], d.strftime('%d.%m.%Y'), zahl(mittel), lo[1], lo[1] + 1, zahl(lo[0]), hi[1], hi[1] + 1, zahl(hi[0])))


def main():
    try:
        tage = holen()
    except Exception as e:                      # SMARD nicht erreichbar: nichts ändern
        print('SMARD nicht erreichbar:', e)
        return 0
    jetzt = datetime.datetime.now(TZ)
    heute = jetzt.date().isoformat()
    morgen = (jetzt.date() + datetime.timedelta(days=1)).isoformat()
    if heute not in tage or sum(v is not None for v in tage[heute]) < 20:
        print('keine vollständigen Werte für heute, nichts geändert')
        return 0
    ab = (jetzt.date() - datetime.timedelta(days=8)).isoformat()
    tage = {k: v for k, v in sorted(tage.items()) if ab <= k <= morgen and sum(x is not None for x in v) >= 20}
    ziel = ROOT / 'assets' / 'strompreis.json'
    alt = json.loads(ziel.read_text(encoding='utf-8')) if ziel.exists() else {}
    neu = alt.get('tage') != tage
    stand = jetzt if neu else datetime.datetime.fromisoformat(alt['stand'])     # ohne neue Preise bleibt der Stand, damit nichts unnötig neu gespeichert wird
    if neu:
        daten = {'stand': jetzt.strftime('%Y-%m-%dT%H:%M'), 'einheit': 'ct/kWh, Börsenpreis ohne Steuern, Abgaben und Netzentgelt',
                 'quelle': 'Bundesnetzagentur | SMARD.de, CC BY 4.0', 'zone': 'DE-LU', 'tage': tage}
        ziel.write_text(json.dumps(daten, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    seite = ROOT / 'strompreis-heute.html'
    if seite.exists():
        s = seite.read_text(encoding='utf-8')
        teile = [satz(heute, tage[heute], 'Heute')]
        if morgen in tage:
            teile.append(satz(morgen, tage[morgen], 'Morgen'))
        block = ('<!--SP-->\n<p class="sp-st" id="sp-st">%s <span class="sp-stand">Stand: %s Uhr.</span></p>\n<!--/SP-->'
                 % (' '.join(t for t in teile if t), stand.strftime('%d.%m.%Y, %H:%M')))
        s2 = re.sub(r'<!--SP-->.*?<!--/SP-->', lambda m: block, s, flags=re.S)
        if s2 != s:
            seite.write_text(s2, encoding='utf-8')
        sm = ROOT / 'sitemap.xml'
        x = sm.read_text(encoding='utf-8')
        x2 = re.sub(r'(<loc>https://strom-daheim\.de/strompreis-heute\.html</loc>\s*<lastmod>)[^<]*', lambda m: m.group(1) + heute, x)
        if x2 != x:
            sm.write_text(x2, encoding='utf-8')
    print('Preise aktualisiert:' if neu else 'Preise unverändert:', ', '.join(tage))
    return 0


if __name__ == '__main__':
    sys.exit(main())
