"""Strom-Daheim: Solar-Atlas. Baut den datengetriebenen Teil von solar-atlas.html (zwischen <!--ATLAS--> und <!--/ATLAS-->)
und die 95 Regionen-Seiten in solar/ aus werkzeuge/pvdaten/atlas.json (Kennzahlen, von atlas.js gerechnet) und
werkzeuge/pvdaten/atlas_karte.json (Flächen der Karte: jede Fläche gehört zum nächstgelegenen Rechenort; Umriss: Natural Earth, gemeinfrei).

Aufruf im Repository-Ordner:  python3 werkzeuge/solaratlas.py
Läuft auch automatisch am Ende von werkzeuge/fusszeile.py, damit Menü und Fußzeile der Regionen-Seiten zu den übrigen Seiten passen.
Die Regionen-Seiten nie von Hand ändern: Text und Aufbau stehen hier in der Datei. Neue Sonnendaten: erst node werkzeuge/pvdaten/atlas.js.
"""
import json, re, html, pathlib, sys, unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'werkzeuge'))
import site_header, fusszeile

SITE = 'https://strom-daheim.de'
A = json.loads((ROOT / 'werkzeuge/pvdaten/atlas.json').read_text(encoding='utf-8'))
K = json.loads((ROOT / 'werkzeuge/pvdaten/atlas_karte.json').read_text(encoding='utf-8'))
R = A['regionen']
STAND = '14.11.2026'      # Tag, an dem Text und Rechenweg zuletzt geprüft wurden
MON = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
MET = [('dach', 'Dach nach Süden', 'Süddach, 35° geneigt', 'kWh je kWp'), ('ow', 'Dach Ost/West', 'Ost-West-Dach, 15° geneigt', 'kWh je kWp'),
       ('bkw90', 'Balkon senkrecht', 'Balkonkraftwerk 900 Wp, senkrecht nach Süden', 'kWh im Jahr'), ('bkw30', 'Balkon aufgeständert', 'Balkonkraftwerk 900 Wp, 30° nach Süden', 'kWh im Jahr')]
PAL = ['#3d3420', '#6b5521', '#9a7a1f', '#c99a1c', '#ffb81c']      # eine Farbe, dunkel = wenig, hell = viel (die Bühne ist immer dunkel)


def z(n):
    return ('{:,}'.format(int(round(n)))).replace(',', '.')


def slug(plz):
    t = R[plz]['name'].lower().replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
    t = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode()
    return plz + '-' + re.sub(r'[^a-z0-9]+', '-', t).strip('-')


def url(plz):
    return '/solar/%s.html' % slug(plz)


def rang(key):
    order = sorted(R, key=lambda p: -R[p][key])
    return {p: i + 1 for i, p in enumerate(order)}


RANG = {m[0]: rang(m[0]) for m in MET}
MEAN = {m[0]: sum(r[m[0]] for r in R.values()) / len(R) for m in MET}


def farbe(key, v):
    lo, hi = min(r[key] for r in R.values()), max(r[key] for r in R.values())
    return PAL[min(4, int((v - lo) / (hi - lo + 1e-9) * 5))]


def karte():
    p = ''.join('<path d="%s" fill="%s" data-r="%s"/>' % (K['regionen'][k]['d'], farbe('dach', R[k]['dach']), k) for k in sorted(K['regionen']))
    return ('<svg class="ill" id="sa-map" viewBox="0 0 %d %d" role="img" aria-label="Karte von Deutschland: Solarertrag je Postleitregion. Die Werte stehen auch in der Tabelle.">'
            '<g stroke="#000" stroke-width="1.2" stroke-linejoin="round">%s</g><path id="sa-sel" d="" fill="none" stroke="#fff" stroke-width="3" stroke-linejoin="round" pointer-events="none"/></svg>' % (K['w'], K['h'], p))


