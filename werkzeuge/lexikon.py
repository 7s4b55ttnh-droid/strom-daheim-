"""Lexikon: baut aus werkzeuge/lexikon.json die Übersicht (Block zwischen <!--LEX--> und <!--/LEX--> in lexikon.html),
je Begriff eine Seite lexikon/<slug>.html und assets/lexikon.json für die Erklärungen beim Antippen (site.js).
Aufruf: python3 werkzeuge/lexikon.py. Läuft auch am Ende von werkzeuge/fusszeile.py, damit Menü und Fußzeile passen."""
import re, json, html, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'werkzeuge'))
import site_header, fusszeile
SITE = 'https://strom-daheim.de'


def z(n):
    return ('%d' % round(n)).replace(',', '.') if n < 1000 else ('{:,}'.format(round(n))).replace(',', '.')


def daten():
    d = json.loads((ROOT / 'werkzeuge/lexikon.json').read_text(encoding='utf-8'))
    werte = {}
    try:
        A = json.loads((ROOT / 'werkzeuge/pvdaten/atlas.json').read_text(encoding='utf-8'))['regionen']
        v = [r['dach'] for r in A.values()]; werte = {'ertrag_min': z(min(v)), 'ertrag_max': z(max(v))}
    except Exception:
        werte = {'ertrag_min': 'rund 1.000', 'ertrag_max': '1.250'}
    for b in d['begriffe']:
        for k in ('was', 'wichtig'):
            if '%(' in b[k]:
                b[k] = b[k] % werte
    d['begriffe'].sort(key=lambda b: b['name'].lower().replace('ä', 'a').replace('ö', 'o').replace('ü', 'u'))
    return d


def url(b):
    return '/lexikon/%s.html' % b['slug']


def block(d):
    k = ''.join('<a href="%s"><b>%s</b><span>%s</span></a>' % (url(b), html.escape(b['name']), html.escape(b['kurz'])) for b in d['begriffe'])
    return ('<!--LEX-->\n<section class="band" id="begriffe"><div class="wrap">\n<div class="head"><span class="eyebrow">%d Begriffe</span><h2>Von A bis Z.</h2></div>\n'
            '<div class="lx-grid">%s</div>\n<p class="lx-none" id="lx-none" hidden>Dazu haben wir noch keinen Eintrag.</p>\n</div></section>\n<!--/LEX-->' % (len(d['begriffe']), k))


def seite(b, d, kopf, fuss, goat):
    by = {x['slug']: x for x in d['begriffe']}
    u = SITE + url(b); kurzname = re.sub(r'\s*\(.*?\)', '', b['name'])
    title = '%s: einfach erklärt – Strom-Daheim' % b['name']
    desc = b['kurz']
    head = kopf
    head = re.sub(r'<title>.*?</title>', lambda m: '<title>%s</title>' % html.escape(title), head, flags=re.S)
    head = re.sub(r'<meta property="og:title" content="[^"]*">', lambda m: '<meta property="og:title" content="%s">' % html.escape(title, quote=True), head)
    head = re.sub(r'<meta (name="description"|property="og:description") content="[^"]*">', lambda m: '<meta %s content="%s">' % (m.group(1), html.escape(desc, quote=True)), head)
    head = head.replace(SITE + '/lexikon.html', u)
    head = re.sub(r'<script type="application/ld\+json" id="ld">.*?</script>\n?', '', head, flags=re.S)
    org = {'@type': 'Organization', 'name': 'Strom-Daheim', 'url': SITE + '/'}
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'DefinedTerm', '@id': u + '#begriff', 'name': b['name'], 'description': b['kurz'], 'url': u,
         'inDefinedTermSet': {'@type': 'DefinedTermSet', 'name': 'Lexikon von Strom-Daheim', 'url': SITE + '/lexikon.html'}},
        {'@type': 'Article', 'headline': '%s: einfach erklärt' % b['name'], 'name': title, 'description': desc, 'inLanguage': 'de-DE', 'url': u, 'mainEntityOfPage': u,
         'datePublished': b.get('seit', d['stand']), 'dateModified': d['stand'], 'image': SITE + '/assets/og/lexikon.jpg', 'about': {'@id': u + '#begriff'}, 'author': org, 'publisher': org},
        {'@type': 'BreadcrumbList', 'itemListElement': [{'@type': 'ListItem', 'position': 1, 'name': 'Strom-Daheim', 'item': SITE + '/'},
                                                        {'@type': 'ListItem', 'position': 2, 'name': 'Lexikon', 'item': SITE + '/lexikon.html'},
                                                        {'@type': 'ListItem', 'position': 3, 'name': kurzname, 'item': u}]}]}
    head += '\n<script type="application/ld+json" id="ld">%s</script>' % json.dumps(ld, ensure_ascii=False).replace('</', '<\\/')
    links = ''.join('<a href="%s"%s>%s</a>' % (h, ' class="pri"' if i == 0 else '', html.escape(t)) for i, (h, t) in enumerate(b.get('links', [])))
    verw = ''.join('<a href="%s"><b>%s</b><span>%s</span></a>' % (url(by[s]), html.escape(by[s]['name']), html.escape(by[s]['kurz'])) for s in b.get('verwandt', []) if s in by)
    bsp = '<div class="lx-ex"><b>Ein Beispiel</b>%s</div>' % html.escape(b['beispiel']) if b.get('beispiel') else ''
    tag = d['stand']; stand = '%s.%s.%s' % (tag[8:10], tag[5:7], tag[:4])
    main = ('<main id="main">\n<div class="lxh"><div class="wrap read">\n<span class="eyebrow"><a href="/lexikon.html">Lexikon</a> · Stand %s</span>\n<h1>%s</h1>\n<p class="lx-def">%s</p>\n</div></div>\n'
            '<section class="band"><div class="wrap read">\n<div class="head"><h2>Was bedeutet %s?</h2></div>\n<p>%s</p>\n%s\n</div></section>\n'
            '<section><div class="wrap read">\n<div class="head"><h2>Warum das für dich zählt.</h2></div>\n<p>%s</p>\n<div class="lx-links">%s</div>\n</div></section>\n'
            % (stand, html.escape(b['name']), html.escape(b['kurz']), html.escape(kurzname), html.escape(b['was']), bsp, html.escape(b['wichtig']), links))
    if verw:
        main += '<section class="band"><div class="wrap">\n<div class="head"><span class="eyebrow">Verwandte Begriffe</span><h2>Passt dazu.</h2></div>\n<div class="lx-grid">%s</div>\n<p style="margin-top:22px"><a href="/lexikon.html">Alle Begriffe im Lexikon</a></p>\n</div></section>\n' % verw
    main += '</main>\n'
    return head + '\n</head><body>\n' + site_header.block('lexikon').replace(' aria-current="page"', '') + main + fuss + '\n' + goat + '</body></html>\n'


