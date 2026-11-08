"""Strom-Daheim: strukturierte Daten (JSON-LD), Kasten „Kurz gesagt“ und llms.txt.
Aufruf im Repository-Ordner: python3 werkzeuge/seo.py
Neue Seite: Eintrag in KURZ ergänzen (zwei Sätze, nur Fakten, die auf der Seite stehen) und das Skript erneut ausführen."""
import re, json, html, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = 'https://strom-daheim.de'
NAME = 'Strom-Daheim'
KURZ = {
    'anleitung-balkonkraftwerk.html': 'Ein Balkonkraftwerk mit höchstens 960&nbsp;Watt Modulleistung und 800&nbsp;Watt Wechselrichter darf in die normale Haushaltssteckdose, die Montage schaffst du an einem Nachmittag. Danach meldest du es innerhalb eines Monats im Marktstammdatenregister an; zur Miete brauchst du für Brüstung oder Fassade die Zustimmung des Vermieters, die er nicht grundlos verweigern darf.',
    'e-auto.html': 'Zuhause laden kostet etwa 5 bis 8&nbsp;€ pro 100&nbsp;km, an öffentlichen Säulen zahlst du meist deutlich mehr (39 bis 89&nbsp;ct pro kWh). Für regelmäßiges Laden ist eine Wallbox mit 11&nbsp;kW sicherer und schneller als die Haushaltssteckdose.',
    'anleitung-wallbox.html': 'Eine Wallbox kostet mit Einbau im Standardfall etwa 800 bis 2.200&nbsp;€, anschließen darf sie nur ein eingetragener Elektrofachbetrieb. Sie wird beim Netzbetreiber angemeldet, und als steuerbare Verbrauchseinrichtung nach §&nbsp;14a sparst du etwa 110 bis 190&nbsp;€ Netzentgelt im Jahr.',
    'powerstation.html': 'Für Router, Handys und Licht reicht eine kleine Powerstation mit etwa 250&nbsp;Wh, für Kühlschrank und Licht über einen Tag braucht es rund 1.000&nbsp;Wh. Eine Powerstation versorgt nur Geräte, die direkt in ihr stecken, und darf nie über ein Kabel ins Hausnetz einspeisen.',
    'stromtarif.html': 'In der Grundversorgung zahlst du im Schnitt 40,39&nbsp;ct pro kWh, günstige Tarife liegen bei 31,93&nbsp;ct: Bei 2.500&nbsp;kWh sind das rund 210&nbsp;€ im Jahr. Der Wechsel ist kostenlos, technisch in 24 Stunden erledigt, und der Strom fließt ohne Unterbrechung weiter.',
    'stromfresser.html': 'Zwei Personen in einer Wohnung brauchen laut Stromspiegel 2025 im Schnitt 1.900&nbsp;kWh im Jahr; der Vergleich auf dieser Seite zeigt deine Klasse von A bis G. Die größten Stromfresser findest du mit einem Strommessgerät zwischen Steckdose und Gerät, Standby summiert sich dabei oft mehr als gedacht.',
    'waermepumpe.html': 'Im Altbau erreichen Luft-Wasser-Wärmepumpen laut Fraunhofer ISE im Mittel eine Jahresarbeitszahl von 3,4. Ob dein Haus passt, zeigt der 55-Grad-Test. Die KfW fördert seit 21. Juli 2026 mit 30&nbsp;% plus Boni, höchstens 70 bis 80&nbsp;% von 28.000&nbsp;€ Kosten.',
    'pv-anlage.html': 'Eine Photovoltaik-Anlage mit 10&nbsp;kWp kostet 2026 rund 12.000&nbsp;€, mit 10-kWh-Speicher rund 17.000&nbsp;€, und erzeugt etwa 9.000 bis 11.000&nbsp;kWh im Jahr. Lohnend ist vor allem der selbst genutzte Strom, denn die feste Einspeisevergütung für neue kleine Anlagen soll ab 2027 wegfallen; beschlossen ist das noch nicht.',
    'energielabel.html': 'Seit März 2021 gilt für viele Geräte wieder die Skala A bis G, und die beste Klasse A ist bewusst fast leer. Wichtiger als der Buchstabe ist die kWh-Zahl: Ein Kühlschrank von 2002 braucht bis zu 330&nbsp;kWh im Jahr, das beste neue Gerät 90 bis 125&nbsp;kWh.',
    'black-friday.html': 'Black Friday ist am 27. November 2026, Cyber Monday am 30. November. Ein Rabatt soll sich grundsätzlich auf den niedrigsten Preis der letzten 30 Tage beziehen, die UVP sagt wenig. Prüfe den Preisverlauf, lass dich von Countdowns nicht drängen und rechne vorher aus, ob sich ein Gerät wie Powerstation oder Balkonkraftwerk für dich lohnt.',
    'kuehlschrank.html': 'Ein Kühlschrank braucht nur 7&nbsp;°C, ein Gefrierschrank −18&nbsp;°C. Jedes Grad kälter kostet etwa 6&nbsp;Prozent mehr Strom, und schon 5&nbsp;mm Eis bedeuten rund 30&nbsp;Prozent mehr Energie, deshalb ab 1&nbsp;cm Eis abtauen. Ob die Türdichtung schließt, zeigt ein eingeklemmtes Blatt Papier.',
    'waesche-trocknen.html': 'Ein Wärmepumpentrockner braucht laut Umweltbundesamt etwa 0,7 bis 1&nbsp;kWh pro Trocknung, ein alter Trockner ohne Wärmepumpe rund 3,4&nbsp;kWh. Der Wäscheständer kostet keinen Strom, eine Ladung mit 5&nbsp;kg gibt aber bis zu 2&nbsp;Liter Wasser an die Raumluft ab: mehrmals täglich 5 bis 10 Minuten stoßlüften und die Luftfeuchte bei 40 bis 60&nbsp;Prozent halten.',
    'kochen.html': 'Beim Kochen spart der Deckel am meisten, je nach Quelle 10&nbsp;Prozent bis zwei Drittel. Wasser bis etwa einen Liter erhitzt der Wasserkocher mit rund einem Drittel weniger Energie als der Herd, ein Schnellkochtopf halbiert den Verbrauch etwa. Induktion braucht laut Stiftung Warentest 290 bis 340&nbsp;kWh im Jahr, Glaskeramik 360 bis 430&nbsp;kWh.',
    'weihnachtsbeleuchtung.html': 'Eine LED-Lichterkette mit 5&nbsp;W kostet laut Verbraucherzentrale NRW für vier Wochen mit acht Stunden am Tag etwa 40&nbsp;Cent, eine alte Glühlampen-Kette mit 50&nbsp;W rund 4&nbsp;€. Strom aus Batterien ist etwa 300-mal so teuer wie aus der Steckdose. Für draußen brauchst du Ketten mit mindestens Schutzart IP44 und ein Prüfzeichen wie VDE, GS oder TÜV.',
    'lueften.html': 'Im Winter reichen drei bis zehn Minuten Stoßlüften, drei- bis viermal am Tag, und kein Raum sollte unter 16&nbsp;°C fallen. Liegt die Luftfeuchte länger über 50&nbsp;Prozent, solltest du lüften. Schimmel wächst, wenn an einer Wand längere Zeit 80&nbsp;Prozent Feuchte herrschen; kleine Flächen bis etwa einen halben Quadratmeter entfernst du mit Ethanol 70 bis 80&nbsp;Prozent.',
    'heizluefter.html': 'Heizlüfter, Ölradiator und Infrarotheizung machen aus einer Kilowattstunde Strom eine Kilowattstunde Wärme, keines davon ist sparsamer als das andere. Ein Heizlüfter mit 2.000&nbsp;W kostet bei 32&nbsp;ct pro kWh rund 64&nbsp;ct pro Stunde, Strom ist je kWh gut zweieinhalb- bis dreimal so teuer wie Gas. Heizlüfter gehören direkt in die Wandsteckdose, nicht an eine Mehrfachsteckdose.',
    'klimageraet.html': 'Ein mobiles Klimagerät (Monoblock) kostet etwa 250 bis 1.000&nbsp;€, ist laut Stiftung Warentest aber bis zu siebenmal weniger effizient als ein fest eingebautes Split-Gerät. Das Split-Gerät kostet 800 bis 2.500&nbsp;€ plus Einbau durch einen Kältetechnik-Fachbetrieb und braucht im Jahr Strom für etwa 52 bis 120&nbsp;€, ein Monoblock für 100 bis 150&nbsp;€. In der Mietwohnung brauchst du für ein Split-Gerät die Erlaubnis des Vermieters.',
    'smart-meter.html': 'Einen Smart Meter musst du ab 6.000&nbsp;kWh Jahresverbrauch, mit einem steuerbaren Gerät nach §&nbsp;14a oder mit einer Solaranlage über 7&nbsp;kW bekommen, im Haushalt kostet er dann höchstens 40 bis 50&nbsp;€ im Jahr. Alle anderen bekommen bis 2032 einen digitalen Zähler für höchstens 25&nbsp;€ im Jahr und können einen Smart Meter freiwillig für 100&nbsp;€ einmalig und 30&nbsp;€ im Jahr bestellen.',
    'solar-laden.html': 'Mit PV-Überschussladen lädst du dein E-Auto mit Solarstrom, der 6 bis 14&nbsp;ct pro kWh kostet statt rund 37&nbsp;ct aus dem Netz. Dafür braucht es eine Dachanlage ab etwa 6 bis 10&nbsp;kWp und mindestens rund 1,4&nbsp;kW Überschuss. Ein Balkonkraftwerk mit 800&nbsp;W reicht dafür nicht.',
}
SKIP_LD = {'impressum.html', 'datenschutz.html', '404.html', 'index.html'}
LD_RE = re.compile(r'<script type="application/ld\+json" id="ld">.*?</script>\n?', re.S)
def toc(main):
    """Inhaltsverzeichnis mit Lesezeit für den Kasten „Kurz gesagt“."""
    items = []
    for sid, body in re.findall(r'<section[^>]*\bid="([^"]+)"[^>]*>(.*?)</section>', main, re.S):
        if sid in ('quellen', 'kurz-gesagt'):
            continue
        m = re.search(r'<h2[^>]*>(.*?)</h2>', body, re.S)
        if m:
            items.append((sid, re.sub(r'<[^>]+>', '', m.group(1)).strip().rstrip('.')))
    if len(items) < 3:
        return ''
    words = len(re.sub(r'<script.*?</script>|<style.*?</style>|<[^>]+>', ' ', main, flags=re.S).split())
    mins = max(1, round(words / 200))
    lis = ''.join('<li><a href="#%s">%s</a></li>' % (i, t) for i, t in items)
    return '<details class="toc"><summary><span>Inhalt</span><span class="toc-t">%d Min. Lesezeit</span></summary><ol>%s</ol></details>' % (mins, lis)