def atlas_block():
    best = max(R, key=lambda p: R[p]['dach']); worst = min(R, key=lambda p: R[p]['dach'])
    diff = round((R[best]['dach'] / R[worst]['dach'] - 1) * 100)
    ow = round((1 - MEAN['ow'] / MEAN['dach']) * 100)
    fass = round((1 - sum(r['fass'] for r in R.values()) / len(R) / MEAN['dach']) * 100)
    order = sorted(R, key=lambda p: -R[p]['dach'])
    def zeile(p):
        r = R[p]
        return ('<tr data-r="%s"><td>%d</td><td><a href="%s">%s</a></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
                % (p, RANG['dach'][p], url(p), html.escape(r['name']), p, z(r['dach']), z(r['ow']), z(r['bkw90']), z(r['bkw30'])))
    kopf = '<thead><tr><th scope="col">Platz</th><th scope="col">Region</th><th scope="col">PLZ</th><th scope="col">Dach Süd</th><th scope="col">Dach Ost/West</th><th scope="col">Balkon senkrecht</th><th scope="col">Balkon 30°</th></tr></thead>'
    daten = {p: {'n': R[p]['name'], 'u': url(p), 'v': [R[p][m[0]] for m in MET], 'r': [RANG[m[0]][p] for m in MET]} for p in sorted(R)}
    meta = {'met': [[m[1], m[2], m[3]] for m in MET], 'mean': [round(MEAN[m[0]]) for m in MET], 'pal': PAL}
    chips = ''.join('<button type="button" data-m="%d" aria-pressed="%s">%s</button>' % (i, 'true' if i == 0 else 'false', m[1]) for i, m in enumerate(MET))
    leg = ''.join('<i style="background:%s"></i>' % c for c in PAL)
    return '''<!--ATLAS-->
<div class="hero sah">
  <div class="wrap sa-top sa-3">
    <div class="sa-txt sa-head">
      <span class="eyebrow">Solar-Atlas · Sonnendaten 2005 bis 2023</span>
      <h1>Wie viel Sonnenstrom gibt es bei dir?</h1>
      <p>95 Regionen, vier Arten zu bauen. Gib deine Postleitzahl ein oder tipp auf die Karte.</p>
    </div>
    <div class="sa-mapbox">%(karte)s
      <div class="sa-tip" id="sa-tip" hidden></div>
      <div class="sa-leg" aria-hidden="true"><span id="sa-lo">%(wv)s</span>%(leg)s<span id="sa-hi">%(bv)s</span><em id="sa-unit">kWh je kWp</em></div>
    </div>
    <div class="sa-ctl">
      <form class="sa-form" id="sa-form" action="/balkonkraftwerk-planer.html" method="get"><label for="sa-plz">Deine Postleitzahl</label><div><input id="sa-plz" name="p" type="text" inputmode="numeric" autocomplete="postal-code" maxlength="5" placeholder="97070" aria-describedby="sa-hint"><button type="submit" class="sa-go">Im Planer rechnen</button></div></form>
      <div class="chips sa-chips" id="sa-met" role="group" aria-label="Was soll die Karte zeigen?">%(chips)s</div>
      <div class="sa-card" id="sa-card" aria-live="polite"><p class="sa-hint" id="sa-hint">Im Schnitt aller Regionen liefert ein Süddach %(mean)s&nbsp;kWh je kWp im Jahr. Am meisten sind es in %(bn)s mit %(bv)s, am wenigsten in %(wn)s mit %(wv)s.</p></div>
    </div>
  </div>
</div>
<script type="application/json" id="sa-data">%(json)s</script>

<section class="band" id="rangliste"><div class="wrap">
<div class="head"><span class="eyebrow">Rangliste</span><h2>Alle 95 Regionen.</h2><p class="lede">Sortiert nach dem Ertrag eines Süddachs. Dach-Werte in kWh je kWp und Jahr, Balkonkraftwerk mit 900&nbsp;Wp in kWh im Jahr.</p></div>
<div class="sa-tw"><table class="sa-t" id="sa-tab">%(kopf)s<tbody>%(top)s</tbody></table></div>
<details class="sa-all"><summary>Alle Regionen zeigen</summary><div class="sa-tw"><table class="sa-t">%(kopf)s<tbody>%(rest)s</tbody></table></div></details>
<p class="hint" style="margin-top:14px">Eine Region sind alle Postleitzahlen mit denselben ersten zwei Ziffern. Gerechnet wird für ihren größten Ort.</p>
</div></section>

<section id="lesen"><div class="wrap">
<div class="head"><span class="eyebrow">Einordnen</span><h2>Was die Zahlen sagen.</h2></div>
<div class="grid3">
  <div class="card opt"><b class="t">kWh je kWp</b><p>So viel Strom liefert ein Kilowatt Modulleistung in einem Jahr. Eine Dachanlage mit 10&nbsp;kWp bringt also das Zehnfache. Der Wert macht Standorte vergleichbar.</p></div>
  <div class="card opt"><b class="t">Süden liegt vorn, aber knapp</b><p>Zwischen der stärksten und der schwächsten Region liegen %(diff)s&nbsp;%%. Die Sonne reicht überall in Deutschland für eine Solaranlage.</p></div>
  <div class="card opt"><b class="t">Die Ausrichtung zählt ähnlich viel</b><p>Ein flaches Ost-West-Dach bringt im Schnitt %(ow)s&nbsp;%% weniger als ein Süddach, eine senkrechte Südfassade %(fass)s&nbsp;%% weniger. Dafür verteilt sich der Strom anders über Tag und Jahr.</p></div>
</div>
</div></section>

<section class="band" id="fragen"><div class="wrap read">
<span class="eyebrow">Häufige Fragen</span><h2>Kurz beantwortet.</h2>
<details><summary>Woher kommen die Zahlen?</summary><p>Aus den Sonnendaten von PVGIS, dem Photovoltaik-Rechner der Europäischen Kommission. Für jede Region liegt ein typisches Jahr mit Werten für jede Stunde vor, gemittelt aus den Jahren 2005 bis 2023. Daraus rechnen wir den Ertrag mit demselben Rechenkern wie im Balkonkraftwerk-Planer.</p></details>
<details><summary>Wie genau sind die Werte?</summary><p>Wir haben den Rechenkern in 112 Fällen mit den Ergebnissen von PVGIS verglichen: Im Mittel weicht er 0,8&nbsp;%% ab, im ungünstigsten Fall 6,2&nbsp;%%. Dein Dach kann trotzdem abweichen, vor allem durch Schatten, eine andere Neigung oder die Lage im Gebirge. Auch einzelne Jahre schwanken.</p></details>
<details><summary>Warum Postleitregionen und nicht meine genaue Adresse?</summary><p>Weil die Seite ohne fremde Server auskommt. Die Daten für 95 Regionen liegen fertig bei uns. Innerhalb einer Region sind die Unterschiede meist klein gegenüber dem Einfluss von Ausrichtung und Schatten.</p></details>
<details><summary>Welche Verluste sind eingerechnet?</summary><p>Bei den Dach-Werten 10&nbsp;%% für Kabel, Wechselrichter und Verschmutzung, so wie PVGIS sie ansetzt. Beim Balkonkraftwerk rechnen wir wie im Planer, mit einem Wechselrichter, der höchstens 800&nbsp;Watt abgibt.</p></details>
<details><summary>Was bringt die Anlage bei mir in Euro?</summary><p>Das hängt davon ab, wie viel Strom du selbst verbrauchst. Der <a href="/balkonkraftwerk-planer.html">Balkonkraftwerk-Planer</a> rechnet es mit deinem Verbrauch und deinem Strompreis aus, für Dachanlagen der <a href="/pv-anlage.html">Ratgeber zur Solaranlage</a>.</p></details>
</div></section>

<section id="quellen"><div class="wrap read">
<span class="eyebrow">Quellen</span><h2>Woher die Zahlen kommen.</h2>
<div class="src"><ol>
<li>PVGIS 5.3, Europäische Kommission, Gemeinsame Forschungsstelle: Datenbank PVGIS-SARAH3, typisches Jahr aus 2005 bis 2023. PVGIS © Europäische Union <a href="https://re.jrc.ec.europa.eu/pvg_tools/de/" target="_blank" rel="noopener">re.jrc.ec.europa.eu</a></li>
<li>Karte: eigene Darstellung. Jede Fläche zeigt den Wert des nächstgelegenen Rechenorts. Umriss nach Natural Earth (gemeinfrei).</li>
</ol><p style="margin-top:12px">Geprüft am %(stand)s.</p></div>
</div></section>

<section><div class="wrap read">
<div class="cta"><a class="btn" href="/balkonkraftwerk-planer.html">Balkonkraftwerk für meinen Balkon rechnen</a><a class="btn sec" href="/pv-anlage.html">Lohnt sich eine Anlage aufs Dach?</a></div>
</div></section>
<!--/ATLAS-->''' % dict(chips=chips, karte=karte(), leg=leg, mean=z(MEAN['dach']), bn=html.escape(R[best]['name']), bv=z(R[best]['dach']), wn=html.escape(R[worst]['name']), wv=z(R[worst]['dach']),
                    json=json.dumps({'reg': daten, 'meta': meta}, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/'), kopf=kopf, top=''.join(zeile(p) for p in order[:10]),
                    rest=''.join(zeile(p) for p in order[10:]), diff=diff, ow=ow, fass=fass, stand=STAND)


def monate(r):
    """Monatsbalken als festes SVG (kein Skript nötig), einmal für breite und einmal für schmale Bildschirme."""
    def bild(W, H, L, kurz):
        B, T = 26, 22
        mx = max(r['mon']); step = 50 if mx > 120 else 25; top = (int(mx / step) + 1) * step
        bw = (W - L - 4) / 12; pad = 5 if not kurz else 2.5
        s = '<svg class="%s" viewBox="0 0 %d %d" role="img" aria-label="Ertrag je Monat für 1 kWp auf einem Süddach: %s">' % ('k' if kurz else 'l', W, H, ', '.join('%s %s kWh' % (MON[i], z(v)) for i, v in enumerate(r['mon'])))
        g = 0
        while g <= top:
            y = T + (H - T - B) * (1 - g / top)
            s += '<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" class="g"/><text x="%d" y="%.1f" text-anchor="end">%d</text>' % (L, W - 4, y, y, L - 5, y + 4, g); g += step
        for i, v in enumerate(r['mon']):
            h = (H - T - B) * v / top; x = L + i * bw + pad; y = H - B - h; w = bw - 2 * pad; q = min(4, w / 2)
            s += '<path d="M%.1f %dV%.1fq0 -%.1f %.1f -%.1fh%.1fq%.1f 0 %.1f %.1fV%dz" class="b"/><text x="%.1f" y="%.1f" text-anchor="middle" class="v">%s</text><text x="%.1f" y="%d" text-anchor="middle">%s</text>' % (
                x, H - B, y + q, q, q, q, w - 2 * q, q, q, q, H - B, x + w / 2, y - 5, z(v), x + w / 2, H - 8, MON[i][0] if kurz else MON[i])
        return s + '</svg>'
    return bild(640, 250, 34, False) + bild(340, 230, 28, True)


def minikarte(plz):
    k = K['regionen'][plz]
    return ('<svg class="sa-mini" viewBox="0 0 %d %d" aria-hidden="true"><path d="%s" class="u"/><path d="%s" class="r"/><circle cx="%s" cy="%s" r="7" class="p"/></svg>' % (K['w'], K['h'], K['umriss'], k['d'], k['x'], k['y']))


def nachbarn(plz, n=6):
    import math
    a = R[plz]
    d = lambda p: math.hypot((R[p]['lon'] - a['lon']) * math.cos(math.radians(51)), R[p]['lat'] - a['lat'])
    return sorted((p for p in R if p != plz), key=d)[:n]


def region(plz, kopf_html, fuss_html, goat):
    r = R[plz]; name = html.escape(r['name']); u = SITE + url(plz)
    title = 'Solarertrag %s (PLZ %s) – Strom-Daheim' % (r['name'], plz)
    desc = ('In der Region %s (PLZ %s) liefert ein Süddach rund %s kWh je kWp im Jahr, ein Balkonkraftwerk mit 900 Wp senkrecht rund %s kWh. Mit Monatswerten und Tabelle nach Ausrichtung.'
            % (r['name'], plz, z(r['dach']), z(r['bkw90'])))
    if len(desc) > 160:
        desc = 'Region %s (PLZ %s): Ein Süddach liefert rund %s kWh je kWp im Jahr, ein Balkonkraftwerk mit 900 Wp senkrecht rund %s kWh.' % (r['name'], plz, z(r['dach']), z(r['bkw90']))
    head = kopf_html
    head = re.sub(r'<title>.*?</title>', lambda m: '<title>%s</title>' % html.escape(title), head, flags=re.S)
    head = re.sub(r'<meta property="og:title" content="[^"]*">', lambda m: '<meta property="og:title" content="%s">' % html.escape(title, quote=True), head)
    head = re.sub(r'<meta (name="description"|property="og:description") content="[^"]*">', lambda m: '<meta %s content="%s">' % (m.group(1), html.escape(desc, quote=True)), head)
    head = head.replace(SITE + '/solar-atlas.html', u)
    head = re.sub(r'<script type="application/ld\+json" id="ld">.*?</script>\n?', '', head, flags=re.S)
    head = re.sub(r'<script src="/solar-atlas\.js" defer></script>', '', head)
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'Article', 'headline': 'Solarertrag in der Region %s' % r['name'], 'name': title, 'description': desc, 'inLanguage': 'de-DE', 'url': u, 'mainEntityOfPage': u,
         'datePublished': '2026-11-14', 'dateModified': A['stand'], 'image': SITE + '/assets/og/solar-atlas.jpg',
         'author': {'@type': 'Organization', 'name': 'Strom-Daheim', 'url': SITE + '/'}, 'publisher': {'@type': 'Organization', 'name': 'Strom-Daheim', 'url': SITE + '/'}},
        {'@type': 'BreadcrumbList', 'itemListElement': [{'@type': 'ListItem', 'position': 1, 'name': 'Strom-Daheim', 'item': SITE + '/'},
                                                        {'@type': 'ListItem', 'position': 2, 'name': 'Solar-Atlas', 'item': SITE + '/solar-atlas.html'},
                                                        {'@type': 'ListItem', 'position': 3, 'name': r['name'], 'item': u}]}]}
    head = head.replace('</head>', '<script type="application/ld+json" id="ld">%s</script>\n</head>' % json.dumps(ld, ensure_ascii=False).replace('</', '<\\/'), 1)
    dm = (r['dach'] / MEAN['dach'] - 1) * 100
    vergleich = 'so viel wie im Schnitt aller Regionen' if abs(dm) < 0.5 else '%s&nbsp;%% %s als im Schnitt aller Regionen' % (z(abs(dm)) if abs(dm) >= 1 else '1', 'mehr' if dm > 0 else 'weniger')
    tab = ''.join('<tr><th scope="row">%d° geneigt</th>%s</tr>' % (A['neigung'][i], ''.join('<td%s>%s</td>' % (' class="mx"' if v == max(max(x) for x in r['tab']) else '', z(v)) for v in row)) for i, row in enumerate(r['tab']))
    sommer = sum(r['mon'][3:9]) / sum(r['mon']) * 100
    nb = ''.join('<a href="%s"><b>%s</b><span>PLZ %s · %s kWh je kWp</span></a>' % (url(p), html.escape(R[p]['name']), p, z(R[p]['dach'])) for p in nachbarn(plz))
    main = '''<main id="main">
<div class="hero sah sa-reg">
  <div class="wrap sa-top">
    <div class="sa-txt">
      <span class="eyebrow"><a href="/solar-atlas.html">Solar-Atlas</a> · Postleitzahlen %(plz)s…</span>
      <h1>Solarertrag in der Region %(name)s</h1>
      <p>Ein Süddach liefert hier rund <b>%(dach)s&nbsp;kWh je kWp</b> im Jahr. Das ist %(vergleich)s, Platz %(rang)d von 95.</p>
      <div class="jump"><a class="pri" href="#zahlen">Alle Zahlen</a><a href="#monate">Monat für Monat</a><a href="/solar-atlas.html">Zur Karte</a></div>
    </div>
    <div class="sa-mapbox">%(mini)s</div>
  </div>
</div>

<section id="zahlen"><div class="wrap">
<div class="head"><span class="eyebrow">Kennzahlen</span><h2>Vier Arten zu bauen.</h2><p class="lede">Gerechnet für %(name)s mit den Sonnendaten der Jahre 2005 bis 2023.</p></div>
<div class="res sa-res">
  <div class="hi"><b>%(dach)s kWh</b><span>je kWp und Jahr auf einem Süddach mit 35° Neigung</span></div>
  <div><b>%(ow)s kWh</b><span>je kWp und Jahr auf einem Ost-West-Dach mit 15° Neigung</span></div>
  <div><b>%(b90)s kWh</b><span>im Jahr: Balkonkraftwerk mit 900&nbsp;Wp, senkrecht am Südbalkon</span></div>
  <div><b>%(b30)s kWh</b><span>im Jahr: Balkonkraftwerk mit 900&nbsp;Wp, 30° aufgeständert nach Süden</span></div>
</div>
<p class="hint" style="margin-top:14px">Eine Dachanlage mit 10&nbsp;kWp nach Süden liefert hier rechnerisch rund %(zehn)s&nbsp;kWh im Jahr. Schatten, Schnee und einzelne Jahre können das Ergebnis verschieben.</p>
<form class="sa-form sa-inl" action="/balkonkraftwerk-planer.html" method="get"><label for="sa-plz">Was das in Euro bringt, rechnet der Planer mit deinem Verbrauch:</label><div><input id="sa-plz" name="p" type="text" inputmode="numeric" autocomplete="postal-code" maxlength="5" pattern="[0-9]{5}" required placeholder="%(plz)s…" aria-label="Deine Postleitzahl"><button type="submit" class="sa-go">Im Planer rechnen</button></div></form>
</div></section>

<section class="band" id="monate"><div class="wrap">
<div class="head"><span class="eyebrow">Jahresverlauf</span><h2>Monat für Monat.</h2><p class="lede">Ertrag in kWh für 1&nbsp;kWp auf einem Süddach mit 35° Neigung. Von April bis September kommen %(sommer)s&nbsp;%% des Jahresertrags.</p></div>
<div class="sa-chart">%(monate)s</div>
</div></section>

<section id="ausrichtung"><div class="wrap">
<div class="head"><span class="eyebrow">Ausrichtung</span><h2>Was dein Dach daraus macht.</h2><p class="lede">kWh je kWp und Jahr, je nach Himmelsrichtung und Neigung. Der höchste Wert ist markiert.</p></div>
<div class="sa-tw"><table class="sa-t sa-o"><thead><tr><th scope="col">Neigung</th><th scope="col">Ost</th><th scope="col">Südost</th><th scope="col">Süd</th><th scope="col">Südwest</th><th scope="col">West</th></tr></thead><tbody>%(tab)s</tbody></table></div>
<p class="hint" style="margin-top:14px">Eine senkrechte Südfassade kommt hier auf %(fass)s&nbsp;kWh je kWp. Ob deine Stadt oder dein Bundesland Solaranlagen fördert, erfährst du bei deiner Kommune.</p>
</div></section>

<section class="band" id="nachbarn"><div class="wrap">
<div class="head"><span class="eyebrow">In der Nähe</span><h2>Regionen nebenan.</h2></div>
<div class="sa-nb">%(nb)s</div>
</div></section>

<section id="quellen"><div class="wrap read">
<span class="eyebrow">Quellen</span><h2>Woher die Zahlen kommen.</h2>
<div class="src"><ol>
<li>PVGIS 5.3, Europäische Kommission, Gemeinsame Forschungsstelle: Datenbank PVGIS-SARAH3, typisches Jahr aus 2005 bis 2023, Rechenort %(name)s. PVGIS © Europäische Union <a href="https://re.jrc.ec.europa.eu/pvg_tools/de/" target="_blank" rel="noopener">re.jrc.ec.europa.eu</a></li>
<li>Rechenweg und Genauigkeit stehen im <a href="/solar-atlas.html#fragen">Solar-Atlas</a>: Dach-Werte mit 10&nbsp;%% Verlusten, Balkonkraftwerk mit 800-Watt-Wechselrichter.</li>
</ol><p style="margin-top:12px">Geprüft am %(stand)s.</p></div>
</div></section>

<section><div class="wrap read">
<div class="cta"><a class="btn" href="/balkonkraftwerk-planer.html">Balkonkraftwerk für meinen Balkon rechnen</a><a class="btn sec" href="/solar-atlas.html">Alle Regionen vergleichen</a></div>
</div></section>
</main>
''' % dict(plz=plz, name=name, dach=z(r['dach']), ow=z(r['ow']), b90=z(r['bkw90']), b30=z(r['bkw30']), vergleich=vergleich, rang=RANG['dach'][plz], mini=minikarte(plz),
           zehn=z(round(r['dach'] * 10, -2)), sommer=z(sommer), monate=monate(r), tab=tab, fass=z(r['fass']), nb=nb, stand=STAND)
    return head + '\n</head><body>\n' + site_header.block('solar-atlas').replace(' aria-current="page"', '') + main + fuss_html + '\n' + goat + '</body></html>\n'


