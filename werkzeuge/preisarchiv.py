"""Strompreis-Archiv: Monatsseiten mit den Börsenstrompreisen (strompreis/JJJJ-MM.html), Übersicht strompreis-archiv.html
(Block zwischen <!--PA--> und <!--/PA-->) und die Stundenwerte als CSV zum Herunterladen (assets/strompreis/JJJJ-MM.csv).

Quelle: Bundesnetzagentur | SMARD.de, Day-Ahead-Preis Deutschland/Luxemburg, Lizenz CC BY 4.0. Die Quellenangabe muss auf den Seiten bleiben.
Die Werte liegen je Jahr in werkzeuge/preisarchiv/JJJJ.json ({Datum: [24 Werte in ct/kWh]}). werkzeuge/strompreis.py ruft
merken() und seiten() bei jedem Lauf auf (GitHub-Ablauf „Strompreise holen“), Agenten müssen nichts tun.
Von Hand:  python3 werkzeuge/preisarchiv.py          Seiten aus den gespeicherten Werten neu bauen
           python3 werkzeuge/preisarchiv.py nachholen fehlende Tage seit START von SMARD holen (rund 100 Abrufe)"""
import json, re, sys, html, pathlib, datetime, calendar
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'werkzeuge'))
SITE = 'https://strom-daheim.de'
DIR = ROOT / 'werkzeuge' / 'preisarchiv'
START = '2025-01-01'
MON = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']
QUELLE = 'Bundesnetzagentur | SMARD.de'


def z(v, n=1):
    return (('%.' + str(n) + 'f') % v).replace('.', ',').replace('-', '−')


def laden():
    d = {}
    for f in sorted(DIR.glob('2*.json')):
        d.update(json.loads(f.read_text(encoding='utf-8')))
    return d


def merken(tage):
    """Nimmt {Datum: [24 Werte]} auf; nur vollständige, vergangene oder heutige Tage. Gibt True zurück, wenn sich etwas geändert hat."""
    DIR.mkdir(exist_ok=True)
    heute = datetime.date.today().isoformat(); neu = {}
    for k, v in tage.items():
        if START <= k <= heute and len(v) == 24 and sum(x is not None for x in v) >= 23:
            neu.setdefault(k[:4], {})[k] = v
    geaendert = False
    for jahr, werte in neu.items():
        f = DIR / (jahr + '.json'); alt = json.loads(f.read_text(encoding='utf-8')) if f.exists() else {}
        zus = dict(alt); zus.update(werte)
        if zus != alt:
            f.write_text('{\n' + ',\n'.join('"%s":%s' % (k, json.dumps(zus[k], separators=(',', ':'))) for k in sorted(zus)) + '\n}\n', encoding='utf-8'); geaendert = True
    return geaendert


def nachholen():
    import strompreis, zoneinfo
    TZ = zoneinfo.ZoneInfo('Europe/Berlin'); idx = strompreis.get(strompreis.BASE + 'index_hour.json')['timestamps']
    ab = datetime.datetime.fromisoformat(START).timestamp() * 1000 - 8 * 86400000; roh = {}
    for ts in [t for t in idx if t >= ab]:
        try:
            for t, v in strompreis.get(strompreis.BASE + '4169_DE-LU_hour_%d.json' % ts)['series']:
                if v is not None:
                    roh[t] = v
        except Exception as e:
            print('Woche', ts, 'fehlt:', e)
    tage = {}
    for t, v in sorted(roh.items()):
        d = datetime.datetime.fromtimestamp(t / 1000, TZ)
        tage.setdefault(d.date().isoformat(), {}).setdefault(d.hour, []).append(v / 10)
    print('nachgeholt:', len(tage), 'Tage, geändert:', merken({k: [round(sum(h[i]) / len(h[i]), 2) if i in h else None for i in range(24)] for k, h in tage.items()}))


