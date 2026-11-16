"""Stromkosten je Gerät: baut aus werkzeuge/stromkosten.json die Sammelseite stromkosten.html (Block zwischen <!--SK--> und <!--/SK-->)
und je Gerät eine Seite stromkosten/<slug>.html („Was kostet … an Strom?“). Rechner: /stromkosten.js.
Aufruf: python3 werkzeuge/stromkosten.py. Läuft auch am Ende von werkzeuge/fusszeile.py, damit Menü und Fußzeile passen.
Die Geräte-Seiten bekommen KEINE Kachel auf der Startseite und KEINEN Menüeintrag, nur die Sammelseite."""
import re, json, html, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'werkzeuge'))
SITE = 'https://strom-daheim.de'
STAND = '2026-11-16'
PREISE = (25, 30, 35, 40)


def z(v, n=0):
    s = ('{:,.%df}' % n).format(v).replace(',', 'X').replace('.', ',').replace('X', '.')
    return s


def geld(eur):
    return (z(eur * 100, 1 if eur < 0.1 else 0) + '&nbsp;ct') if eur < 1 else (z(eur, 2 if eur < 100 else 0) + '&nbsp;€')


def rechne(g):
    """(kWh im Jahr, kWh je Einheit, Name der Einheit)"""
    if g['art'] == 'w':
        std = g['min'] / 60 if 'min' in g else g['h']; kw = g['w'] * g.get('anteil', 100) / 100 / 1000
        return kw * std * g['tage'], kw, 'Stunde'
    if g['art'] == 'gang':
        return g['kwh'] * g['proWoche'] * 52, g['kwh'], g['wort']
    return g['kwh'], g['kwh'] / 365, 'Tag'


def dauer(g):
    if 'min' in g:
        return '%d Minuten am Tag' % g['min']
    return ('%s Stunden am Tag' % z(g['h'], 0 if g['h'] == int(g['h']) else 1)) if g['h'] != 1 else 'einer Stunde am Tag'


def antwort(g, ct, kurz=False):
    j, e, name = rechne(g); p = ct / 100; Ein = g['ein'][0].upper() + g['ein'][1:]
    if g['art'] == 'w':
        mittel = ' im Mittel' if g.get('anteil', 100) < 100 else ''
        zeit = ('Bei Dauerbetrieb an %d Tagen im Jahr' % g['tage']) if g.get('h') == 24 else ('Bei %s an %d Tagen im Jahr' % (dauer(g), g['tage']))
        return '%s mit %s&nbsp;Watt kostet bei %d&nbsp;Cent pro kWh%s etwa <b>%s pro Stunde</b>. %s sind das rund <b>%s</b>.' % (Ein, z(g['w']), ct, mittel, geld(e * p), zeit, geld(j * p))
    if g['art'] == 'gang':
        return '%s braucht etwa %s&nbsp;kWh Strom. Das kostet bei %d&nbsp;Cent pro kWh rund <b>%s</b>. Bei %d Mal pro Woche sind das etwa <b>%s im Jahr</b>.' % (Ein, z(g['kwh'], 2 if g['kwh'] < 0.1 else 1 if g['kwh'] * 10 == int(g['kwh'] * 10) else 2), ct, geld(e * p), g['proWoche'], geld(j * p))
    return '%s braucht etwa %s&nbsp;kWh Strom im Jahr. Das kostet bei %d&nbsp;Cent pro kWh rund <b>%s im Jahr</b>, also etwa %s im Monat.' % (Ein, z(g['kwh']), ct, geld(j * p), geld(j * p / 12))


def feld(f, label, wert, hinweis='', aria=None, attr=''):
    return ('<label class="skc-f"%s><span>%s</span><input class="vin" data-f="%s" type="text" inputmode="decimal" autocomplete="off" value="%s"%s>%s</label>'
            % (attr, label, f, wert, ' aria-label="%s"' % aria if aria else '', '<small>%s</small>' % hinweis if hinweis else ''))


def kommazahl(v):
    return str(v).replace('.', ',')


