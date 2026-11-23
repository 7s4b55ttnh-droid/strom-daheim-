#!/usr/bin/env python3
"""Schreibt ebike.html (E-Bike-Ratgeber). Aufruf: python3 werkzeuge/ebike.py   (nach smarthome.py, vor fusszeile.py und seo.py)

Aufbau wie smarthome.py: Kopf, Menü und Fuß kommen aus der Vorlage infrarotheizung.html, die Stile sm-* aus smarthome.CSS.
REGELN
- Jede Zahl stammt aus QUELLEN (ADAC, Verbraucherzentrale, Stiftung Warentest, ZIV, GDV). Kein eigener Test, keine Noten.
- Für E-Bikes nennen wir keine einzelnen Modelle mit Preis. Die Links führen zu einer Suche bei Amazon (mit „Anzeige“).
- ROCKBROS (Awin 122456, zugelassen 23.11.2026) steht nur beim Zubehör. Links über sh.awin().
- Der Rechner rechnet nur im Browser und speichert nichts.
"""
import re
import smarthome as sh

ROOT = sh.ROOT
STAND = '23.11.2026'
STAND_LANG = '23. November 2026'
RB = 122456


def rb(pfad=''):
    return sh.awin(RB, 'https://rockbrosbike.de/' + pfad)


# Typen: (id, Emoji, Titel, Foto, Bildtext, Satz, passt[], achte[], Hinweis, [(Suchbegriff, Titel, Untertitel)])
TYPEN = [
    ('city', '🏙️', 'City-E-Bike', 'ebike-city', 'Cremefarbenes E-Bike mit tiefem Einstieg und Korb vor einer Bäckerei in einer Altstadtgasse',
     'Aufrecht sitzen, bequem aufsteigen, alles dran: Licht, Schutzbleche, Gepäckträger. Gemacht für kurze Wege in der Stadt.',
     ['Einkauf, Arbeit, Arzt: Strecken bis etwa 15 Kilometer', 'Tiefer Einstieg, auch mit Rock oder steifer Hüfte', 'Wenig Pflege mit Nabenschaltung und Kettenschutz'],
     ['Tiefeinsteiger oder Rahmen mit Oberrohr: Probier beides', 'Hydraulische Bremsen, vor allem bei viel Gepäck', 'Lässt sich der Akku zum Laden abnehmen?'],
     'Jedes fünfte verkaufte E-Bike war 2025 ein Cityrad (19&nbsp;Prozent laut Zweirad-Industrie-Verband).',
     [('E-Bike City Tiefeinsteiger 28 Zoll', 'City-E-Bike mit tiefem Einstieg', 'Für Alltag und kurze Wege'), ('E-Bike Urban leicht Riemenantrieb', 'Leichtes Urban-E-Bike', 'Oft unter 20 Kilogramm, meist mit Motor im Hinterrad')]),
    ('trekking', '🚴', 'Trekking-E-Bike', 'ebike-trekking', 'Dunkelgraues Trekking-E-Bike mit Gepäckträger und Seitentasche an einem Flussufer',
     'Der Alleskönner: schnell genug für den Arbeitsweg, bequem genug für die Tagestour, stabil genug für Gepäck.',
     ['Pendeln und Touren von 20 bis 80 Kilometern', 'Kettenschaltung mit vielen Gängen für Steigungen', 'Gepäckträger für Taschen, oft mit Federgabel'],
     ['Mittelmotor: laut ADAC am beliebtesten, mit ausgewogenem Fahrverhalten', 'Zulässiges Gesamtgewicht: Rad, du und Gepäck zusammen', 'Probefahrt mit und ohne Motor, auch am Berg'],
     'Knapp jedes vierte verkaufte E-Bike war 2025 ein Trekkingrad (24&nbsp;Prozent laut Zweirad-Industrie-Verband).',
     [('E-Bike Trekking Mittelmotor 28 Zoll', 'Trekking-E-Bike mit Mittelmotor', 'Für Pendeln und Touren'), ('E-Bike SUV vollgefedert Gepäckträger', 'SUV-E-Bike', 'Breite Reifen, Federung und trotzdem alltagstauglich')]),
    ('mtb', '⛰️', 'E-Mountainbike', 'ebike-mtb', 'Schwarzes E-Mountainbike mit breiten Stollenreifen lehnt an einem Holzzaun im Herbstwald',
     'Breite Reifen, kräftiger Motor, starke Bremsen. Für Waldwege, Schotter und Trails.',
     ['Bergauf mit Unterstützung, bergab mit Federung', 'Hardtail mit Federgabel oder vollgefedert', 'Die meistverkaufte Gruppe unter den E-Bikes'],
     ['Für die Straße fehlen oft Licht, Schutzbleche und Ständer', 'Scheibenbremsen mit großen Scheiben', 'Schwerer als ein Rad ohne Motor: Heb es vor dem Kauf einmal an'],
     'E-Mountainbikes waren 2025 mit 38&nbsp;Prozent die größte Gruppe unter den verkauften E-Bikes (Zweirad-Industrie-Verband).',
     [('E-Mountainbike Hardtail 29 Zoll', 'E-Mountainbike Hardtail', 'Federgabel vorn, für Wald- und Schotterwege'), ('E-Mountainbike Fully', 'E-Mountainbike vollgefedert', 'Für Trails und grobes Gelände')]),
    ('lastenrad', '📦', 'E-Lastenrad', 'ebike-lastenrad', 'E-Lastenrad mit langer Holzkiste, zwei Einkaufskisten und Sitzbank vor einem Wohnhaus',
     'Ersetzt für viele Wege das Auto: Kinder, Wocheneinkauf oder Werkzeug fahren in der Kiste oder auf dem langen Gepäckträger mit.',
     ['Kinder zur Kita, Einkauf, Getränkekisten', 'Zwei Räder (wendig) oder drei Räder (kippstabil im Stand)', 'Longtail: verlängerter Gepäckträger statt Kiste, schmaler und leichter'],
     ['Zulässige Zuladung und Sitze mit Gurt für Kinder', 'Starke Bremsen: Das Gewicht ist hoch', 'Wo steht es über Nacht? Ein Lastenrad passt selten in den Keller'],
     'Knapp jedes zehnte verkaufte E-Bike war 2025 ein Lastenrad (9,5&nbsp;Prozent laut Zweirad-Industrie-Verband).',
     [('E-Lastenrad Familie Kindersitz', 'E-Lastenrad mit Kiste', 'Für Kinder und Einkauf'), ('E-Bike Longtail Cargo', 'Longtail-E-Bike', 'Langer Gepäckträger, fährt sich fast wie ein normales Rad')]),
    ('falt', '🧳', 'Kompakt- und Falt-E-Bike', 'ebike-falt', 'Zusammengeklapptes Falt-E-Bike mit kleinen Rädern im Flur einer Wohnung neben dem Schuhregal',
     'Kleine Räder, klappbar oder zumindest schmal. Für Pendler mit Bahn, kleine Wohnungen und das Wohnmobil.',
     ['Passt in den Kofferraum, in den Zug und in den Flur', 'Lässt sich oft auf mehrere Körpergrößen einstellen', 'Steht in der Wohnung sicherer als im Hof'],
     ['Gewicht: Du trägst es öfter als andere Räder', 'Faltmaß und wie schnell das Falten wirklich geht', 'Kleine Räder rollen auf Kopfsteinpflaster unruhiger'],
     '',
     [('E-Bike Klapprad 20 Zoll', 'Falt-E-Bike mit 20 Zoll', 'Zum Zusammenklappen'), ('E-Bike Kompaktrad 20 Zoll', 'Kompakt-E-Bike', 'Klein, aber nicht faltbar, dafür stabiler')]),
]