def kennzahlen(tage):
    """tage: sortierte Liste (Datum, [24]). Liefert Mittel, Extremwerte, negative Stunden, Mittel je Tagesstunde, günstigstes 3-Stunden-Fenster."""
    alle = [(v, d, h) for d, w in tage for h, v in enumerate(w) if v is not None]
    je_h = []
    for h in range(24):
        x = [w[h] for d, w in tage if w[h] is not None]; je_h.append(sum(x) / len(x) if x else 0)
    fen = min(range(22), key=lambda h: je_h[h] + je_h[h + 1] + je_h[h + 2]); teuer = max(range(22), key=lambda h: je_h[h] + je_h[h + 1] + je_h[h + 2])
    return {'mittel': sum(v for v, _, _ in alle) / len(alle), 'min': min(alle), 'max': max(alle), 'neg': sum(1 for v, _, _ in alle if v < 0), 'n': len(alle),
            'je_h': je_h, 'fen': fen, 'fen_v': sum(je_h[fen:fen + 3]) / 3, 'teuer': teuer, 'teuer_v': sum(je_h[teuer:teuer + 3]) / 3,
            'tag': [(d, sum(x for x in w if x is not None) / sum(1 for x in w if x is not None), min(x for x in w if x is not None), max(x for x in w if x is not None)) for d, w in tage]}


def balken(werte, labels, titel, cls='', marke=None):
    """Einfaches Balkendiagramm als SVG. werte: Zahlen, labels: Text je Balken (oder ''), titel: Text je Balken für den Tooltip."""
    n = len(werte); W = 720; H = 250; L = 44; T = 12; B = 26; pw = W - L - 6; ph = H - T - B
    lo = min(0, min(werte)); hi = max(werte); hi = hi if hi > 0 else 1
    span = hi - lo; step = next((s for s in (0.5, 1, 2, 5, 10, 20, 50) if span / s <= 6), 100)
    import math
    lo = math.floor(lo / step) * step; hi = math.ceil(hi / step) * step
    y = lambda v: T + ph * (1 - (v - lo) / (hi - lo)); bw = pw / n; gap = min(2, bw * .2); out = []
    g = lo
    while g <= hi + 1e-9:
        out.append('<line class="g%s" x1="%d" x2="%d" y1="%.1f" y2="%.1f"/><text x="%d" y="%.1f" text-anchor="end">%s</text>' % (' z' if abs(g) < 1e-9 else '', L, W - 6, y(g), y(g), L - 6, y(g) + 4, z(g, 0 if step >= 1 else 1)))
        g += step
    for i, v in enumerate(werte):
        x = L + i * bw + gap / 2; w = bw - gap; y0 = y(0); yv = y(v); r = min(3, w / 2)
        if v >= 0:
            h = max(1, y0 - yv); d = 'M%.1f %.1fV%.1fq0 %.1f %.1f %.1fh%.1fq%.1f 0 %.1f %.1fV%.1fz' % (x, y0, yv + r, -r, r, -r, w - 2 * r, r, r, r, y0) if h > r else 'M%.1f %.1fh%.1fv%.1fh%.1fz' % (x, y0, w, -h, -w)
        else:
            h = max(1, yv - y0); d = 'M%.1f %.1fh%.1fv%.1fh%.1fz' % (x, y0, w, h, -w)
        out.append('<path class="b%s%s" d="%s"><title>%s</title></path>' % (' n' if v < 0 else '', (' ' + marke[i]) if marke and marke[i] else '', d, html.escape(titel[i])))
        if labels[i]:
            out.append('<text x="%.1f" y="%d" text-anchor="middle">%s</text>' % (x + w / 2, H - 8, labels[i]))
    return '<svg class="pa-svg %s" viewBox="0 0 %d %d" role="img" aria-label="%s">%s</svg>' % (cls, W, H, 'Balkendiagramm, die Werte stehen in der Tabelle darunter', ''.join(out))


def url(ym):
    return '/strompreis/%s.html' % ym


def name(ym):
    return '%s %s' % (MON[int(ym[5:7]) - 1], ym[:4])


