#!/usr/bin/env python3
"""RSS-Feed für Pinterest (automatisch veröffentlichen).
Aufruf: python3 pinfeed.py <site-ordner> <https://domain>
Liest <site>/assets/pins/pins.json (Liste: datei, titel, text, link, datum JJJJ-MM-TT),
schreibt <site>/pins.xml. Nur Pins mit datum <= jetzt (Berlin; datum 'JJJJ-MM-TT' oder 'JJJJ-MM-TT HH:MM') kommen in den Feed:
so werden im Voraus eingeplante Pins Tag für Tag freigegeben. Neueste zuerst.
Bilder liegen in <site>/assets/pins/. Täglich einmal laufen lassen und pushen."""
import json, sys, pathlib, datetime, email.utils
from xml.sax.saxutils import escape as e
site, dom = pathlib.Path(sys.argv[1]), sys.argv[2].rstrip('/')
from zoneinfo import ZoneInfo
jetzt = datetime.datetime.now(ZoneInfo('Europe/Berlin')).strftime('%Y-%m-%d %H:%M')
alle = json.load(open(site / 'assets/pins/pins.json'))
pins = [p for p in alle if (p['datum'] if len(p['datum']) > 10 else p['datum'] + ' 00:00') <= jetzt]
pins.sort(key=lambda p: p['datum'], reverse=True)
def rfc(d):
    t = (datetime.datetime.strptime(d, '%Y-%m-%d %H:%M') if len(d) > 10 else datetime.datetime.strptime(d, '%Y-%m-%d').replace(hour=9)).replace(tzinfo=ZoneInfo('Europe/Berlin'))
    return email.utils.format_datetime(t)
items = []
for p in pins:
    img = '%s/assets/pins/%s' % (dom, p['datei'])
    size = (site / 'assets/pins' / p['datei']).stat().st_size
    items.append(
        '<item><title>%s</title><link>%s</link><guid isPermaLink="false">%s</guid>'
        '<pubDate>%s</pubDate><description>%s</description>'
        '<enclosure url="%s" length="%d" type="image/jpeg"/>'
        '<media:content url="%s" medium="image" type="image/jpeg" width="1000" height="1500"/></item>'
        % (e(p['titel']), e(p['link']), e(p['datei']), rfc(p['datum']),
           e('<img src="%s" alt="%s"><p>%s</p>' % (img, e(p['titel']), e(p['text']))),
           img, size, img))
xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
       '<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/"><channel>'
       '<title>%s Pins</title><link>%s/</link><description>Neue Pins</description><language>de-DE</language>%s'
       '</channel></rss>\n') % (e(dom.split('//')[1]), dom, ''.join(items))
(site / 'pins.xml').write_text(xml)
print(len(pins), 'von', len(alle), 'Pins freigegeben ->', site / 'pins.xml')