QUELLEN = [
    (1, 'ADAC: Unterschied E-Bike und Pedelec (Stand 20.07.2026)', 'https://www.adac.de/rund-ums-fahrzeug/zweirad/fahrrad-ebike-pedelec/vorschriften-verhalten/pedelec-ebike', 'adac.de'),
    (2, 'ADAC: E-Bike-Kauf, worauf es ankommt (Stand 24.04.2025)', 'https://www.adac.de/rund-ums-fahrzeug/elektromobilitaet/pedelec-kaufberatung/', 'adac.de'),
    (3, 'ADAC: E-Bike-Akku, Lebensdauer und Reichweite verlängern (Stand 16.10.2026)', 'https://www.adac.de/rund-ums-fahrzeug/zweirad/fahrrad-ebike-pedelec/kauf-ausruestung/e-bike-akku-pflegen/', 'adac.de'),
    (4, 'Zweirad-Industrie-Verband: Marktdaten Fahrradwirtschaft 2025 (11.03.2026)', 'https://www.ziv-zweirad.de/wp-content/uploads/2026/03/Marktdaten-Fahrradwirtschaft-2025.pdf', 'ziv-zweirad.de'),
    (5, 'Stiftung Warentest: E-Bikes im Test (30.04.2026)', 'https://www.test.de/E-Bike-Test-4733454-0/', 'test.de'),
    (6, 'Verbraucherzentrale: Versicherung gegen Fahrraddiebstahl (Stand 21.11.2025)', 'https://www.verbraucherzentrale.de/wissen/geld-versicherungen/weitere-versicherungen/fahrradversicherung-welcher-versicherungsschutz-ist-notwendig-13647', 'verbraucherzentrale.de'),
    (7, 'ZDFheute: Zahlen des Versicherer-Verbands GDV zum Fahrraddiebstahl 2024', 'https://www.zdfheute.de/panorama/kriminalitaet/fahrrad-diebstahl-zahlen-2024-100.html', 'zdfheute.de'),
]

FAQ = [
    ('Was ist der Unterschied zwischen E-Bike und Pedelec?', 'Im Alltag meinen fast alle mit „E-Bike“ ein Pedelec: Der Motor hilft nur, wenn du trittst, mit höchstens 250&nbsp;Watt und bis 25&nbsp;km/h. Rechtlich ist das ein Fahrrad. Ein E-Bike im engeren Sinn fährt auch ohne Treten und gilt laut ADAC in der Regel als Mofa oder Kleinkraftrad.'),
    ('Brauche ich einen Führerschein oder ein Kennzeichen?', 'Für ein Pedelec bis 25&nbsp;km/h nicht. Für ein S-Pedelec bis 45&nbsp;km/h brauchst du laut ADAC die Fahrerlaubnis der Klasse AM, ein Versicherungskennzeichen und einen Helm.'),
    ('Wie weit komme ich mit einer Akkuladung?', 'Der ADAC nennt 50 bis 100&nbsp;Kilometer im gemischten Betrieb, je nach Akku und Bedingungen. Laut Stiftung Warentest bestimmt die Kapazität des Akkus allein die Reichweite nicht: Unterstützungsstufe, Gewicht, Steigungen, Wind und Reifendruck zählen mit.'),
    ('Was kostet eine Akkuladung?', 'Ein Akku mit 500&nbsp;Wattstunden fasst eine halbe Kilowattstunde. Bei 35&nbsp;Cent je Kilowattstunde sind das rund 18&nbsp;Cent, Ladeverluste nicht mitgerechnet. Mit deinen Zahlen rechnet der <a href="#rechner">Rechner</a>.'),
    ('Wie lange hält ein E-Bike-Akku?', 'Der ADAC nennt für moderne Akkus etwa 500 bis 1.000 volle Ladezyklen oder rund 25.000 bis 60.000&nbsp;Kilometer. Danach ist der Akku nicht unbedingt defekt, er fasst aber weniger. Ein Ersatzakku kostet laut ADAC 300 bis 800&nbsp;€.'),
    ('Ist mein E-Bike über die Hausratversicherung versichert?', 'Pedelecs gelten als Fahrräder und sind laut Verbraucherzentrale meist mitversichert, aber nur gegen Einbruchdiebstahl, etwa aus dem verschlossenen Keller. Den Diebstahl auf der Straße deckt ein Zusatz zur Hausratversicherung oder eine eigene Fahrradversicherung. Prüfe die Versicherungssumme in deinem Vertrag.'),
    ('Darf ich den Akku in der Wohnung laden?', 'Ja. Der ADAC nennt Brände selten und empfiehlt trotzdem: auf nicht brennbarem Untergrund laden, weg von Vorhängen und Polstern, nicht lange unbeaufsichtigt, einen Rauchmelder in der Nähe, und das Ladegerät nach dem Laden ausstecken.'),
    ('Kann ich mit dem E-Bike auf dem Radweg fahren?', 'Mit dem Pedelec bis 25&nbsp;km/h ja, es ist rechtlich ein Fahrrad. S-Pedelecs gehören laut ADAC auf die Fahrbahn, Radwege sind grundsätzlich tabu. Baden-Württemberg und Nordrhein-Westfalen können Radwege unter Voraussetzungen freigeben.'),
]