def monat_seite(ym, tage, alle_k, kopf, fuss, goat, heute):
    import site_header
    k = alle_k[ym]; jahr, mon = int(ym[:4]), int(ym[5:7]); voll = len(tage) == calendar.monthrange(jahr, mon)[1]
    laufend = ym == heute[:7]; nm = name(ym); u = SITE + url(ym)
    vm = (datetime.date(jahr, mon, 1) - datetime.timedelta(days=1)).strftime('%Y-%m'); vj = '%d-%02d' % (jahr - 1, mon)
    nx = (datetime.date(jahr, mon, 28) + datetime.timedelta(days=7)).strftime('%Y-%m')
    title = 'Strompreis %s: Börsenpreis je Tag und Stunde – Strom-Daheim' % nm
    desc = 'Börsenstrompreis im %s: im Schnitt %s ct pro kWh, günstigste und teuerste Stunde, Verlauf je Tag und die Stundenwerte als CSV.' % (nm, z(k['mittel']))
    head = kopf
    head = re.sub(r'<title>.*?</title>', lambda m: '<title>%s</title>' % html.escape(title), head, flags=re.S)
    head = re.sub(r'<meta property="og:title" content="[^"]*">', lambda m: '<meta property="og:title" content="%s">' % html.escape(title, quote=True), head)
    head = re.sub(r'<meta (name="description"|property="og:description") content="[^"]*">', lambda m: '<meta %s content="%s">' % (m.group(1), html.escape(desc, quote=True)), head)
    head = head.replace(SITE + '/strompreis-archiv.html', u)
    head = re.sub(r'<script type="application/ld\+json" id="ld">.*?</script>\n?', '', head, flags=re.S)
    org = {'@type': 'Organization', 'name': 'Strom-Daheim', 'url': SITE + '/'}; letzter = tage[-1][0]
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'Article', 'headline': 'Strompreis im %s' % nm, 'name': title, 'description': desc, 'inLanguage': 'de-DE', 'url': u, 'mainEntityOfPage': u,
         'datePublished': tage[0][0], 'dateModified': letzter, 'image': SITE + '/assets/og/strompreis-heute.jpg', 'author': org, 'publisher': org},
        {'@type': 'Dataset', 'name': 'Börsenstrompreis Deutschland/Luxemburg, Stundenwerte %s' % nm, 'description': 'Day-Ahead-Preis der Gebotszone Deutschland/Luxemburg je Stunde in Cent pro Kilowattstunde, ohne Steuern, Abgaben und Netzentgelt.',
         'url': u, 'license': 'https://creativecommons.org/licenses/by/4.0/', 'temporalCoverage': '%s/%s' % (tage[0][0], letzter), 'spatialCoverage': 'Deutschland und Luxemburg',
         'creator': {'@type': 'Organization', 'name': 'Bundesnetzagentur | SMARD.de', 'url': 'https://www.smard.de/'}, 'isBasedOn': 'https://www.smard.de/',
         'distribution': {'@type': 'DataDownload', 'encodingFormat': 'text/csv', 'contentUrl': SITE + '/assets/strompreis/%s.csv' % ym}},
        {'@type': 'BreadcrumbList', 'itemListElement': [{'@type': 'ListItem', 'position': 1, 'name': 'Strom-Daheim', 'item': SITE + '/'},
                                                        {'@type': 'ListItem', 'position': 2, 'name': 'Strompreis-Archiv', 'item': SITE + '/strompreis-archiv.html'},
                                                        {'@type': 'ListItem', 'position': 3, 'name': nm, 'item': u}]}]}
    head += '\n<script type="application/ld+json" id="ld">%s</script>' % json.dumps(ld, ensure_ascii=False).replace('</', '<\\/')
    dde = lambda d: '%s.%s.' % (d[8:10], d[5:7])
    vergl = []
    for other, wort in ((vm, 'als im ' + name(vm)), (vj, 'als im ' + name(vj))):
        if other in alle_k and not laufend:
            diff = (k['mittel'] / alle_k[other]['mittel'] - 1) * 100 if alle_k[other]['mittel'] > 0 else None
            if diff is not None:
                vergl.append('%s&nbsp;%% %s %s (%s&nbsp;ct)' % (z(abs(diff), 0), 'mehr' if diff > 0 else 'weniger', wort, z(alle_k[other]['mittel'])) if abs(diff) >= 0.5 else 'so viel wie im ' + name(other))
    intro = ('Im %s kostete Strom an der Börse im Schnitt <b>%s&nbsp;ct pro kWh</b>.' % (nm, z(k['mittel'])) if not laufend else
             'Im %s kostet Strom an der Börse bisher im Schnitt <b>%s&nbsp;ct pro kWh</b> (Stand %s%s, %d Tage).' % (nm, z(k['mittel']), dde(letzter), letzter[:4], len(tage)))
    if vergl:
        intro += ' Das ist ' + ' und '.join(vergl) + '.'
    tb = ''.join('<tr><th scope="row">%s%s</th><td>%s</td><td>%s</td><td>%s</td></tr>' % (dde(d), d[:4], z(m), z(lo), z(hi)) for d, m, lo, hi in k['tag'])
    tagchart = balken([t[1] for t in k['tag']], [str(int(t[0][8:10])) if int(t[0][8:10]) in (1, 5, 10, 15, 20, 25, 30) else '' for t in k['tag']], ['%s%s: %s ct' % (dde(t[0]), t[0][:4], z(t[1])) for t in k['tag']])
    hchart = balken(k['je_h'], [str(h) if h % 3 == 0 else '' for h in range(24)], ['%d bis %d Uhr: %s ct' % (h, h + 1, z(v)) for h, v in enumerate(k['je_h'])], 'h')
    neg = ('An %d von %d Stunden war der Preis negativ.' % (k['neg'], k['n']) if k['neg'] else 'Negative Preise gab es in diesem Monat nicht.')
    nav = ''.join('<a href="%s">%s %s</a>' % (url(o), pfeil, name(o)) for o, pfeil in ((vm, '←'), (nx, '→')) if o in alle_k)
    main = '''<main id="main">
<div class="pah"><div class="wrap">
<span class="eyebrow"><a href="/strompreis-archiv.html">Strompreis-Archiv</a> · %(status)s</span>
<h1>Strompreis im %(nm)s</h1>
<p class="lede">%(intro)s</p>
<div class="pa-st">
<div><b>%(mittel)s ct</b><span>Durchschnitt pro kWh</span></div>
<div><b>%(minv)s ct</b><span>günstigste Stunde: %(mind)s, %(minh)d bis %(minh1)d Uhr</span></div>
<div><b>%(maxv)s ct</b><span>teuerste Stunde: %(maxd)s, %(maxh)d bis %(maxh1)d Uhr</span></div>
<div><b>%(neg)d</b><span>Stunden mit negativem Preis</span></div>
</div>
<p class="pa-q">Börsenpreis ohne Steuern, Abgaben und Netzentgelt. Daten: %(quelle)s.</p>
</div></div>
<section class="band" id="tage"><div class="wrap">
<div class="head"><span class="eyebrow">Verlauf</span><h2>Jeder Tag im Überblick.</h2><p class="lede">Durchschnittlicher Börsenpreis je Tag in Cent pro kWh.</p></div>
<div class="pa-card">%(tagchart)s
<details class="pa-tbl"><summary>Alle Tage als Tabelle</summary><div class="pa-tw" tabindex="0" role="region" aria-label="Tabelle, seitlich verschiebbar"><table><thead><tr><th scope="col">Tag</th><th scope="col">Schnitt</th><th scope="col">niedrigste Stunde</th><th scope="col">höchste Stunde</th></tr></thead><tbody>%(tb)s</tbody></table></div></details></div>
</div></section>
<section id="stunden"><div class="wrap">
<div class="head"><span class="eyebrow">Tageszeit</span><h2>Wann war Strom am günstigsten?</h2><p class="lede">Durchschnitt je Stunde des Tages über den ganzen Monat, in Cent pro kWh.</p></div>
<div class="pa-card">%(hchart)s</div>
<p class="pa-txt">Im Schnitt des Monats war Strom zwischen <b>%(fen)d und %(fen3)d Uhr</b> am günstigsten (%(fenv)s&nbsp;ct) und zwischen %(teu)d und %(teu3)d Uhr am teuersten (%(teuv)s&nbsp;ct). %(negsatz)s Wer Waschmaschine, Spülmaschine oder das Laden des E-Autos in die günstigen Stunden legt, zahlt mit einem dynamischen Tarif weniger. Die beste Startzeit für heute findet der <a href="/strompreis-heute.html#fenster">Geräte-Planer</a>.</p>
</div></section>
<section class="band" id="einordnung"><div class="wrap read">
<div class="head"><span class="eyebrow">Einordnung</span><h2>Was die Zahl bedeutet.</h2></div>
<p>Der Börsenpreis ist der Großhandelspreis für Strom, der am Vortag für jede Stunde festgelegt wird. Haushalte zahlen deutlich mehr: Dazu kommen Netzentgelt, Steuern, Umlagen und der Aufschlag des Anbieters. Bei einem festen Tarif merkst du von den Schwankungen nichts. Bei einem <a href="/stromtarif.html#dynamisch">dynamischen Tarif</a> gehen sie Stunde für Stunde in deine Rechnung ein.</p>
<p>Die Werte sind Mittel je Stunde. Seit Oktober 2025 wird der Preis an der Börse in Viertelstunden gebildet, die Abrechnung deines Anbieters kann deshalb leicht abweichen.</p>
</div></section>
<section id="daten"><div class="wrap read">
<div class="head"><span class="eyebrow">Daten</span><h2>Zum Herunterladen.</h2></div>
<p>Alle Stundenwerte dieses Monats als Tabelle für Excel und Co.: <a href="/assets/strompreis/%(ym)s.csv" download>strompreis-%(ym)s.csv</a>. Spalten: Datum, Stunde, Cent pro kWh.</p>
<p>Die Daten stammen von der Bundesnetzagentur (<a href="https://www.smard.de/" target="_blank" rel="noopener">SMARD.de</a>) und stehen unter der Lizenz <a href="https://creativecommons.org/licenses/by/4.0/deed.de" target="_blank" rel="noopener">CC BY 4.0</a>. Du darfst sie frei verwenden, wenn du die Quelle nennst: „%(quelle)s“. Über einen Link auf diese Seite freuen wir uns.</p>
<nav class="pa-nav" aria-label="Andere Monate">%(nav)s<a href="/strompreis-archiv.html">Alle Monate</a><a href="/strompreis-heute.html">Strompreis heute</a></nav>
</div></section>
</main>
''' % {'status': 'laufender Monat, täglich neu' if laufend else ('vollständig' if voll else 'Daten ab %s' % dde(tage[0][0])), 'nm': nm, 'intro': intro, 'mittel': z(k['mittel']),
       'minv': z(k['min'][0]), 'mind': dde(k['min'][1]), 'minh': k['min'][2], 'minh1': k['min'][2] + 1, 'maxv': z(k['max'][0]), 'maxd': dde(k['max'][1]), 'maxh': k['max'][2], 'maxh1': k['max'][2] + 1,
       'neg': k['neg'], 'quelle': QUELLE, 'tagchart': tagchart, 'tb': tb, 'hchart': hchart, 'fen': k['fen'], 'fen3': k['fen'] + 3, 'fenv': z(k['fen_v']), 'teu': k['teuer'], 'teu3': k['teuer'] + 3, 'teuv': z(k['teuer_v']),
       'negsatz': neg, 'ym': ym, 'nav': nav}
    return head + '\n</head><body>\n' + site_header.block('strompreis-archiv').replace(' aria-current="page"', '') + main + fuss + '\n' + goat + '</body></html>\n'