def rechner(g, ct, hub=False):
    j, e, name = rechne(g); p = ct / 100
    preis = feld('ct', 'Strompreis (Cent pro kWh)', ct, 'Arbeitspreis aus deinem Vertrag', 'Strompreis in Cent pro Kilowattstunde')
    if hub:
        felder = (feld('w', 'Leistung (Watt)', g['w'], attr=' data-for="w"') + feld('h', 'Stunden pro Tag', kommazahl(g['h']), attr=' data-for="w"') + feld('tage', 'Tage im Jahr', g['tage'], attr=' data-for="w"')
                  + '<label class="skc-f" data-for="gang jahr" hidden><span id="sk-kwh-l">Verbrauch (kWh)</span><input class="vin" data-f="kwh" type="text" inputmode="decimal" autocomplete="off" value="1"></label>'
                  + feld('proWoche', 'Wie oft pro Woche', 4, attr=' data-for="gang" hidden'))
    elif g['art'] == 'w':
        felder = feld('w', 'Leistung (Watt)', g['w'], 'steht auf dem Typenschild') + (feld('min', 'Minuten pro Tag', g['min']) if 'min' in g else feld('h', 'Stunden pro Tag', kommazahl(g['h']))) + feld('tage', 'Tage im Jahr', g['tage'])
    elif g['art'] == 'gang':
        felder = feld('kwh', 'Verbrauch je %s (kWh)' % g['wort'], kommazahl(g['kwh']), 'steht in der Anleitung oder auf dem Energielabel') + feld('proWoche', 'Wie oft pro Woche', g['proWoche'])
    else:
        felder = feld('kwh', 'Verbrauch im Jahr (kWh)', g['kwh'], 'steht auf dem Energielabel')
    einheit = 'pro Stunde' if g['art'] == 'w' else 'pro ' + name
    return ('<div class="skc" data-art="%s" data-anteil="%d" data-emb><div class="skc-in">%s%s<p class="skc-err" role="alert" hidden>Bitte prüfe die Eingaben: Hier steht eine Zahl, mit der wir nicht rechnen können.</p></div>'
            '<div class="skc-out" aria-live="polite"><div class="skc-big"><b data-o="jahr">%s</b><span>Stromkosten im Jahr</span></div>'
            '<div class="skc-row"><div><b data-o="einheit">%s</b><span data-o="einheit-l">%s</span></div><div><b data-o="monat">%s</b><span>pro Monat</span></div><div><b data-o="kwh">%s kWh</b><span>Strom im Jahr</span></div></div>'
            '<div class="skc-bar" aria-hidden="true"><i></i></div><p class="skc-v" data-o="vergleich"></p></div></div>'
            % (g['art'], g.get('anteil', 100), felder, preis, geld(j * p).replace('&nbsp;', ' '), geld(e * p).replace('&nbsp;', ' '), einheit, geld(j * p / 12).replace('&nbsp;', ' '), z(j, 1 if j < 10 else 0)))


def url(g):
    return '/stromkosten/%s.html' % g['slug']