CSS = sh.CSS + '''
/* E-Bike-Ratgeber: Stile dieser Seite (werkzeuge/ebike.py) */
.eb-kl{display:grid;gap:14px;grid-template-columns:repeat(3,minmax(0,1fr))}@media(max-width:860px){.eb-kl{grid-template-columns:1fr}}
.eb-kl article{background:var(--pan);border:1px solid color-mix(in srgb,var(--line) 60%,transparent);border-radius:24px;padding:22px}
.band .eb-kl article{background:var(--bg)}
.eb-kl h3{margin:0 0 4px}.eb-kl .w{color:var(--mut);margin:0 0 12px}.eb-kl ul{margin:0;padding-left:18px;display:grid;gap:6px}
.eb-kl .ok{display:inline-block;margin:0 0 10px;padding:4px 10px;border-radius:999px;font-size:.8rem;font-weight:700;background:color-mix(in srgb,var(--ok) 18%,transparent);color:var(--ink)}
.eb-kl .no{background:color-mix(in srgb,var(--warn) 20%,transparent)}
.eb-r{display:grid;gap:22px;grid-template-columns:minmax(0,1fr) minmax(0,1fr);align-items:start}@media(max-width:860px){.eb-r{grid-template-columns:1fr}}
.eb-in{background:var(--pan);border:1px solid color-mix(in srgb,var(--line) 60%,transparent);border-radius:24px;padding:22px;display:grid;gap:16px}
.eb-in label{display:grid;gap:6px;font-weight:600}.eb-in label span{font-weight:400;color:var(--mut);font-size:.9rem}
.eb-in .f{display:flex;align-items:center;gap:10px}.eb-in input{font:inherit;width:100%;min-height:46px;padding:0 14px;border-radius:14px;border:1.5px solid var(--line);background:var(--bg);color:var(--ink)}
.eb-in input:focus-visible{outline:3px solid var(--sky);outline-offset:2px}.eb-in .e{flex:none;min-width:74px;color:var(--mut)}
.eb-in h3{margin:6px 0 0}
.eb-out{background:var(--ink);color:var(--bg);border-radius:24px;padding:24px;display:grid;gap:14px}
.eb-out .z{display:flex;justify-content:space-between;gap:14px;align-items:baseline;border-bottom:1px solid color-mix(in srgb,var(--bg) 22%,transparent);padding-bottom:12px}
.eb-out .z:last-of-type{border:0;padding-bottom:0}.eb-out .z b{font-size:1.5rem;white-space:nowrap}.eb-out .g b{font-size:2.1rem}
.eb-out p{margin:0;font-size:.92rem;opacity:.85}
.eb-ak{display:grid;gap:14px;grid-template-columns:repeat(2,minmax(0,1fr))}@media(max-width:760px){.eb-ak{grid-template-columns:1fr}}
.eb-zu{display:grid;gap:22px;grid-template-columns:minmax(0,1.1fr) minmax(0,.9fr);align-items:start}@media(max-width:900px){.eb-zu{grid-template-columns:1fr}}
.eb-rb{margin-top:22px;background:var(--pan);border:1px solid color-mix(in srgb,var(--line) 60%,transparent);border-radius:24px;padding:22px}
.band .eb-rb{background:var(--bg)}.eb-rb h3{margin:0 0 6px}.eb-rb p{margin:0 0 14px;color:var(--mut)}
.eb-rb .l{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.eb-ch li{display:grid;grid-template-columns:28px 1fr;gap:10px;align-items:start}.eb-ch{list-style:none;padding:0;margin:0;display:grid;gap:12px}
.eb-ch li:before{content:"✓";display:grid;place-items:center;width:26px;height:26px;border-radius:50%;background:var(--sun);color:#000;font-weight:700;font-size:.85rem}
'''

