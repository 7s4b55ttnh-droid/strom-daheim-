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
    'stromtarif.html': 'In der Grundversorgung zahlst du im Schnitt 40,39&nbsp;ct pro kWh, günstige Tarife liegen bei 31,13&nbsp;ct: Bei 2.500&nbsp;kWh sind das rund 230&nbsp;€ im Jahr. Der Wechsel ist kostenlos, technisch in 24 Stunden erledigt, und der Strom fließt ohne Unterbrechung weiter.',
    'stromfresser.html': 'Zwei Personen in einer Wohnung brauchen laut Stromspiegel 2025 im Schnitt 1.900&nbsp;kWh im Jahr; der Vergleich auf dieser Seite zeigt deine Klasse von A bis G. Die größten Stromfresser findest du mit einem Strommessgerät zwischen Steckdose und Gerät, Standby summiert sich dabei oft mehr als gedacht.',
    'waermepumpe.html': 'Im Altbau erreichen Luft-Wasser-Wärmepumpen laut Fraunhofer ISE im Mittel eine Jahresarbeitszahl von 3,4. Ob dein Haus passt, zeigt der 55-Grad-Test. Die KfW fördert seit 21. Juli 2026 mit 30&nbsp;% plus Boni, höchstens 70 bis 80&nbsp;% von 28.000&nbsp;€ Kosten.',
    'pv-anlage.html': 'Eine Photovoltaik-Anlage mit 10&nbsp;kWp kostet 2026 rund 12.000&nbsp;€, mit 10-kWh-Speicher rund 17.000&nbsp;€, und erzeugt etwa 9.000 bis 11.000&nbsp;kWh im Jahr. Lohnend ist vor allem der selbst genutzte Strom, denn die feste Einspeisevergütung für neue kleine Anlagen soll ab 2027 wegfallen; beschlossen ist das noch nicht.',
    'solar-laden.html': 'Mit PV-Überschussladen lädst du dein E-Auto mit Solarstrom, der 6 bis 14&nbsp;ct pro kWh kostet statt rund 37&nbsp;ct aus dem Netz. Dafür braucht es eine Dachanlage ab etwa 6 bis 10&nbsp;kWp und mindestens rund 1,4&nbsp;kW Überschuss. Ein Balkonkraftwerk mit 800&nbsp;W reicht dafür nicht.',
}
SKIP_LD = {'impressum.html', 'datenschutz.html', '404.html', 'index.html'}
LD_RE = re.compile(r'<script type="application/ld\+json" id="ld">.*?</script>\n?', re.S)
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
            box = ('<section class="kurz-s"><div class="wrap read"><div class="kurz" id="kurz-gesagt"><b>Kurz gesagt</b><p>%s</p></div></div></section>\n' % KURZ[name])
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