def seite(g, d, kopf, fuss, goat):
    import site_header
    ct = d['preis']; j, e, name = rechne(g); u = SITE + url(g); kats = dict(d['kategorien'])
    title = '%s – Strom-Daheim' % g['frage']
    ant = antwort(g, ct); desc = re.sub(r'<[^>]+>', '', ant).replace('&nbsp;', ' ')
    if len(desc) > 158:
        desc = desc[:desc.rfind('. ', 0, 158) + 1]
    head = kopf
    head = re.sub(r'<title>.*?</title>', lambda m: '<title>%s</title>' % html.escape(title), head, flags=re.S)
    head = re.sub(r'<meta property="og:title" content="[^"]*">', lambda m: '<meta property="og:title" content="%s">' % html.escape(title, quote=True), head)
    head = re.sub(r'<meta (name="description"|property="og:description") content="[^"]*">', lambda m: '<meta %s content="%s">' % (m.group(1), html.escape(desc, quote=True)), head)
    head = head.replace(SITE + '/stromkosten.html', u)
    head = re.sub(r'<script type="application/ld\+json" id="ld">.*?</script>\n?', '', head, flags=re.S)
    org = {'@type': 'Organization', 'name': 'Strom-Daheim', 'url': SITE + '/'}
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'Article', 'headline': g['frage'], 'name': title, 'description': desc, 'inLanguage': 'de-DE', 'url': u, 'mainEntityOfPage': u, 'datePublished': g.get('seit', STAND), 'dateModified': STAND,
         'image': SITE + '/assets/og/stromkosten.jpg', 'author': org, 'publisher': org},
        {'@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': g['frage'], 'acceptedAnswer': {'@type': 'Answer', 'text': desc}}]},
        {'@type': 'BreadcrumbList', 'itemListElement': [{'@type': 'ListItem', 'position': 1, 'name': 'Strom-Daheim', 'item': SITE + '/'},
                                                        {'@type': 'ListItem', 'position': 2, 'name': 'Stromkosten je Gerät', 'item': SITE + '/stromkosten.html'},
                                                        {'@type': 'ListItem', 'position': 3, 'name': g['name'], 'item': u}]}]}
    head += '\n<script type="application/ld+json" id="ld">%s</script>' % json.dumps(ld, ensure_ascii=False).replace('</', '<\\/')
    einheit = 'pro Stunde' if g['art'] == 'w' else 'pro ' + name
    tb = ''.join('<tr><th scope="row">%d ct</th><td>%s</td><td>%s</td><td>%s</td></tr>' % (c, geld(e * c / 100), geld(j * c / 1200), geld(j * c / 100)) for c in PREISE)
    tipps = ''.join('<li>%s</li>' % html.escape(t) for t in g['tipps'])
    gleich = [x for x in d['geraete'] if x['kat'] == g['kat'] and x['slug'] != g['slug']]
    aehnlich = ''.join('<a href="%s"><b>%s</b><span>etwa %s im Jahr</span></a>' % (url(x), html.escape(x['name']), geld(rechne(x)[0] * ct / 100)) for x in gleich[:6])
    rat = '<p>Mehr dazu im Ratgeber <a href="%s">%s</a>.</p>' % (g['ratgeber'][0], html.escape(g['ratgeber'][1])) if g.get('ratgeber') else ''
    annahme = ''
    if g['art'] == 'w':
        annahme = 'Rechenweg: Leistung in Kilowatt mal Stunden mal Strompreis.' + (' Weil das Gerät nicht durchgehend heizt, rechnen wir mit %d&nbsp;Prozent der Leistung.' % g['anteil'] if g.get('anteil', 100) < 100 else '')
    elif g['art'] == 'gang':
        annahme = 'Rechenweg: Verbrauch je %s mal Anzahl mal Strompreis, über 52 Wochen.' % name
    else:
        annahme = 'Rechenweg: Jahresverbrauch vom Energielabel mal Strompreis.'
    main = '''<main id="main">
<div class="lxh"><div class="wrap read">
<span class="eyebrow"><a href="/stromkosten.html">Stromkosten je Gerät</a> · %(kat)s</span>
<h1>%(frage)s</h1>
<p class="lede sk-a">%(ant)s</p>
<p class="sk-q">Richtwert für ein übliches Gerät, Stand %(stand)s. Mit deinen Zahlen rechnet der Rechner darunter.</p>
</div></div>
<section class="band" id="rechner"><div class="wrap">
<div class="head"><span class="eyebrow">Rechner</span><h2>Mit deinem Gerät und deinem Strompreis.</h2></div>
%(rechner)s
<p class="sk-q" style="margin-top:14px">%(annahme)s</p>
</div></section>
<section id="werte"><div class="wrap read">
<div class="head"><span class="eyebrow">Richtwerte</span><h2>Wie viel %(ein)s braucht.</h2></div>
<p><b>Üblich:</b> %(spanne)s.</p>
<p>%(wovon)s</p>
<div class="pa-tw" tabindex="0" role="region" aria-label="Tabelle, seitlich verschiebbar"><table class="sk-t"><caption>Kosten je nach Strompreis, mit den Richtwerten von oben</caption><thead><tr><th scope="col">Strompreis je kWh</th><th scope="col">%(einheit)s</th><th scope="col">pro Monat</th><th scope="col">pro Jahr</th></tr></thead><tbody>%(tb)s</tbody></table></div>
</div></section>
<section class="band" id="sparen"><div class="wrap read">
<div class="head"><span class="eyebrow">Sparen</span><h2>So wird es günstiger.</h2></div>
<ul class="eb-ul">%(tipps)s</ul>
%(rat)s
<p>Mit einem <a href="/stromtarif.html#dynamisch">dynamischen Tarif</a> oder eigener Solaranlage zählt auch der Zeitpunkt: Der <a href="/strompreis-heute.html#fenster">Geräte-Planer</a> zeigt die günstigste Startzeit für heute.</p>
</div></section>
<section id="mehr"><div class="wrap">
<div class="head"><span class="eyebrow">%(kat)s</span><h2>Zum Vergleich.</h2></div>
<div class="lx-grid">%(aehnlich)s</div>
<p style="margin-top:22px"><a href="/stromkosten.html">Alle Geräte und der freie Rechner</a></p>
</div></section>
</main>
''' % {'kat': kats[g['kat']], 'frage': html.escape(g['frage']), 'ant': ant, 'stand': '%s.%s.%s' % (STAND[8:], STAND[5:7], STAND[:4]), 'rechner': rechner(g, ct), 'annahme': annahme,
       'ein': html.escape(g['ein']), 'spanne': html.escape(g['spanne']), 'wovon': html.escape(g['wovon']), 'einheit': einheit, 'tb': tb, 'tipps': tipps, 'rat': rat, 'aehnlich': aehnlich}
    return head + '\n</head><body>\n' + site_header.block('stromkosten').replace(' aria-current="page"', '') + main + fuss + '\n' + goat + '</body></html>\n'