SCRIPT = '''<script>
/* E-Bike-Finder und Kosten-Rechner. Rechnet nur im Browser, speichert nichts. */
(function(){
var f=document.getElementById('eb-form'),out=document.getElementById('eb-out');
var T={city:['City-E-Bike','Kurze Wege in der Stadt, bequem und mit voller Ausstattung.'],trekking:['Trekking-E-Bike','Der Alleskönner für Arbeitsweg und Tour.'],mtb:['E-Mountainbike','Für Waldwege, Schotter und Trails.'],lastenrad:['E-Lastenrad','Kinder und Einkauf fahren mit, oft statt des Autos.'],falt:['Kompakt- oder Falt-E-Bike','Klein genug für Zug, Kofferraum und Flur.']};
function v(n){var e=f.querySelector('input[name="'+n+'"]:checked');return e?e.value:''}
function los(){var t='trekking',w='';
 if(v('last')==='ja'){t='lastenrad';w='Du willst Kinder oder große Einkäufe mitnehmen.'}
 else if(v('platz')==='ja'){t='falt';w='Das Rad muss in Zug, Kofferraum oder Wohnung passen.'}
 else if(v('weg')==='gelaende'){t='mtb';w='Du fährst vor allem abseits der Straße.'}
 else if(v('weg')==='stadt'&&v('strecke')==='kurz'){t='city';w='Du fährst kurze Wege in der Stadt.'}
 else{w=v('strecke')==='lang'?'Du fährst längere Strecken und willst Gepäck mitnehmen können.':'Du fährst gemischt: Stadt, Radweg und auch mal eine Tour.'}
 out.innerHTML='<span class="eyebrow">Dein Typ</span><h3>'+T[t][0]+'</h3><p>'+T[t][1]+' '+w+'</p><ul><li><a href="#'+t+'">'+T[t][0]+'<span>Was es kann und worauf du achtest</span></a></li></ul>'+(v('strecke')==='lang'?'<p style="margin-top:14px;font-size:.9rem">Für lange Strecken lohnt ein Blick auf Akku und Reichweite weiter unten.</p>':'')}
f.addEventListener('change',los);los();
var R=document.getElementById('eb-rech');
function z(id){var x=parseFloat(String(document.getElementById(id).value).replace(',','.'));return isFinite(x)&&x>0?x:0}
function eur(x){return x.toLocaleString('de-DE',{minimumFractionDigits:2,maximumFractionDigits:2})+'\\u00a0€'}
function ct(x){return x<1?Math.round(x*100)+'\\u00a0Cent':eur(x)}
function rech(){var wh=z('eb-wh'),km=z('eb-km'),p=z('eb-p')/100,j=z('eb-j'),l=z('eb-l'),s=z('eb-s');
 var lad=wh/1000*p,h=km?lad/km*100:0,jahr=h*j/100,auto=l*s,autoj=auto*j/100;
 var da=km>0&&wh>0;
 document.getElementById('eb-o1').textContent=wh?ct(lad):'–';document.getElementById('eb-o2').textContent=da?ct(h):'–';
 document.getElementById('eb-o3').textContent=da&&j?eur(jahr):'–';document.getElementById('eb-o4').textContent=l&&s?eur(auto):'–';
 document.getElementById('eb-o5').textContent=da&&j&&l&&s?eur(Math.max(0,autoj-jahr)):'–';
 document.getElementById('eb-o6').textContent=da&&j?Math.ceil(j/km)+' Ladungen im Jahr':''}
R.addEventListener('input',rech);rech()})();
</script>
'''


def frage(name, leg, opts):
    return '<fieldset><legend>%s</legend><div class="sm-ch">%s</div></fieldset>' % (leg, ''.join('<label><input type="radio" name="%s" value="%s"%s><span>%s</span></label>' % (name, val, ' checked' if k == 0 else '', t) for k, (val, t) in enumerate(opts)))


def such(liste, emoji):
    return '<div class="items">%s</div>' % ''.join('<a class="item" href="%s" rel="sponsored nofollow noopener" target="_blank"><span class="ic" aria-hidden="true">%s</span><div><b>%s</b><span>%s</span></div><span class="go">Ansehen →</span></a>' % (sh.amz(q), emoji, t, u) for q, t, u in liste)


def typ(i, b):
    bid, emo, titel, foto, alt, satz, passt, achte, hinweis, links = b
    return ('<section%s id="%s"><div class="wrap">\n'
            '<div class="sm-b"><div class="sm-bt"><span class="eyebrow">%s Typ %d von %d</span><h2>%s</h2><p class="lede">%s</p>'
            '<div class="sm-2"><div><h3>Wofür es passt</h3><ul class="sm-l">%s</ul></div><div><h3>Worauf du achtest</h3><ul class="sm-l">%s</ul></div></div>%s</div>'
            '<figure class="sm-f">%s</figure></div>\n'
            '<div class="sm-roh">%s<p class="hint">Die Links führen zu einer Suche bei Amazon.<span class="tag">Anzeige</span> Kauf ein E-Bike möglichst erst nach einer Probefahrt.</p></div>\n</div></section>\n'
            % (' class="band"' if i % 2 else '', bid, emo, i + 1, len(TYPEN), titel + '.', satz,
               ''.join('<li>%s</li>' % x for x in passt), ''.join('<li>%s</li>' % x for x in achte),
               ('<p class="sm-n">%s</p>' % hinweis) if hinweis else '', sh.pic(foto, alt), such(links, emo)))


