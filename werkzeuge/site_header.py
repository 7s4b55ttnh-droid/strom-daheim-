"""Einheitliche Kopfzeile + Menü für Strom-Daheim. apply(html, page_key) ersetzt den vorhandenen Block."""
import re

SUN = '<svg class="th-sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2.2M12 19.3v2.2M4.6 4.6l1.6 1.6M17.8 17.8l1.6 1.6M2.5 12h2.2M19.3 12h2.2M4.6 19.4l1.6-1.6M17.8 6.2l1.6-1.6"/></svg>'
MOON = '<svg class="th-moon" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg>'
BURGER = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>'
CLOSE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg>'
BOLT = '<svg viewBox="0 0 64 64" aria-hidden="true"><path d="M35 10 19 36h11l-3 18 18-27H34z"/></svg>'
SHARE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v12M7 8l5-5 5 5M5 13v6a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-6"/></svg>'
PRINT = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 9V3h10v6M7 17H5a2 2 0 0 1-2-2v-4a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-2M7 14h10v7H7z"/></svg>'

NAV = [('/', 'Balkonkraftwerk', 'index'), ('/anleitung-balkonkraftwerk.html', 'Montage', 'anleitung-balkonkraftwerk'),
       ('/e-auto.html', 'E-Auto', 'e-auto'), ('/anleitung-wallbox.html', 'Wallbox', 'anleitung-wallbox'),
       ('/powerstation.html', 'Notstrom', 'powerstation')]
GRID = [('/#rechner-sektion', '☀️', 'Lohnt sich ein Balkonkraftwerk?', 'Rechner mit deinen Zahlen', None),
        ('/anleitung-balkonkraftwerk.html', '🔧', 'Balkonkraftwerk montieren', '8 Schritte und Einkaufsliste', 'anleitung-balkonkraftwerk'),
        ('/#vergleich', '⚖️', 'Welches Set kaufen?', '4 geprüfte Komplettsets', None),
        ('/#speicher', '🔋', 'Lohnt sich ein Speicher?', 'Zwei Rechenbeispiele', None),
        ('/e-auto.html', '🚗', 'Was kostet mein E-Auto?', 'Ladekosten-Rechner', 'e-auto'),
        ('/anleitung-wallbox.html', '🔌', 'Wallbox installieren', 'Schritte, Kosten, Förderung', 'anleitung-wallbox'),
        ('/powerstation.html', '🔦', 'Powerstation und Notstrom', 'Größen-Rechner und Vorsorge-Liste', 'powerstation'),
        ('/stromfresser.html', '💡', 'Stromfresser finden', 'Verbrauch vergleichen, Geräte-Rechner', 'stromfresser'),
        ('/stromtarif.html', '💶', 'Stromtarif wechseln', 'Wechsel-Rechner, dynamischer Tarif', 'stromtarif'),
        ('/waermepumpe.html', '♨️', 'Wärmepumpe', 'Kosten, Förderung, Altbau', 'waermepumpe'),
        ('/solar-laden.html', '🌞', 'E-Auto mit Solarstrom laden', 'Überschussladen und Rechner', 'solar-laden'),
        ('/pv-anlage.html', '🏠', 'Solaranlage aufs Dach', 'Kosten, Ertrag, EEG-Reform', 'pv-anlage'),
        ('/#ratgeber', '📋', 'Anmelden, Mieten, Tarif', 'Kurz erklärt', None)]
CUR = ' aria-current="page"'


def block(page):
    links = ''.join('<a href="%s"%s>%s</a>' % (h, CUR if k == page else '', t) for h, t, k in NAV)
    grid = ''.join('<a href="%s"%s><span class="i" aria-hidden="true">%s</span><span><b>%s</b><small>%s</small></span></a>'
                   % (h, CUR if k == page else '', i, t, sub) for h, i, t, sub, k in GRID)
    return ('<a class="skip" href="#main">Zum Inhalt springen</a>\n'
            '<header class="sh" id="sh"><div class="sh-in"><a class="sh-logo" href="/">' + BOLT + '<span>Strom-Daheim</span></a>'
            '<nav class="sh-links" aria-label="Hauptmenü">' + links + '</nav>'
            '<button class="sh-ic" id="th" type="button" aria-label="Hell oder dunkel umschalten">' + SUN + MOON + '</button>'
            '<button class="sh-ic sh-mb" id="sh-mb" type="button" aria-expanded="false" aria-controls="sh-sheet">' + BURGER + '<span>Menü</span></button></div></header>\n'
            '<div class="sh-sheet" id="sh-sheet" hidden role="dialog" aria-modal="true" aria-label="Menü"><div class="sh-sheet-in">'
            '<div class="sh-top"><b>Strom-Daheim</b><button class="sh-ic" id="sh-close" type="button" aria-label="Menü schließen">' + CLOSE + '</button></div>'
            '<p class="sh-h">Ratgeber und Rechner</p><nav class="sh-grid" aria-label="Alle Ratgeber">' + grid + '</nav>'
            '<div id="sh-toc-wrap" hidden><p class="sh-h">Auf dieser Seite</p><nav class="sh-toc" id="sh-toc" aria-label="Auf dieser Seite"></nav></div>'
            '<p class="sh-foot"><a href="/so-arbeiten-wir.html">So arbeiten wir</a> · <a href="/impressum.html">Impressum</a> · <a href="/datenschutz.html">Datenschutz</a></p>'
            '</div></div>\n')


PAT = re.compile(r'<a class="skip" href="#main">Zum Inhalt springen</a>\n<header class="sh"[\s\S]*?<p class="sh-foot">[\s\S]*?</p></div></div>\n')


def apply(html, page):
    m = PAT.search(html)
    assert m, 'Kopfzeilen-Block nicht gefunden'
    return html[:m.start()] + block(page) + html[m.end():]