def main():
    f0 = ROOT / 'lexikon.html'
    if not f0.exists():
        print('lexikon.html fehlt, nichts gebaut'); return
    d = daten(); s = f0.read_text(encoding='utf-8')
    s2 = re.sub(r'<!--LEX-->.*?<!--/LEX-->', lambda m: block(d), s, flags=re.S)
    if s2 != s:
        f0.write_text(s2, encoding='utf-8'); s = s2
    kopf = s[:s.index('</head>')].rstrip('\n')
    fuss = '<footer><div class="wrap">\n<p>Alle Angaben sind allgemeine Erklärungen ohne Gewähr und ersetzen keine Beratung im Einzelfall.</p>\n' + fusszeile.block('') + '\n</div></footer>'
    m = re.search(r'<script>\n/\* Besucherzähler.*?</script>\n', s, flags=re.S); goat = m.group(0) if m else ''
    out = ROOT / 'lexikon'; out.mkdir(exist_ok=True); soll = set(); n = 0
    for b in d['begriffe']:
        f = out / (b['slug'] + '.html'); soll.add(f.name); t = seite(b, d, kopf, fuss, goat)
        if not f.exists() or f.read_text(encoding='utf-8') != t:
            f.write_text(t, encoding='utf-8'); n += 1
    for f in out.glob('*.html'):
        if f.name not in soll:
            f.unlink()
    tip = [{'n': b['name'], 'k': b['kurz'], 'u': url(b), 'w': b['w'], 'l': [x[0].split('#')[0] for x in b.get('links', [])]} for b in d['begriffe'] if b.get('w')]
    a = ROOT / 'assets/lexikon.json'; neu = json.dumps(tip, ensure_ascii=False, separators=(',', ':')) + '\n'
    if not a.exists() or a.read_text(encoding='utf-8') != neu:
        a.write_text(neu, encoding='utf-8')
    sm = ROOT / 'sitemap.xml'; x = sm.read_text(encoding='utf-8'); add = ''
    for b in d['begriffe']:
        loc = SITE + url(b)
        if '<loc>%s</loc>' % loc not in x:
            add += '<url><loc>%s</loc><lastmod>%s</lastmod></url>' % (loc, d['stand'])
    if add:
        sm.write_text(x.replace('</urlset>', add + '</urlset>'), encoding='utf-8')
    print('Lexikon: %d Begriffe, %d Seiten neu geschrieben, %d mit Erklärung im Text' % (len(d['begriffe']), n, len(tip)))


if __name__ == '__main__':
    main()