def main():
    v = (ROOT / 'infrarotheizung.html').read_text(encoding='utf-8')
    kopf, fuss = v[:v.index('<main id="main">')], v[v.index('</main>'):]
    fuss = re.sub(r'<script>\n/\* Infrarotheizung-Kosten-Rechner.*?</script>\n?', '', fuss, count=1, flags=re.S)
    assert 'Kosten-Rechner' not in fuss, 'Vorlage: Fuß enthält noch das Rechner-Skript der Vorlage'
    title = 'E-Bike kaufen: Typen, Akku, Kosten, Regeln – Strom-Daheim'
    desc = 'E-Bike-Ratgeber: welcher Typ zu dir passt, Motor und Akku erklärt, was eine Ladung kostet, Regeln, Versicherung und Diebstahlschutz. Mit Rechner.'
    ogd = 'Welches E-Bike passt zu mir? Fünf Typen im Vergleich, Motor und Akku erklärt, Kosten-Rechner, Akkupflege, Regeln, Versicherung und Zubehör.'
    kopf = re.sub(r'<title>.*?</title>', '<title>%s</title>' % title, kopf, count=1)
    for prop, val in (('og:title', title), ('og:description', ogd), ('og:url', 'https://strom-daheim.de/ebike.html'), ('og:image', 'https://strom-daheim.de/assets/og/ebike.jpg')):
        kopf, n = re.subn(r'<meta property="%s" content="[^"]*">' % prop, '<meta property="%s" content="%s">' % (prop, val), kopf, count=1)
        assert n == 1, prop
    kopf, n = re.subn(r'<meta name="description" content="[^"]*">', '<meta name="description" content="%s">' % desc, kopf, count=1)
    assert n == 1
    kopf = kopf.replace('https://strom-daheim.de/infrarotheizung.html', 'https://strom-daheim.de/ebike.html')
    kopf = re.sub(r'<script type="application/ld\+json" id="ld">.*?</script>\n?', '', kopf, flags=re.S)
    kopf = re.sub(r'<meta name="checked" content="[^"]*">', '', kopf)
    assert 'canonical" href="https://strom-daheim.de/ebike.html' in kopf, 'Vorlage: kanonische Adresse nicht ersetzt'
    kopf = kopf.replace('</style>', CSS + '</style>', 1)

    nav = ''.join('<li><a href="#%s"><b>%d</b>%s</a></li>' % (b[0], i + 1, b[2]) for i, b in enumerate(TYPEN))
    zub = [('Fahrradhelm Erwachsene MIPS', 'Helm', 'Stiftung Warentest rät zu einem geprüften Helm'), ('Fahrradschloss Faltschloss Sicherheitsstufe hoch', 'Falt- oder Bügelschloss', 'Am besten zwei Schlösser für Rahmen und Räder'),
           ('Fahrradtasche Gepäckträger wasserdicht', 'Gepäckträgertasche', 'Wasserdicht, für Einkauf und Arbeitsweg'), ('Fahrradbeleuchtung Set StVZO USB', 'Licht mit StVZO-Zulassung', 'Für Räder ohne fest verbautes Licht'),
           ('Handyhalterung Fahrrad Lenker', 'Handyhalter', 'Für die Navigation am Lenker'), ('Standluftpumpe Manometer Fahrrad', 'Standpumpe mit Manometer', 'Richtiger Reifendruck spart Akku')]
    m = '''<main id="main">
<div class="hero">
  <picture><source type="image/webp" srcset="assets/ebike-m.webp 800w, assets/ebike.webp 1280w" sizes="100vw"><img src="assets/ebike.jpg" srcset="assets/ebike-m.jpg 800w, assets/ebike.jpg 1280w" sizes="100vw" alt="Dunkelgraues E-Bike mit Akku im Rahmen steht im Abendlicht auf einem Radweg zwischen Feldern" width="1280" height="720" fetchpriority="high" decoding="async" style="object-position:60%% 50%%"></picture>
  <div class="wrap">
    <span class="eyebrow">Ratgeber · Stand %(stand_lang)s</span>
    <h1>E-Bike: So findest du das richtige.</h1>
    <p>Welcher Typ zu dir passt, was Motor und Akku können, was eine Ladung kostet und welche Regeln gelten. Mit Rechner für deine Strecke.</p>
    <div class="jump"><a class="pri" href="#finder">Welcher Typ passt?</a><a href="#typen">Alle Typen</a><a href="#rechner">Kosten-Rechner</a><a href="#akku">Akku pflegen</a><a href="#zubehoer">Zubehör</a></div>
  </div>
</div>

<section id="begriffe"><div class="wrap">
<div class="head"><span class="eyebrow">Erst die Begriffe</span><h2>E-Bike, Pedelec, S-Pedelec.</h2><p class="lede">Fast alles, was als „E-Bike“ verkauft wird, ist ein Pedelec. Rechtlich macht das einen großen Unterschied.</p></div>
<div class="eb-kl">
<article><span class="ok">Gilt als Fahrrad</span><h3>Pedelec</h3><p class="w">Der Motor hilft nur beim Treten.</p><ul><li>Bis 25&nbsp;km/h, Motor mit höchstens 250&nbsp;Watt</li><li>Schiebehilfe bis 6&nbsp;km/h erlaubt</li><li>Kein Führerschein, kein Kennzeichen, kein Mindestalter</li><li>Radwege wie mit dem Fahrrad</li></ul></article>
<article><span class="ok no">Gilt als Kraftfahrzeug</span><h3>S-Pedelec</h3><p class="w">Unterstützung beim Treten bis 45&nbsp;km/h.</p><ul><li>Fahrerlaubnis Klasse AM</li><li>Versicherungskennzeichen</li><li>Helmpflicht</li><li>Nur auf der Fahrbahn, Radwege grundsätzlich tabu</li></ul></article>
<article><span class="ok no">Gilt meist als Mofa</span><h3>E-Bike im engeren Sinn</h3><p class="w">Fährt auch ohne Treten.</p><ul><li>Bis 25&nbsp;km/h in der Regel ein Mofa</li><li>Mofa-Prüfbescheinigung und Versicherungskennzeichen</li><li>Helmpflicht</li><li>Bis 45&nbsp;km/h ein Kleinkraftrad</li></ul></article>
</div>
<p class="hint" style="margin-top:16px">Angaben laut ADAC. Der ADAC rät, dass Kinder bis 14&nbsp;Jahre kein Pedelec fahren. In diesem Ratgeber meint „E-Bike“ das Pedelec bis 25&nbsp;km/h, wie im Alltag üblich.</p>
</div></section>

<section class="band" id="typen"><div class="wrap">
<div class="head"><span class="eyebrow">Überblick</span><h2>Fünf Typen, fünf Aufgaben.</h2><p class="lede">2025 wurden in Deutschland rund 2&nbsp;Millionen E-Bikes verkauft, im Schnitt für 2.550&nbsp;€. Welcher Typ passt, hängt davon ab, wo und wie weit du fährst.</p></div>
<ol class="sm-nav">%(nav)s</ol>
</div></section>

<section id="finder"><div class="wrap">
<div class="head"><span class="eyebrow">Finder</span><h2>Welcher Typ passt zu mir?</h2><p class="lede">Vier Fragen, ein Vorschlag.</p></div>
<div class="sm-fd"><form id="eb-form" onsubmit="return false">
%(f1)s%(f2)s%(f3)s%(f4)s
</form><div class="sm-res" id="eb-out" aria-live="polite"></div></div>
<p class="hint" style="margin-top:16px">Der Vorschlag folgt festen Regeln: Wer Kinder oder große Lasten fährt, bekommt das Lastenrad. Wer das Rad tragen oder verstauen muss, das Faltrad. Gelände führt zum Mountainbike, kurze Stadtwege zum Cityrad, alles andere zum Trekkingrad.</p>
</div></section>

%(typen)s
<section class="band" id="technik"><div class="wrap">
<div class="head"><span class="eyebrow">Technik</span><h2>Motor und Akku kurz erklärt.</h2><p class="lede">Zwei Bauteile entscheiden, wie sich ein E-Bike fährt und wie weit es kommt.</p></div>
<div class="tbl" tabindex="0" role="region" aria-label="Motorarten im Vergleich, auf schmalen Bildschirmen seitlich verschiebbar"><table><thead><tr><th>Motor</th><th>Stärke</th><th>Schwäche</th></tr></thead><tbody>
<tr><td>Mittelmotor am Tretlager</td><td>Am beliebtesten, ausgewogenes Fahrverhalten</td><td>Teurer, keine Rückgewinnung beim Rollen</td></tr>
<tr><td>Motor im Hinterrad</td><td>Gute Traktion, passt zu sportlichen und leichten Rädern</td><td>Hinten schwer, etwa beim Tragen über Treppen</td></tr>
<tr><td>Motor im Vorderrad</td><td>Häufig bei günstigen Rädern</td><td>Kann auf glattem Boden, am Berg und in Kurven durchdrehen oder wegrutschen</td></tr>
</tbody></table></div>
<p class="hint">Angaben laut ADAC. Räder mit Drehmomentsensor messen, wie kräftig du trittst, und unterstützen entsprechend. Einfache Trittsensoren an günstigen Rädern erkennen nur, dass sich die Pedale drehen.</p>
<div class="eb-ak" style="margin-top:clamp(28px,4vw,44px)">
<div><h3>Akku in Zahlen</h3><ul class="sm-l">
<li>Die Kapazität steht in Wattstunden (Wh) auf dem Akku: 500&nbsp;Wh sind eine halbe Kilowattstunde</li>
<li>Reichweite laut ADAC: 50 bis 100&nbsp;Kilometer im gemischten Betrieb</li>
<li>Lebensdauer laut ADAC: etwa 500 bis 1.000 volle Ladezyklen oder 25.000 bis 60.000&nbsp;Kilometer</li>
<li>Ersatzakku laut ADAC: 300 bis 800&nbsp;€</li></ul></div>
<div><h3>Was die Reichweite frisst</h3><ul class="sm-l">
<li>Hohe Unterstützungsstufe und häufiges Anfahren</li>
<li>Gewicht von dir, Gepäck und Anhänger</li>
<li>Steigungen und Gegenwind</li>
<li>Kälte: Sie senkt die Reichweite vorübergehend</li></ul></div>
</div>
<p class="hint">Laut Stiftung Warentest bestimmt die Kapazität des Akkus allein die Reichweite nicht, und viel Motorleistung ist nicht für jeden sinnvoll.</p>
</div></section>

<section id="rechner"><div class="wrap">
<div class="head"><span class="eyebrow">Rechner</span><h2>Was kostet mich das Fahren?</h2><p class="lede">Trag ein, was auf deinem Akku steht und wie weit du damit kommst. Der Vergleich mit dem Auto rechnet nur den Sprit.</p></div>
<div class="eb-r" id="eb-rech">
<div class="eb-in">
<label for="eb-wh">Akku<span>Steht auf dem Akku, üblich sind 400 bis 750&nbsp;Wh</span><div class="f"><input id="eb-wh" type="text" inputmode="decimal" value="500" autocomplete="off"><span class="e">Wh</span></div></label>
<label for="eb-km">Reichweite je Ladung<span>Aus deiner Erfahrung oder laut ADAC 50 bis 100&nbsp;km</span><div class="f"><input id="eb-km" type="text" inputmode="decimal" value="70" autocomplete="off"><span class="e">km</span></div></label>
<label for="eb-p">Strompreis<span>Arbeitspreis auf deiner Rechnung</span><div class="f"><input id="eb-p" type="text" inputmode="decimal" value="35" autocomplete="off"><span class="e">Cent/kWh</span></div></label>
<label for="eb-j">Strecke im Jahr<span>Zum Beispiel 10&nbsp;km am Tag an 200 Tagen</span><div class="f"><input id="eb-j" type="text" inputmode="decimal" value="2000" autocomplete="off"><span class="e">km</span></div></label>
<h3>Zum Vergleich: Auto</h3>
<label for="eb-l">Verbrauch<span>Dein Auto auf 100&nbsp;km</span><div class="f"><input id="eb-l" type="text" inputmode="decimal" value="7" autocomplete="off"><span class="e">Liter</span></div></label>
<label for="eb-s">Spritpreis<span>Was du zuletzt gezahlt hast</span><div class="f"><input id="eb-s" type="text" inputmode="decimal" value="1,75" autocomplete="off"><span class="e">€/Liter</span></div></label>
</div>
<div class="eb-out" aria-live="polite">
<div class="z"><span>Eine Akkuladung</span><b id="eb-o1"></b></div>
<div class="z g"><span>Strom auf 100&nbsp;km</span><b id="eb-o2"></b></div>
<div class="z"><span>Strom im Jahr</span><b id="eb-o3"></b></div>
<div class="z"><span>Sprit auf 100&nbsp;km mit dem Auto</span><b id="eb-o4"></b></div>
<div class="z"><span>Weniger Spritkosten im Jahr, wenn du diese Strecke statt mit dem Auto fährst</span><b id="eb-o5"></b></div>
<p id="eb-o6"></p>
<p>So rechnen wir: Akku in Kilowattstunden mal Strompreis ergibt die Ladung, geteilt durch die Reichweite die Kosten je Kilometer. Ladeverluste, Verschleiß, Versicherung und Anschaffung sind nicht enthalten. Die Vorgaben sind Beispielwerte, keine Messwerte.</p>
</div>
</div>
<p class="hint" style="margin-top:16px">Was das Laden eines Elektroautos kostet, rechnet der <a href="/e-auto.html">E-Auto-Rechner</a>.</p>
</div></section>

<section class="band" id="akku"><div class="wrap">
<div class="sm-b"><div class="sm-bt"><span class="eyebrow">🔋 Laden und Pflege</span><h2>So hält der Akku lange.</h2><p class="lede">Der Akku ist das teuerste Verschleißteil. Mit ein paar Gewohnheiten hält er deutlich länger. Alle Angaben laut ADAC.</p>
<div class="sm-2"><div><h3>Im Alltag</h3><ul class="sm-l"><li>Ladestand zwischen 20 und 80&nbsp;Prozent halten</li><li>Voll laden ist in Ordnung, wenn die Tour bald startet</li><li>Nicht unter 0&nbsp;Grad laden: Den kalten Akku erst auf Zimmertemperatur bringen</li><li>Hitze schadet mehr als Kälte, über 30&nbsp;Grad auf Dauer vermeiden</li></ul></div>
<div><h3>Im Winter und bei Pausen</h3><ul class="sm-l"><li>Mit 40 bis 60&nbsp;Prozent einlagern</li><li>Frostfrei lagern, der ADAC nennt 5 bis 20&nbsp;Grad</li><li>Alle 4 bis 8 Wochen den Ladestand prüfen</li><li>Akku nicht dauerhaft am Ladegerät lassen</li></ul></div></div>
<p class="sm-n">Sicher laden: auf nicht brennbarem Untergrund, weg von Vorhängen und Polstern, nicht lange unbeaufsichtigt und mit einem Rauchmelder in der Nähe. Nach dem Laden das Ladegerät ausstecken. Brände sind laut ADAC selten.</p></div>
<figure class="sm-f">%(pic_akku)s</figure></div>
</div></section>

<section id="kauf"><div class="wrap read">
<div class="head"><span class="eyebrow">Vor dem Kauf</span><h2>Sieben Punkte für die Probefahrt.</h2><p class="lede">Der Preis sagt laut Stiftung Warentest wenig über die Qualität. Im Test von zehn Urban-E-Bikes (Heft 5/2026) lagen die Preise zwischen etwa 1.200 und 3.720&nbsp;€.</p></div>
<ul class="eb-ch">
<li><span><b>Mehrere Räder fahren.</b> Mit Motor und ohne, auch an einer Steigung.</span></li>
<li><span><b>Anheben.</b> Ab etwa 25&nbsp;Kilogramm wird Tragen über Treppen laut ADAC schwierig.</span></li>
<li><span><b>Bremsen prüfen.</b> Der ADAC empfiehlt hydraulische Felgen- oder Scheibenbremsen, besonders bei viel Gepäck.</span></li>
<li><span><b>Gesamtgewicht nachlesen.</b> Rad, du und Gepäck müssen zusammen unter dem zulässigen Wert bleiben.</span></li>
<li><span><b>Akku abnehmen.</b> Geht das leicht, und kommst du am Stellplatz an eine Steckdose?</span></li>
<li><span><b>Anhänger geplant?</b> Dann die Freigabe des Herstellers prüfen.</span></li>
<li><span><b>Schaltung testen.</b> Die Gänge sollen auch am Berg leicht wechseln.</span></li>
</ul>
<p class="hint" style="margin-top:18px">Die Stiftung Warentest führt 41 geprüfte E-Bikes in ihrer Datenbank (Stand 04/2026), darunter Trekking-, City-, SUV- und Urban-Räder. Die Ergebnisse stehen im <a href="https://www.test.de/E-Bike-Test-4733454-0/" target="_blank" rel="noopener">Test bei test.de</a>.</p>
</div></section>

<section class="band" id="diebstahl"><div class="wrap">
<div class="sm-b"><div class="sm-bt"><span class="eyebrow">🔒 Diebstahl und Versicherung</span><h2>Gut abschließen, richtig versichern.</h2><p class="lede">2024 wurden den Versicherern rund 135.000 gestohlene Räder gemeldet. Der Schaden lag im Schnitt bei etwa 1.190&nbsp;€, so hoch wie nie. Diebe haben es vor allem auf teure Räder und E-Bikes abgesehen.</p>
<div class="sm-2"><div><h3>Abschließen</h3><ul class="sm-l"><li>Hochwertiges Bügel- oder Kettenschloss, am besten zwei</li><li>Rahmen und Räder an einen festen Gegenstand</li><li>Belebte, beleuchtete Plätze wählen</li><li>Kaufbeleg, Rahmennummer und aktuelle Fotos aufbewahren</li></ul></div>
<div><h3>Versichern</h3><ul class="sm-l"><li>Hausrat: meist nur Einbruchdiebstahl, etwa aus dem verschlossenen Keller</li><li>Diebstahl auf der Straße: Zusatz zur Hausrat oder eigene Fahrradversicherung</li><li>Eine eigene Fahrradversicherung kann auch Unfall, Sturz und Elektronik abdecken</li><li>Diebstahl sofort der Polizei und der Versicherung melden</li></ul></div></div>
<p class="sm-n">Laut Verbraucherzentrale lohnt eine eigene Fahrradversicherung meist nur bei wertvollen Rädern. Für ein Rad für 1.500&nbsp;€ lagen die Jahresbeiträge dort zwischen 48 und 370&nbsp;€. Vergleiche vor allem Kaufpreisgrenze, Selbstbeteiligung und vorgeschriebene Schlösser.</p></div>
<figure class="sm-f">%(pic_schloss)s</figure></div>
</div></section>

<section id="zubehoer"><div class="wrap">
<div class="head"><span class="eyebrow">Zubehör</span><h2>Was du zum Rad noch brauchst.</h2><p class="lede">Helm und Schloss gehören von Anfang an dazu. Der Rest macht den Alltag bequemer.</p></div>
<div class="eb-zu"><div>
<div class="sm-roh" style="margin-top:0">%(zub)s<p class="hint">Die Links führen zu einer Suche bei Amazon.<span class="tag">Anzeige</span></p></div>
<div class="eb-rb"><h3>Direkt beim Hersteller: ROCKBROS</h3><p>ROCKBROS baut seit 2010 Fahrradzubehör: Taschen, Beleuchtung, Helme, Brillen und Halterungen.</p>
<div class="l"><a class="btn" href="%(rb1)s" rel="sponsored nofollow noopener" target="_blank">Zum Shop von ROCKBROS</a><a class="btn sec" href="%(rb2)s" rel="sponsored nofollow noopener" target="_blank">Fahrradtaschen</a><span class="tag">Anzeige</span></div></div>
</div>
<figure class="sm-f">%(pic_zub)s</figure></div>
</div></section>

<section class="band" id="fragen"><div class="wrap read">
<div class="head"><span class="eyebrow">Häufige Fragen</span><h2>Kurz beantwortet.</h2></div>
%(faq)s
</div></section>

<section id="quellen"><div class="wrap read">
<div class="cta"><a class="btn" href="#finder">Zum Finder</a><a class="btn sec" href="/e-auto.html">Was kostet mein E-Auto?</a></div>
<p class="hint" style="margin-top:18px">Mehr zum Laden zu Hause: <a href="/anleitung-wallbox.html">Wallbox installieren</a> und <a href="/stromkosten.html">Stromkosten je Gerät</a>. Strom vom eigenen Balkon liefert das <a href="/">Balkonkraftwerk</a>.</p>
<div class="src" style="margin-top:32px"><b>Quellen</b><ol>
%(quellen)s
</ol><p style="margin-top:12px">Geprüft am %(stand)s. Wir haben kein Rad selbst getestet und geben keine Bewertungen aus Tests wieder. Regeln und Versicherungsbedingungen können sich ändern, maßgeblich sind Gesetz und dein Vertrag. Das ist keine Rechts- oder Versicherungsberatung.</p></div>
</div></section>
''' % dict(stand=STAND, stand_lang=STAND_LANG, nav=nav,
           f1=frage('weg', 'Wo fährst du vor allem?', [('stadt', 'In der Stadt'), ('gemischt', 'Stadt, Radweg, Landstraße'), ('gelaende', 'Wald und Gelände')]),
           f2=frage('strecke', 'Wie weit fährst du meist?', [('kurz', 'Bis 10 km'), ('mittel', '10 bis 30 km'), ('lang', 'Mehr als 30 km')]),
           f3=frage('last', 'Fahren Kinder oder große Einkäufe mit?', [('nein', 'Nein'), ('ja', 'Ja, regelmäßig')]),
           f4=frage('platz', 'Muss das Rad in Zug, Auto oder Wohnung?', [('nein', 'Nein'), ('ja', 'Ja')]),
           typen=''.join(typ(i, b) for i, b in enumerate(TYPEN)),
           pic_akku=sh.pic('ebike-akku', 'Abnehmbarer E-Bike-Akku lädt auf dem Fliesenboden eines Hauswirtschaftsraums, an der Decke ein Rauchmelder'),
           pic_schloss=sh.pic('ebike-schloss', 'E-Bike an einem Fahrradständer auf einem beleuchteten Platz in der Dämmerung'),
           pic_zub=sh.pic('ebike-zubehoer', 'Helm, Faltschloss, Gepäckträgertasche, Lichter, Handyhalter und Pumpe auf einer Werkbank'),
           zub=such(zub, '🚲'), rb1=rb(), rb2=rb('collections/fahrradtaschen-fur-pendler-touren-bikepacking'),
           faq='\n'.join('<details><summary>%s</summary><div><p>%s</p></div></details>' % x for x in FAQ),
           quellen='\n'.join('<li>%s <a href="%s" target="_blank" rel="noopener">%s</a></li>' % (t, u, d) for _, t, u, d in QUELLEN))
    assert [q[0] for q in QUELLEN] == list(range(1, len(QUELLEN) + 1))
    out = kopf + m + '</main>' + fuss[len('</main>'):].replace('<script>\n/* Besucherzähler', SCRIPT + '<script>\n/* Besucherzähler', 1)
    assert SCRIPT in out, 'Skript nicht eingefügt'
    import site_header
    out = site_header.apply(out, 'ebike')   # Menü mit dieser Seite als aktueller Seite
    (ROOT / 'ebike.html').write_text(out, encoding='utf-8')
    print('ebike.html geschrieben:', len(out), 'Zeichen,', len(TYPEN), 'Typen')


if __name__ == '__main__':
    main()