def main():
    seite = ROOT / 'solar-atlas.html'
    if not seite.exists():
        print('solar-atlas.html fehlt, nichts gebaut'); return
    s = seite.read_text(encoding='utf-8')
    kg = re.search(r'<section class="kurz-s">.*?</section>\n', s, flags=re.S)      # Kasten „Kurz gesagt“ von seo.py bleibt erhalten
    def neu(m):
        blk = atlas_block()
        if kg:
            i = blk.index('<section')
            blk = blk[:i] + kg.group(0) + blk[i:]
        return blk
    s2 = re.sub(r'<!--ATLAS-->.*?<!--/ATLAS-->', neu, s, flags=re.S)
    if s2 != s:
        seite.write_text(s2, encoding='utf-8'); s = s2
    kopf = s[:s.index('</head>')].rstrip('\n')
    fuss = '<footer><div class="wrap">\n<p>Alle Zahlen sind Richtwerte ohne Gewähr. Mit „Anzeige“ markierte Links sind Partnerlinks (Amazon-Partnerprogramm); bei einem Kauf erhalten wir eine Provision, für dich ändert sich der Preis nicht. Als Amazon-Partner verdienen wir an qualifizierten Verkäufen.</p>\n' + fusszeile.block('') + '\n</div></footer>'
    m = re.search(r'<script>\n/\* Besucherzähler.*?</script>\n', s, flags=re.S)
    goat = m.group(0) if m else ''
    out = ROOT / 'solar'; out.mkdir(exist_ok=True)
    soll = set(); n = 0
    for plz in sorted(R):
        f = out / (slug(plz) + '.html'); soll.add(f.name)
        t = region(plz, kopf, fuss, goat)
        if not f.exists() or f.read_text(encoding='utf-8') != t:
            f.write_text(t, encoding='utf-8'); n += 1
    for f in out.glob('*.html'):
        if f.name not in soll:
            f.unlink()
    sm = ROOT / 'sitemap.xml'; x = sm.read_text(encoding='utf-8'); neu = ''
    for plz in sorted(R):
        loc = SITE + url(plz)
        if '<loc>%s</loc>' % loc not in x:
            neu += '<url><loc>%s</loc><lastmod>%s</lastmod></url>' % (loc, A['stand'])
    if neu:
        sm.write_text(x.replace('</urlset>', neu + '</urlset>'), encoding='utf-8')
    print('Solar-Atlas: %d Regionen-Seiten neu geschrieben, %d vorhanden' % (n, len(soll)))


if __name__ == '__main__':
    main()