def uebersicht(alle_k, heute):
    jahre = sorted({ym[:4] for ym in alle_k}, reverse=True); out = []
    for j in jahre:
        ms = [ym for ym in sorted(alle_k) if ym[:4] == j]; mx = max(alle_k[ym]['mittel'] for ym in alle_k)
        gew = sum(alle_k[ym]['mittel'] * alle_k[ym]['n'] for ym in ms) / sum(alle_k[ym]['n'] for ym in ms)
        rows = ''.join('<a href="%s"><b>%s</b><span class="pa-bar"><i style="width:%.1f%%"></i></span><em>%s ct</em></a>' % (url(ym), MON[int(ym[5:7]) - 1] + (' (läuft)' if ym == heute[:7] else ''), max(2, alle_k[ym]['mittel'] / mx * 100), z(alle_k[ym]['mittel'])) for ym in reversed(ms))
        out.append('<div class="pa-year"><h3>%s <span>Schnitt %s%s&nbsp;ct pro kWh</span></h3><div class="pa-months">%s</div></div>' % (j, 'bisher ' if j == heute[:4] else '', z(gew), rows))
    return ('<!--PA-->\n<section class="band" id="monate"><div class="wrap">\n<div class="head"><span class="eyebrow">%d Monate</span><h2>Monat für Monat.</h2><p class="lede">Durchschnittlicher Börsenpreis in Cent pro kWh. Tipp auf einen Monat für Tage, Stunden und Daten.</p></div>\n%s\n</div></section>\n<!--/PA-->'
            % (len(alle_k), ''.join(out)))