KG_RE = re.compile(r'<section class="kurz-s">.*?</section>\n', re.S)


def text(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()


def meta(s, prop):
    m = re.search(r'<meta (?:name|property)="%s" content="([^"]*)"' % prop, s)
    return html.unescape(m.group(1)) if m else ''


def checked(s):
    m = re.search(r'Geprüft am (\d{2})\.(\d{2})\.(\d{4})', s)
    return '%s-%s-%s' % (m.group(3), m.group(2), m.group(1)) if m else None


def faqs(main):
    out = []
    for sec in re.findall(r'<section[^>]*>.*?</section>', main, re.S):
        if 'id="fragen"' not in sec and 'Kurz beantwortet' not in sec and 'Häufige Fragen' not in sec:
            continue
        for q, a in re.findall(r'<details(?![^>]*class="(?:help|more)")[^>]*>\s*<summary>(.*?)</summary>\s*<div>(.*?)</div>\s*</details>', sec, re.S):
            q, a = text(q), text(a)
            if q and a:
                out.append({'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}})
    return out


def run():
    llms = []
    for f in sorted(ROOT.glob('*.html')):
        s = f.read_text(encoding='utf-8')
        name = f.name
        title = re.search(r'<title>(.*?)</title>', s).group(1)
        desc = meta(s, 'description')
        url = SITE + ('/' if name == 'index.html' else '/' + name)
        if name not in {'impressum.html', 'datenschutz.html', '404.html'}:
            llms.append((name, html.unescape(title).replace(' – ' + NAME, ''), desc, url))
        if name in SKIP_LD:
            continue
        main = s[s.index('<main'):s.index('</main>')]
        # Kasten „Kurz gesagt“ vor dem ersten Abschnitt
        s = KG_RE.sub('', s)
        if name in KURZ:
            box = ('<section class="kurz-s"><div class="wrap read"><div class="kurz" id="kurz-gesagt"><b>Kurz gesagt</b><p>%s</p></div>%s</div></section>\n' % (KURZ[name], toc(main)))
            i = s.index('<section', s.index('<main'))
            s = s[:i] + box + s[i:]
        h1 = text(re.search(r'<h1[^>]*>(.*?)</h1>', main, re.S).group(1))
        day = checked(s)
        org = {'@type': 'Organization', 'name': NAME, 'url': SITE + '/'}
        art = {'@type': 'Article', 'headline': h1[:110], 'name': html.unescape(title), 'description': desc,
               'inLanguage': 'de-DE', 'url': url, 'mainEntityOfPage': url, 'author': org, 'publisher': org}
        img = meta(s, 'og:image')
        if img:
            art['image'] = img
        if day:
            art['dateModified'] = day
        if name in KURZ:
            art['abstract'] = text(KURZ[name])
        graph = [art]
        q = faqs(main)
        if q:
            graph.append({'@type': 'FAQPage', 'mainEntity': q})
        graph.append({'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': NAME, 'item': SITE + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': h1[:80], 'item': url}]})
        ld = json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False).replace('</', '<\\/')
        s = LD_RE.sub('', s)
        s = s.replace('</head>', '<script type="application/ld+json" id="ld">%s</script>\n</head>' % ld, 1)
        f.write_text(s, encoding='utf-8')
        print('ok', name, 'Fragen:', len(q), 'Kurz:', name in KURZ)
    # llms.txt: Übersicht für KI-Assistenten
    lines = ['# %s' % NAME, '',
             '> Ratgeber-Website zu Strom zuhause in Deutschland: Balkonkraftwerk, Wallbox, E-Auto laden, Wärmepumpe, Stromtarif, Stromsparen und Notstrom. Mit Rechnern, Quellen und Prüfdatum. Finanziert über gekennzeichnete Amazon-Partnerlinks.', '',
             '## Ratgeber und Rechner', '']
    for name, t, d, u in llms:
        lines.append('- [%s](%s): %s' % (t, u, d))
    (ROOT / 'llms.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('llms.txt', len(llms), 'Seiten')


if __name__ == '__main__':
    run()
