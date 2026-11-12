"""Fußzeile in Spalten nach Themen (seit 11.11.2026, Design-Agent).

Baut den Linkblock <div class="fl fc"> in ALLEN Seiten neu (außer Impressum und Datenschutz, die keinen haben).
Die Spalte einer Seite kommt aus der Ratgeber-Galerie der Startseite: erstes Thema in data-k der Kachel
(solar, auto, haushalt, heizen, tarif). Linktexte stehen unten in TEXTE.

NEUE SEITE: Kachel mit data-k auf der Startseite einfügen, hier in TEXTE einen kurzen Linktext ergänzen,
dann  python3 werkzeuge/fusszeile.py  ausführen. Fehlt der Text, nimmt das Skript den Titel aus der Kachel.
"""
import re, pathlib, html as H

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPALTEN = [('solar', 'Solar und Balkon'), ('auto', 'E-Auto'), ('haushalt', 'Haushalt'), ('heizen', 'Heizen und Lüften'), ('tarif', 'Tarif und Zähler')]
TEXTE = {  # Reihenfolge innerhalb einer Spalte = Reihenfolge hier
    '/': 'Balkonkraftwerk-Rechner', '/anleitung-balkonkraftwerk.html': 'Balkonkraftwerk montieren', '/pv-anlage.html': 'Solaranlage aufs Dach',
    '/powerstation.html': 'Powerstation und Notstrom',
    '/e-auto.html': 'E-Auto laden', '/anleitung-wallbox.html': 'Wallbox-Anleitung', '/solar-laden.html': 'Mit Solarstrom laden',
    '/stromfresser.html': 'Stromfresser finden', '/energielabel.html': 'Energielabel', '/kochen.html': 'Kochen mit wenig Strom',
    '/kuehlschrank.html': 'Kühlschrank einstellen', '/spuelmaschine.html': 'Spülmaschine', '/waschmaschine.html': 'Waschmaschine', '/waesche-trocknen.html': 'Wäsche trocknen',
    '/backen.html': 'Plätzchen backen', '/weihnachtsbeleuchtung.html': 'Weihnachtsbeleuchtung', '/weihnachten-strom.html': 'Stromkosten an Weihnachten',
    '/black-friday.html': 'Black Friday',
    '/waermepumpe.html': 'Wärmepumpe', '/heizluefter.html': 'Heizlüfter', '/klimageraet.html': 'Klimagerät', '/lueften.html': 'Richtig lüften',
    '/stromtarif.html': 'Stromtarif wechseln', '/smart-meter.html': 'Smart Meter',
}
EXTRA = {'/': 'solar'}  # Seiten ohne eigene Kachel


def galerie():
    t = (ROOT / 'index.html').read_text()
    hub = t[t.index('id="alles"'):]
    out = {}
    for m in re.finditer(r'<a class="[^"]*" href="(/[^"#]*\.html)" data-k="([^"]+)">.*?<b>(.*?)</b>', hub, re.S):
        if m.group(1) == '/seite.html':
            continue
        out.setdefault(m.group(1), (m.group(2).split()[0], re.sub(r'<[^>]+>', '', m.group(3)).strip()))
    return out


def block(cur):
    g = galerie()
    pages = {h: (k, TEXTE.get(h, t)) for h, (k, t) in g.items()}
    for h, k in EXTRA.items():
        pages[h] = (k, TEXTE[h])
    order = list(TEXTE)
    cols = []
    for k, lab in SPALTEN:
        hs = sorted([h for h, (kk, _) in pages.items() if kk == k], key=lambda h: order.index(h) if h in order else 999)
        if hs:
            cols.append('<div><p class="fc-h">%s</p>%s</div>' % (lab, ''.join(
                '<a href="%s"%s>%s</a>' % (h, ' aria-current="page"' if h == cur else '', H.escape(pages[h][1], quote=False)) for h in hs)))
    cols.append('<div><p class="fc-h">Strom-Daheim</p><a href="/so-arbeiten-wir.html"%s>So arbeiten wir</a><a href="/impressum.html">Impressum</a>'
                '<a href="/datenschutz.html">Datenschutz</a><a href="https://stil-daheim.de/">Schwesterseite Stil-Daheim</a></div>'
                % (' aria-current="page"' if cur == '/so-arbeiten-wir.html' else ''))
    return '<nav class="fl fc" aria-label="Alle Seiten">%s</nav><p class="fc-c">© 2026 Strom-Daheim</p>' % ''.join(cols)


def main():
    n = 0
    for f in sorted(ROOT.glob('*.html')):
        if f.name in ('impressum.html', 'datenschutz.html'):
            continue
        t = f.read_text()
        cur = '/' if f.name == 'index.html' else '/' + f.name
        new, k = re.subn(r'<div class="fl">.*?</div>|<nav class="fl fc".*?</nav><p class="fc-c">.*?</p>', lambda m: block(cur), t, count=1, flags=re.S)
        if k and new != t:
            f.write_text(new); n += 1
    print('Fußzeile erneuert in', n, 'Seiten')


if __name__ == '__main__':
    main()