def seiten():
    import fusszeile
    f0 = ROOT / 'strompreis-archiv.html'
    if not f0.exists():
        print('strompreis-archiv.html fehlt, nichts gebaut'); return
    d = laden()
    if not d:
        print('Strompreis-Archiv: keine Werte gespeichert'); return
    heute = datetime.date.today().isoformat(); je = {}
    for k in sorted(d):
        je.setdefault(k[:7], []).append((k, d[k]))
    alle_k = {ym: kennzahlen(t) for ym, t in je.items()}
    s = f0.read_text(encoding='utf-8')
    s2 = re.sub(r'<!--PA-->.*?<!--/PA-->', lambda m: uebersicht(alle_k, heute), s, flags=re.S)
    if s2 != s:
        f0.write_text(s2, encoding='utf-8'); s = s2
    kopf = s[:s.index('</head>')].rstrip('\n')
    fuss = '<footer><div class="wrap">\n<p>Alle Zahlen ohne Gewähr. Börsenpreise: Bundesnetzagentur | SMARD.de, CC BY 4.0.</p>\n' + fusszeile.block('') + '\n</div></footer>'
    m = re.search(r'<script>\n/\* Besucherzähler.*?</script>\n', s, flags=re.S); goat = m.group(0) if m else ''
    out = ROOT / 'strompreis'; out.mkdir(exist_ok=True); csvdir = ROOT / 'assets' / 'strompreis'; csvdir.mkdir(parents=True, exist_ok=True); n = 0
    for ym, tage in je.items():
        t = monat_seite(ym, tage, alle_k, kopf, fuss, goat, heute); f = out / (ym + '.html')
        if not f.exists() or f.read_text(encoding='utf-8') != t:
            f.write_text(t, encoding='utf-8'); n += 1
        c = 'Datum;Stunde;Cent pro kWh\n' + ''.join('%s;%d;%s\n' % (dd, h, ('%.2f' % v).replace('.', ',')) for dd, w in tage for h, v in enumerate(w) if v is not None)
        c = '# Quelle: Bundesnetzagentur | SMARD.de, Lizenz CC BY 4.0. Day-Ahead-Preis Deutschland/Luxemburg ohne Steuern, Abgaben und Netzentgelt. Aufbereitet von strom-daheim.de\n' + c
        cf = csvdir / (ym + '.csv')
        if not cf.exists() or cf.read_text(encoding='utf-8') != c:
            cf.write_text(c, encoding='utf-8')
    sm = ROOT / 'sitemap.xml'; x = sm.read_text(encoding='utf-8')
    for ym, tage in je.items():
        loc = SITE + url(ym); last = tage[-1][0]
        if '<loc>%s</loc>' % loc not in x:
            x = x.replace('</urlset>', '<url><loc>%s</loc><lastmod>%s</lastmod></url></urlset>' % (loc, last))
        else:
            x = re.sub(r'(<loc>%s</loc>\s*<lastmod>)[^<]*' % re.escape(loc), lambda mm: mm.group(1) + last, x)
    x = re.sub(r'(<loc>%s/strompreis-archiv\.html</loc>\s*<lastmod>)[^<]*' % re.escape(SITE), lambda mm: mm.group(1) + max(d), x)
    if x != sm.read_text(encoding='utf-8'):
        sm.write_text(x, encoding='utf-8')
    print('Strompreis-Archiv: %d Monate, %d Seiten neu geschrieben' % (len(je), n))


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'nachholen':
        nachholen()
    seiten()