def block(d):
    ct = d['preis']; out = []
    for k, lab in d['kategorien']:
        gs = sorted([g for g in d['geraete'] if g['kat'] == k], key=lambda g: -rechne(g)[0])
        out.append('<h3 class="sk-k">%s</h3><div class="sk-list">%s</div>' % (lab, ''.join(
            '<a href="%s"><b>%s</b><span class="sk-b"><i style="width:%.1f%%"></i></span><em data-sk-jahr="%.3f">%s</em></a>' % (url(g), html.escape(g['name']), max(3, min(100, rechne(g)[0] / 500 * 100)), rechne(g)[0], geld(rechne(g)[0] * ct / 100)) for g in gs)))
    daten = {g['slug']: {k: g[k] for k in ('art', 'w', 'h', 'min', 'tage', 'anteil', 'kwh', 'proWoche', 'wort', 'spanne') if k in g} for g in d['geraete']}
    opts = ''.join('<optgroup label="%s">%s</optgroup>' % (lab, ''.join('<option value="%s"%s>%s</option>' % (g['slug'], ' selected' if g['slug'] == 'heizluefter' else '', html.escape(g['name'])) for g in d['geraete'] if g['kat'] == k)) for k, lab in d['kategorien'])
    start = next(g for g in d['geraete'] if g['slug'] == 'heizluefter')
    return ('<!--SK-->\n<section class="band" id="rechner"><div class="wrap">\n<div class="head"><span class="eyebrow">Rechner</span><h2>Was kostet dein Gerät?</h2><p class="lede">Gerät wählen oder eigene Werte eintragen.</p></div>\n'
            '<label class="sk-sel"><span>Gerät</span><select id="sk-sel">%s</select></label>\n%s\n<p class="sk-q" id="sk-note" style="margin-top:14px">Üblich: %s. <a href="%s">Mehr zu diesem Gerät</a></p>\n'
            '<script>window.SKG=%s</script>\n</div></section>\n'
            '<section id="geraete"><div class="wrap">\n<div class="head"><span class="eyebrow">%d Geräte</span><h2>Was kostet was im Jahr?</h2><p class="lede">Richtwerte bei üblicher Nutzung und deinem Strompreis aus dem Rechner. Tipp auf ein Gerät für Details.</p></div>\n%s\n</div></section>\n<!--/SK-->'
            % (opts, rechner(start, ct, hub=True), html.escape(start['spanne']), url(start), json.dumps(daten, ensure_ascii=False, separators=(',', ':')), len(d['geraete']), ''.join(out)))


def main():
    import fusszeile
    f0 = ROOT / 'stromkosten.html'
    if not f0.exists():
        print('stromkosten.html fehlt, nichts gebaut'); return
    d = json.loads((ROOT / 'werkzeuge/stromkosten.json').read_text(encoding='utf-8'))
    s = f0.read_text(encoding='utf-8')
    s2 = re.sub(r'<!--SK-->.*?<!--/SK-->', lambda m: block(d), s, flags=re.S)
    if s2 != s:
        f0.write_text(s2, encoding='utf-8'); s = s2
    kopf = s[:s.index('</head>')].rstrip('\n')
    fuss = '<footer><div class="wrap">\n<p>Alle Zahlen sind Richtwerte ohne Gewähr. Dein Gerät kann mehr oder weniger brauchen: Genau weiß es nur ein Strommessgerät an der Steckdose.</p>\n' + fusszeile.block('') + '\n</div></footer>'
    m = re.search(r'<script>\n/\* Besucherzähler.*?</script>\n', s, flags=re.S); goat = m.group(0) if m else ''
    out = ROOT / 'stromkosten'; out.mkdir(exist_ok=True); soll = set(); n = 0
    for g in d['geraete']:
        f = out / (g['slug'] + '.html'); soll.add(f.name); t = seite(g, d, kopf, fuss, goat)
        if not f.exists() or f.read_text(encoding='utf-8') != t:
            f.write_text(t, encoding='utf-8'); n += 1
    for f in out.glob('*.html'):
        if f.name not in soll:
            f.unlink()
    sm = ROOT / 'sitemap.xml'; x = sm.read_text(encoding='utf-8'); add = ''
    for g in d['geraete']:
        loc = SITE + url(g)
        if '<loc>%s</loc>' % loc not in x:
            add += '<url><loc>%s</loc><lastmod>%s</lastmod></url>' % (loc, STAND)
    if add:
        sm.write_text(x.replace('</urlset>', add + '</urlset>'), encoding='utf-8')
    print('Stromkosten: %d Geräte, %d Seiten neu geschrieben' % (len(d['geraete']), n))


if __name__ == '__main__':
    main()
