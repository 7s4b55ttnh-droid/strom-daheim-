"""Strompreis morgen: schreibt den Block zwischen <!--SM--> und <!--/SM--> in strompreis-morgen.html.
Wird von werkzeuge/strompreis.py bei jedem Lauf aufgerufen (GitHub-Ablauf „Strompreise holen“). Die Preise für morgen
veröffentlicht die Strombörse am frühen Nachmittag; bis dahin zeigt die Seite ehrlich die Preise von heute und sagt das dazu.
Fester Preisteil für den geschätzten Endpreis: 20 ct/kWh plus 19 % Mehrwertsteuer auf den Börsenpreis, wie auf strompreis-heute.html."""
import re, html, pathlib, datetime
import preisarchiv as pa
ROOT = pathlib.Path(__file__).resolve().parent.parent
WT = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
FIX = 20.0
GERAETE = [('Waschmaschine', 2), ('Spülmaschine', 3), ('Trockner', 3), ('E-Auto laden', 4)]


def fenster(w, n):
    """Günstigstes und teuerstes Fenster von n Stunden am Stück: (Startstunde, Mittel)."""
    alle = [(sum(w[h:h + n]) / n, h) for h in range(0, 25 - n) if all(x is not None for x in w[h:h + n])]
    return min(alle), max(alle)


def end(v):
    return FIX + v * 1.19


def block(tage, jetzt):
    heute = jetzt.date(); morgen = (heute + datetime.timedelta(days=1)).isoformat(); da = morgen in tage
    tag = morgen if da else heute.isoformat(); w = tage[tag]; d = datetime.date.fromisoformat(tag)
    werte = [x for x in w if x is not None]; mittel = sum(werte) / len(werte); z = pa.z
    name = '%s, %d. %s %d' % (WT[d.weekday()], d.day, pa.MON[d.month - 1], d.year)
    (gv, gh), (tv, th) = fenster(w, 3); neg = sum(1 for x in werte if x < 0)
    lo = min(werte); hi = max(werte); loh = w.index(lo); hih = w.index(hi)
    vergleich = ''
    if da and heute.isoformat() in tage:
        hw = [x for x in tage[heute.isoformat()] if x is not None]; hm = sum(hw) / len(hw)
        if hm > 0.5:
            diff = (mittel / hm - 1) * 100
            vergleich = ' Das ist %s als heute (%s ct).' % ('etwa so viel' if abs(diff) < 3 else '%s %% %s' % (z(abs(diff), 0), 'mehr' if diff > 0 else 'weniger'), z(hm))
    chart = pa.balken([x if x is not None else 0 for x in w], [str(h) if h % 3 == 0 else '' for h in range(24)],
                      ['%d bis %d Uhr: %s ct an der Börse, etwa %s ct Endpreis' % (h, h + 1, z(x or 0), z(end(x or 0))) for h, x in enumerate(w)],'h',
                      ['gut' if gh <= h < gh + 3 else 'teuer' if th <= h < th + 3 else '' for h in range(24)])
    ger = ''.join('<tr><th scope="row">%s <span>%d Std.</span></th><td>%d Uhr</td><td>%s ct</td><td>%s ct</td></tr>'
                  % (n, st, f[0][1], z(f[0][0]), z(f[1][0])) for n, st in GERAETE for f in [fenster(w, st)])
    tb = ''.join('<tr><th scope="row">%d bis %d Uhr</th><td>%s</td><td>%s</td></tr>' % (h, h + 1, z(x), z(end(x))) for h, x in enumerate(w) if x is not None)
    kopf = ('<p class="sm-day"><b>%s</b> · Preise %s</p>' % (name, 'für morgen' if da else 'von heute'))
    hinweis = '' if da else ('<p class="note sm-wait">Die Preise für morgen stehen noch nicht fest. Die Strombörse veröffentlicht sie am frühen Nachmittag, hier erscheinen sie meist zwischen 13 und 15 Uhr. '
                             'Bis dahin siehst du die Preise von heute.</p>')
    negsatz = (' In %d %s ist der Börsenpreis negativ.' % (neg, 'Stunde' if neg == 1 else 'Stunden')) if neg else ''
    return '''<!--SM-->
<div class="sm" id="sm" data-tag="%(tag)s" data-da="%(da)d">
%(hinweis)s%(kopf)s
<p class="lede sm-l">Strom kostet %(wann)s an der Börse im Schnitt <b>%(mittel)s&nbsp;ct pro kWh</b>.%(vergleich)s Am günstigsten ist es zwischen <b>%(gh)d und %(gh3)d Uhr</b>, am teuersten zwischen %(th)d und %(th3)d Uhr.%(negsatz)s</p>
<div class="pa-st">
<div><b>%(gh)d–%(gh3)d Uhr</b><span>günstigste 3 Stunden, im Schnitt %(gv)s ct</span></div>
<div><b>%(th)d–%(th3)d Uhr</b><span>teuerste 3 Stunden, im Schnitt %(tv)s ct</span></div>
<div><b>%(lo)s ct</b><span>niedrigste Stunde, %(loh)d bis %(loh1)d Uhr</span></div>
<div><b>%(hi)s ct</b><span>höchste Stunde, %(hih)d bis %(hih1)d Uhr</span></div>
</div>
<div class="pa-card sm-c"><h2 class="sm-h">Stunde für Stunde</h2>%(chart)s<p class="sr-leg sm-leg" aria-hidden="true"><span><i class="g"></i>günstigste 3 Stunden</span><span><i class="t"></i>teuerste 3 Stunden</span></p><p class="pa-q">Börsenpreis in Cent pro kWh, Uhrzeit in deutscher Ortszeit. Stand: %(stand)s Uhr.</p></div>
<div class="pa-card sm-c"><h2 class="sm-h">Wann einschalten?</h2>
<div class="pa-tw" tabindex="0" role="region" aria-label="Tabelle, seitlich verschiebbar"><table class="sm-g"><thead><tr><th scope="col">Gerät</th><th scope="col">beste Startzeit</th><th scope="col">Börse im Schnitt</th><th scope="col">zur teuersten Zeit</th></tr></thead><tbody>%(ger)s</tbody></table></div>
<p class="pa-q">Laufzeiten sind Richtwerte. Mit eigener Laufzeit und Frist rechnet der <a href="/strompreis-heute.html#fenster">Geräte-Planer</a>.</p></div>
<details class="pa-tbl sm-c"><summary>Alle 24 Stunden als Tabelle</summary><div class="pa-tw" tabindex="0" role="region" aria-label="Tabelle, seitlich verschiebbar"><table><thead><tr><th scope="col">Stunde</th><th scope="col">Börse (ct/kWh)</th><th scope="col">Endpreis etwa (ct/kWh)</th></tr></thead><tbody>%(tb)s</tbody></table></div></details>
</div>
<!--/SM-->''' % {'tag': tag, 'da': 1 if da else 0, 'hinweis': hinweis, 'kopf': kopf, 'wann': 'morgen' if da else 'heute', 'mittel': z(mittel), 'vergleich': vergleich,
                 'gh': gh, 'gh3': gh + 3, 'th': th, 'th3': th + 3, 'negsatz': negsatz, 'gv': z(gv), 'tv': z(tv), 'lo': z(lo), 'loh': loh, 'loh1': loh + 1, 'hi': z(hi), 'hih': hih, 'hih1': hih + 1,
                 'chart': chart, 'stand': jetzt.strftime('%d.%m.%Y, %H:%M'), 'ger': ger, 'tb': tb}


def seite(tage, jetzt, stand=None):
    f = ROOT / 'strompreis-morgen.html'
    if not f.exists():
        return False
    s = f.read_text(encoding='utf-8'); b = block(tage, stand or jetzt)
    alt = re.search(r'<!--SM-->.*?<!--/SM-->', s, flags=re.S)
    kern = lambda t: re.sub(r'Stand: [^<]* Uhr\.', '', t)
    if alt and kern(alt.group(0)) == kern(b):       # nur die Uhrzeit wäre neu: nichts speichern
        return False
    f.write_text(re.sub(r'<!--SM-->.*?<!--/SM-->', lambda m: b, s, flags=re.S), encoding='utf-8')
    sm = ROOT / 'sitemap.xml'; x = sm.read_text(encoding='utf-8')
    x2 = re.sub(r'(<loc>https://strom-daheim\.de/strompreis-morgen\.html</loc>\s*<lastmod>)[^<]*', lambda m: m.group(1) + jetzt.date().isoformat(), x)
    if x2 != x:
        sm.write_text(x2, encoding='utf-8')
    return True
