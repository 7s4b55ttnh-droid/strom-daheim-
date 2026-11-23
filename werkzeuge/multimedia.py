"""Multimedia-Ratgeber (seit 22.11.2026, Auftrag des Inhabers): schreibt multimedia.html neu.

Aufruf im Repository-Ordner:  python3 werkzeuge/multimedia.py   (danach fusszeile.py und seo.py)
Schwester von smarthome.py: gleiche Bausteine (Karten, Stile, Regeln), eigene Inhalte. Beide Seiten verweisen aufeinander.
REGELN wie in smarthome.py: Preise = UVP des Herstellers am Tag STAND, Angaben von den Herstellerseiten (QUELLEN),
„Preis-Leistung“ ist unsere Einschätzung, kein eigener Test. Stiftung Warentest nur „geprüft MM/JJJJ“, keine Noten.
Fernseher und Beamer: keine eigene Modellauswahl mit Dafür und Dagegen, weil die Modelle jährlich wechseln; dafür Kriterien und Suchlinks.
"""
import re, pathlib
import smarthome as sh

ROOT = sh.ROOT
STAND, STAND_LANG = sh.STAND, sh.STAND_LANG

# (id, Emoji, Titel, Foto, Bildtext, Satz, kann[], achte[], Hinweis)
BEREICHE = [
    ('fernseher', '📺', 'Fernseher', 'multimedia-fernseher', 'Flacher Fernseher an einer hellen Wand über einem Lowboard aus Eiche',
     'Der Fernseher ist die Mitte. Bild, Größe und Anschlüsse entscheidest du hier, den Ton besser separat.',
     ['Streaming-Apps sind bei fast allen Geräten eingebaut', 'Aktuelle Geräte zeigen 4K und HDR', 'Über HDMI eARC geht der Ton zur Soundbar'],
     ['OLED oder LCD: Die meisten Geräte mit sehr gutem Bild im Test der Stiftung Warentest sind OLED', 'Die Größe: Spitzenmodelle beginnen meist bei 48&nbsp;Zoll, kleinere Geräte machen oft Abstriche', 'Mindestens ein HDMI-Anschluss mit eARC für die Soundbar'],
     'Stiftung Warentest führt 269 geprüfte Fernseher (Stand 10/2026), vom Gerät für unter 200&nbsp;€ bis etwa 2.800&nbsp;€. Gute Fernseher gibt es demnach schon für unter 400&nbsp;€, ab etwa 600&nbsp;€ wächst die Auswahl. OLED-Geräte kosten meist mindestens 1.000&nbsp;€.'),
    ('soundbar', '🔊', 'Soundbar', 'multimedia-soundbar', 'Schmale schwarze Soundbar auf einem Holz-Lowboard unter dem Fernseher, daneben ein Subwoofer',
     'Der größte Schritt für wenig Geld: Nur wenige Flachbildfernseher klingen laut Stiftung Warentest sehr gut. Eine Soundbar verbessert den Ton an jedem Gerät.',
     ['Klarere Stimmen und mehr Bass als die Lautsprecher im Fernseher', 'Viele spielen auch Musik über WLAN', 'Später um Subwoofer und Rücklautsprecher erweiterbar'],
     ['Anschluss: HDMI eARC ist der Standard, ältere Fernseher haben nur einen optischen Ausgang', 'Dolby Atmos braucht eine Soundbar, die es kann, und meist HDMI eARC', 'Die Breite sollte zum Fernseher passen'], ''),
    ('streaming', '🎬', 'Streaming-Box und Stick', 'multimedia-streaming', 'Kleine schwarze Streaming-Box, Fernbedienung und Streaming-Stick auf einem Lowboard',
     'Macht einen alten Fernseher wieder schnell und bringt alle Apps mit. Manche Boxen sind zugleich die Zentrale fürs Smarthome.',
     ['Alle großen Streaming-Dienste in einer Oberfläche', '4K, Dolby Vision und Dolby Atmos, wenn Fernseher und Dienst mitspielen', 'Einige steuern Lampen und Thermostate mit'],
     ['Passt die Box zu deinem Handy und deinem Smarthome-System?', 'Ein Netzwerkanschluss per Kabel hilft bei schwachem WLAN', 'Braucht einen freien HDMI-Anschluss am Fernseher'], ''),
    ('multiroom', '🎵', 'Musik in mehreren Räumen', 'multimedia-multiroom', 'Weißer Funklautsprecher im Küchenregal, im Hintergrund ein zweiter im Wohnzimmer',
     'Lautsprecher im WLAN spielen dieselbe Musik in Küche, Bad und Wohnzimmer oder in jedem Raum etwas anderes.',
     ['Lautsprecher per App zu Gruppen zusammenfassen', 'Musik vom Handy schicken, etwa per AirPlay&nbsp;2 oder Spotify Connect', 'Zwei gleiche Lautsprecher als Stereo-Paar oder hinter dem Sofa als Rücklautsprecher'],
     ['Bleib bei einem System, dann arbeiten alle Lautsprecher zusammen', 'WLAN in jedem Raum prüfen', 'Mit Mikrofon oder ohne: Sprachsteuerung ist nicht jedem recht'], ''),
    ('beamer', '📽️', 'Beamer', 'multimedia-beamer', 'Kleiner weißer Beamer auf einem Beistelltisch wirft ein großes Bild an die Wohnzimmerwand',
     'Für den Filmabend mit Bild über die ganze Wand. Ein Beamer ersetzt den Fernseher selten, ergänzt ihn aber gut.',
     ['Bilder mit zwei Metern Breite und mehr', 'Kleine Geräte mit Akku ziehen mit auf den Balkon', 'Viele haben Streaming-Apps und Lautsprecher eingebaut'],
     ['Helligkeit in Lumen: je heller der Raum, desto mehr brauchst du', 'Abstand zur Wand und Bildgröße stehen im Datenblatt', 'Eine helle, glatte Wand oder eine Leinwand'], ''),
    ('kopfhoerer', '🎧', 'Kopfhörer', 'multimedia-kopfhoerer', 'Weiße Bügelkopfhörer auf einer Sofalehne, daneben kleine Ohrhörer mit Ladehülle auf einem Holztisch',
     'Für den Film, wenn andere schlafen, und für Musik unterwegs. Manche Kopfhörer übernehmen den Ton direkt von der Soundbar.',
     ['Aktive Geräuschunterdrückung blendet Umgebungslärm aus', 'Spät abends Filme schauen, ohne jemanden zu wecken', 'Musik hören und telefonieren mit einem Gerät'],
     ['Über dem Ohr oder im Ohr: Probier aus, was du länger bequem trägst', 'Einige Funktionen gibt es nur im System des Herstellers', 'Akkulaufzeit mit eingeschalteter Geräuschunterdrückung vergleichen'], ''),
    ('receiver', '🎛️', 'AV-Receiver', 'multimedia-receiver', 'Schwarzer AV-Receiver in einem Eichen-Lowboard unter dem Fernseher, links und rechts schlanke Standlautsprecher',
     'Die Schaltzentrale für ein Heimkino mit einzelnen Lautsprechern. Wer mehr will als eine Soundbar, landet hier.',
     ['Verteilt Bild und Ton aller Geräte an Fernseher und Lautsprecher', 'Treibt fünf, sieben oder mehr Lautsprecher und einen Subwoofer an', 'Viele messen den Raum mit einem Mikrofon ein'],
     ['Genug HDMI-Eingänge für Konsole, Streaming-Box und Player', 'HDMI eARC für den Ton vom Fernseher', 'Platz im Regal: Ein Receiver wird warm und braucht Luft nach oben'],
     'Für die meisten Wohnzimmer reicht eine Soundbar. Ein AV-Receiver lohnt sich, wenn du Lautsprecher frei aufstellen kannst und Kabel verlegen magst.'),
    ('konsole', '🎮', 'Spielkonsole', 'multimedia-konsole', 'Weiße Spielkonsole neben dem Fernseher auf einem Lowboard, zwei Controller auf dem Couchtisch',
     'Spielen am großen Bild. Die Konsole hängt per HDMI am Fernseher und ist oft zugleich Streaming-Gerät.',
     ['Spiele von der Disc oder aus dem Online-Shop', 'Streaming-Apps laufen auch auf der Konsole', 'Mit mehreren Controllern gemeinsam auf dem Sofa spielen'],
     ['Welche Spiele willst du spielen? Viele Titel gibt es nur für eine Konsole', 'Mit oder ohne Laufwerk: Ohne Laufwerk kaufst du Spiele nur digital', 'Am Fernseher den Spielemodus einschalten, das verkürzt die Verzögerung'], ''),
]

# (id, Bereich, Name, Art, UVP, Hinweis, P/L, für wen, pro[], con[], Suchbegriff, Quelle)
MODELLE = [
    ('sonos-ray', 'soundbar', 'Sonos Ray', 'Kompakte Soundbar', 229, 'UVP', 'Gut', 'Kleine Räume und ältere Fernseher',
     ['Nur 56&nbsp;cm breit, passt ins TV-Möbel', 'Spielt Musik über WLAN, AirPlay&nbsp;2 und Spotify Connect', 'Mit Rücklautsprechern erweiterbar'],
     ['Nur optischer Eingang, kein HDMI', 'Kein Dolby Atmos', 'Keine Mikrofone, nur 2,4-GHz-WLAN'], 'Sonos Ray Soundbar', 3),
    ('sonos-beam', 'soundbar', 'Sonos Beam (Gen. 2)', 'Soundbar mit Dolby Atmos', 499, 'UVP', 'Sehr gut', 'Die meisten Wohnzimmer, Fernseher bis 65&nbsp;Zoll',
     ['Dolby Atmos', 'HDMI eARC, ein Adapter für den optischen Ausgang liegt bei', 'Alexa und Google Assistant eingebaut, AirPlay&nbsp;2', 'Um Subwoofer und Rücklautsprecher erweiterbar'],
     ['WLAN nur mit 2,4&nbsp;GHz, sonst per Netzwerkkabel', 'Das Einmessen auf den Raum braucht ein iPhone oder iPad'], 'Sonos Beam Gen 2', 4),
    ('sonos-arc', 'soundbar', 'Sonos Arc Ultra', 'Große Soundbar', 1099, 'UVP', 'Gut', 'Große Räume und große Fernseher',
     ['Vom Hersteller für große Räume und Fernseher gebaut', 'Um Subwoofer und Rücklautsprecher erweiterbar'],
     ['Mehr als doppelt so teuer wie die Beam'], 'Sonos Arc Ultra', 5),
    ('google-streamer', 'streaming', 'Google TV Streamer (4K)', 'Streaming-Box', 169, 'UVP', 'Gut', 'Android-Haushalte und Google Home',
     ['4K mit HDR und Dolby Vision, Dolby Atmos', '32&nbsp;GB Speicher und Netzwerkanschluss per Kabel', 'Zentrale für Google Home und Matter, Thread eingebaut', 'Fernbedienung lässt sich per Knopf wiederfinden'],
     ['Teurer als ein einfacher Streaming-Stick'], 'Google TV Streamer 4K', 6),
    ('apple-tv', 'streaming', 'Apple TV 4K', 'Streaming-Box', None, '', 'Gut', 'Haushalte mit iPhone und Apple Home',
     ['Dolby Vision und HDR10+, Dolby Atmos', 'Steuerzentrale für Apple Home und Matter-Geräte', 'Mit HomePods als Heimkino-Lautsprecher nutzbar'],
     ['Vor allem für Apple-Haushalte sinnvoll'], 'Apple TV 4K', 7),
    ('sonos-era100', 'multiroom', 'Sonos Era 100', 'WLAN-Lautsprecher', 229, 'UVP', 'Sehr gut', 'Der Einstieg in Musik für mehrere Räume',
     ['WLAN und Bluetooth, AirPlay&nbsp;2', 'Stereo aus einem Gehäuse', 'Sprachsteuerung mit Sonos Voice und Alexa', 'Lässt sich als Rücklautsprecher zur Soundbar nutzen'],
     ['Für den Kabel-Eingang ist ein Adapter nötig, der extra kostet'], 'Sonos Era 100', 8),
    ('xgimi-mogo4', 'beamer', 'XGIMI MoGo 4', 'Kleiner Beamer mit Akku', 599, 'UVP', 'Gut', 'Balkon, Garten und Schlafzimmer',
     ['Akku für bis zu 2,5&nbsp;Stunden Film', 'Full HD, Google TV mit Netflix eingebaut', 'Wiegt 1,31&nbsp;kg, Lautsprecher mit 2&nbsp;×&nbsp;6&nbsp;Watt'],
     ['450&nbsp;ISO-Lumen: nur für dunkle Räume', 'Kein 4K'], 'XGIMI MoGo 4', 10),
    ('xgimi-horizon20', 'beamer', 'XGIMI Horizon 20', 'Heimkino-Beamer mit 4K', 1699, 'UVP', 'Gut', 'Der feste Platz im Wohnzimmer',
     ['4K und 3.200&nbsp;ISO-Lumen aus drei Lasern', 'Optischer Zoom und Lens-Shift: Bild verschieben, ohne den Beamer zu verrücken', 'Google TV mit Netflix eingebaut'],
     ['Teuer', 'Braucht einen festen Platz mit Abstand zur Wand'], 'XGIMI Horizon 20', 11),
    ('sonos-ace', 'kopfhoerer', 'Sonos Ace', 'Bügelkopfhörer mit Geräuschunterdrückung', 379, 'UVP', 'Gut', 'Alle mit einer Sonos-Soundbar, die abends leise weiterschauen wollen',
     ['Übernimmt per Tastendruck den Ton einer passenden Sonos-Soundbar', 'Bis zu 30 Stunden Laufzeit mit Geräuschunterdrückung laut Hersteller', 'Verlustfreier Ton über Bluetooth oder USB-C mit passenden Geräten', 'Kabel für USB-C und 3,5-mm-Klinke liegen bei'],
     ['Der Tonwechsel braucht eine Sonos-Soundbar und die Sonos-App', 'Mit 312&nbsp;Gramm kein Leichtgewicht'], 'Sonos Ace Kopfhörer', 12),
    ('airpods-pro3', 'kopfhoerer', 'Apple AirPods Pro 3', 'Ohrhörer mit Geräuschunterdrückung', 249, 'Preis im Shop des Herstellers', 'Gut', 'Alle mit iPhone, die kleine Ohrhörer für unterwegs und zu Hause suchen',
     ['Bis zu 8 Stunden Wiedergabe mit Geräuschunterdrückung, mit Ladehülle bis zu 24 Stunden', 'Gegen Staub, Schweiß und Wasser geschützt (IP57)', 'Herzfrequenzmessung beim Training und Hörtest', 'Ladehülle mit USB-C, lädt auch kabellos'],
     ['Ausgelegt auf Geräte von Apple', 'Ohne Ladehülle ist nach spätestens 8 Stunden Schluss'], 'Apple AirPods Pro 3', 13),
]

AKTUELL = {'sonos-ray': 179, 'sonos-beam': 349, 'sonos-arc': 849, 'xgimi-mogo4': 399, 'xgimi-horizon20': 1299, 'sonos-ace': 199}   # Preis im Shop des Herstellers am Tag STAND

QUELLEN = [
    (1, 'Stiftung Warentest: Fernseher im Test (Stand 02.10.2026)', 'https://www.test.de/Fernseher-im-Test-1629201-0/', 'test.de'),
    (2, 'Sonos: Soundbars, Übersicht und Preise', 'https://www.sonos.com/de-de/shop/soundbars', 'sonos.com'),
    (3, 'Sonos: Ray', 'https://www.sonos.com/de-de/shop/ray', 'sonos.com'),
    (4, 'Sonos: Beam (Gen. 2)', 'https://www.sonos.com/de-de/shop/beam', 'sonos.com'),
    (5, 'Sonos: Arc Ultra, in der Übersicht der Soundbars', 'https://www.sonos.com/de-de/shop/soundbars', 'sonos.com'),
    (6, 'Google Store: Google TV Streamer (4K)', 'https://store.google.com/de/product/google_tv_streamer', 'store.google.com'),
    (7, 'Apple: Apple TV 4K', 'https://www.apple.com/de/apple-tv-4k/', 'apple.com'),
    (8, 'Sonos: Era 100', 'https://www.sonos.com/de-de/shop/era-100', 'sonos.com'),
    (10, 'XGIMI: MoGo 4', 'https://de.xgimi.com/products/mogo-4', 'xgimi.com'),
    (11, 'XGIMI: Horizon 20', 'https://de.xgimi.com/products/horizon-20', 'xgimi.com'),
    (9, 'Bundesamt für Sicherheit in der Informationstechnik: Smarthome sicher einrichten', 'https://www.bsi.bund.de/DE/Themen/Verbraucherinnen-und-Verbraucher/Informationen-und-Empfehlungen/Internet-der-Dinge-Smart-leben/Smart-Home/smart-home_node.html', 'bsi.bund.de'),
    (12, 'Sonos: Ace', 'https://www.sonos.com/de-de/shop/sonos-ace', 'sonos.com'),
    (13, 'Apple: AirPods Pro 3, Technische Daten', 'https://www.apple.com/de/airpods-pro/specs/', 'apple.com'),
]

FAQ = [
    ('Brauche ich eine Soundbar?', 'Meist lohnt sie sich. Laut Stiftung Warentest klingen nur wenige Flachbildfernseher sehr gut, externe Lautsprecher wie eine Soundbar verbessern den Ton an jedem Gerät.'),
    ('OLED oder LCD?', 'Die meisten Fernseher mit sehr gutem Bild im Test der Stiftung Warentest sind OLED-Geräte: tiefes Schwarz, starker Kontrast, breiter Blickwinkel. Sie kosten meist mindestens 1.000&nbsp;€. LCD-Geräte, die im Handel LED oder QLED heißen, können ebenfalls ein hohes Niveau erreichen.'),
    ('Was ist HDMI eARC?', 'Ein HDMI-Anschluss, über den der Fernseher den Ton an die Soundbar zurückgibt, auch in Formaten wie Dolby Atmos. Die Soundbar kommt an den HDMI-Anschluss des Fernsehers, der mit eARC oder ARC beschriftet ist.'),
    ('Brauche ich einen Streaming-Stick, wenn mein Fernseher smart ist?', 'Nicht unbedingt. Sinnvoll ist er, wenn der Fernseher langsam geworden ist, eine App fehlt oder die Box zugleich dein Smarthome steuern soll.'),
    ('Wie viel Strom braucht ein Fernseher?', 'Das hängt stark von Größe und Technik ab. Richtwerte und einen Rechner findest du unter <a href="/stromkosten/fernseher.html">Stromkosten eines Fernsehers</a>, das Energielabel erklärt die Seite <a href="/energielabel.html">Energielabel</a>.'),
    ('Kann ich Lautsprecher verschiedener Hersteller mischen?', 'Für Musik in mehreren Räumen besser nicht: Gruppen und Stereo-Paare funktionieren zuverlässig nur innerhalb eines Systems. Über AirPlay&nbsp;2 lassen sich Lautsprecher verschiedener Hersteller vom iPhone aus gemeinsam bespielen.'),
    ('Wie verbinde ich Multimedia mit dem Smarthome?', 'Über die Streaming-Box oder den Lautsprecher: Der Google TV Streamer ist Zentrale für Google Home, das Apple TV für Apple Home. Dann dimmt etwa das Licht, wenn der Film startet. Mehr dazu im <a href="/smarthome.html">Smarthome-Ratgeber</a>.'),
]

KETTE = '''<div class="sm-funk" tabindex="0" role="region" aria-label="Schema der Anschlüsse, auf schmalen Bildschirmen seitlich verschiebbar"><svg viewBox="0 0 720 300" role="img" aria-label="Schema: Streaming-Box und Spielkonsole hängen per HDMI am Fernseher. Der Fernseher gibt den Ton über HDMI eARC an die Soundbar. Rücklautsprecher und weitere Räume sind per WLAN verbunden.">
<g fill="none" stroke="currentColor" stroke-opacity=".45" stroke-width="2" stroke-linecap="round">
<path d="M170 80h100M170 200h60c20 0 20-80 40-100"/><path d="M400 110v60"/><path d="M470 205c60 0 70-60 130-60M470 205h130M470 205c60 0 70 50 130 50" stroke-dasharray="2 7"/>
</g>
<g class="sm-box"><rect x="40" y="50" width="130" height="60" rx="14"/><rect x="40" y="170" width="130" height="60" rx="14"/><rect x="270" y="40" width="260" height="70" rx="14"/><rect x="330" y="170" width="140" height="56" rx="14"/></g>
<g fill="currentColor" font-size="15" font-weight="700" text-anchor="middle"><text x="105" y="85">Streaming-Box</text><text x="105" y="205">Konsole</text><text x="400" y="81">Fernseher</text><text x="400" y="203">Soundbar</text></g>
<g fill="currentColor" font-size="13" font-weight="600"><text x="196" y="70">HDMI</text><text x="412" y="146">HDMI eARC</text><text x="608" y="149">Rücklautsprecher</text><text x="608" y="209">Subwoofer</text><text x="608" y="259">Weitere Räume</text></g>
<g fill="currentColor" font-size="13" opacity=".75"><text x="40" y="285">Durchgezogen: Kabel. Gepunktet: WLAN.</text></g>
</svg></div>'''

SCRIPT = '''<script>
/* Multimedia-Finder: schlägt aus drei Antworten Soundbar und Streaming-Box vor. Rechnet nur im Browser, speichert nichts. */
(function(){var f=document.getElementById('sm-form');if(!f)return;var out=document.getElementById('sm-out');var N=__NAMEN__;
function v(n){var e=f.querySelector('input[name="'+n+'"]:checked');return e?e.value:''}
function los(){var sb=v('tv')==='alt'?'sonos-ray':v('raum')==='gross'?'sonos-arc':v('raum')==='klein'&&v('atmos')==='nein'?'sonos-ray':'sonos-beam';
 var st=v('handy')==='iphone'?'apple-tv':'google-streamer';var L=[sb,st];if(v('raum')!=='klein')L.push('sonos-era100');
 var t=v('tv')==='alt'?'Für Fernseher mit optischem Ausgang ist die kleine Soundbar gebaut, und die Streaming-Box bringt die Apps zurück.':v('raum')==='gross'?'Ein großer Raum braucht eine große Soundbar. Zwei Lautsprecher hinter dem Sofa machen daraus Raumklang.':'Für die meisten Wohnzimmer reicht die mittlere Soundbar. Sie kann Dolby Atmos und lässt sich später erweitern.';
 out.innerHTML='<span class="eyebrow">Dein Heimkino</span><h3>'+N[sb][0]+'</h3><p>'+t+'</p><ul>'+L.map(function(x){return '<li><a href="#m-'+x+'">'+N[x][0]+'<span>'+N[x][1]+'</span></a></li>'}).join('')+'</ul>'}
f.addEventListener('change',los);los()})();
</script>
'''


def bereich(i, b):
    bid, emo, titel, foto, alt, satz, kann, achte, hinweis = b
    mods = [m for m in MODELLE if m[1] == bid]
    extra = ''

    def such(liste, emoji):
        return '<div class="items">%s</div>' % ''.join('<a class="item" href="%s" rel="sponsored nofollow noopener" target="_blank"><span class="ic" aria-hidden="true">%s</span><div><b>%s</b><span>%s</span></div><span class="go">Ansehen →</span></a>' % (sh.amz(q), emoji, t, s) for q, t, s in liste)
    if bid == 'fernseher':
        extra = ('<div class="sm-roh"><p>Für Fernseher nennen wir keine eigene Auswahl, weil die Modelle jedes Jahr wechseln und der Test der Stiftung Warentest die bessere Grundlage ist. Geprüft wurden dort 2026 unter anderem diese vier:</p>%s'
                 '<p class="hint">Die Links führen zu einer Suche bei Amazon.<span class="tag">Anzeige</span> Die Ergebnisse stehen im <a href="https://www.test.de/Fernseher-im-Test-1629201-0/" target="_blank" rel="noopener">Test bei test.de</a>.</p></div>'
                 % such([('LG OLED55B6', 'LG OLED B6, 55 Zoll', 'OLED, von der Stiftung Warentest geprüft (2026)'), ('Samsung GQ55S85H', 'Samsung S85H, 55 Zoll', 'Von der Stiftung Warentest geprüft (2026)'),
                         ('Hisense 55U7S Pro', 'Hisense U7S Pro, 55 Zoll', 'Von der Stiftung Warentest geprüft (2026)'), ('TCL 55C7L', 'TCL C7L, 55 Zoll', 'Von der Stiftung Warentest geprüft (2026)')], '📺'))
    if bid == 'beamer':
        extra = ('<div class="sm-roh">%s<p class="hint">Die Links führen zu einer Suche bei Amazon.<span class="tag">Anzeige</span> Vor dem Kauf Helligkeit, Auflösung und Abstand im Datenblatt vergleichen.</p></div>'
                 % such([('Beamer 4K Heimkino', 'Beamer mit 4K', 'Für den festen Platz im Wohnzimmer'), ('Mini Beamer Akku tragbar', 'Kleiner Beamer mit Akku', 'Für Balkon, Garten und unterwegs'),
                         ('Beamer Leinwand Rahmen', 'Leinwand', 'Macht das Bild heller und gleichmäßiger'), ('Beamer Deckenhalterung', 'Deckenhalterung', 'Hält den Beamer aus dem Weg')], '📽️'))
    if bid == 'receiver':
        extra = ('<div class="sm-roh"><p>AV-Receiver wechseln jedes Jahr, deshalb nennen wir keine einzelnen Modelle.</p>%s<p class="hint">Die Links führen zu einer Suche bei Amazon.<span class="tag">Anzeige</span> Vor dem Kauf Zahl der HDMI-Eingänge und der Lautsprecher-Kanäle im Datenblatt prüfen.</p></div>'
                 % such([('AV-Receiver 5.2 HDMI eARC', 'AV-Receiver mit 5 Kanälen', 'Für vorne links, Mitte, rechts und zwei Rücklautsprecher'), ('AV-Receiver 7.2 Dolby Atmos', 'AV-Receiver mit 7 Kanälen', 'Mit Platz für zwei Höhenlautsprecher'),
                         ('Lautsprecherkabel Kupfer 2,5 mm', 'Lautsprecherkabel', 'Vom Receiver zu jedem Lautsprecher'), ('HDMI Kabel Ultra High Speed', 'HDMI-Kabel „Ultra High Speed“', 'Für die Verbindung zum Fernseher')], '🎛️'))
    if bid == 'konsole':
        extra = ('<div class="sm-roh">%s<p class="hint">Die Links führen zu einer Suche bei Amazon.<span class="tag">Anzeige</span> Welche Konsole passt, entscheiden vor allem die Spiele, die du spielen willst.</p></div>'
                 % such([('PlayStation 5 Konsole', 'PlayStation 5', 'Von Sony, mit oder ohne Laufwerk'), ('Xbox Series X Konsole', 'Xbox Series X', 'Von Microsoft'),
                         ('Nintendo Switch 2 Konsole', 'Nintendo Switch 2', 'Von Nintendo, auch für unterwegs'), ('Controller Ladestation', 'Ladestation für Controller', 'Damit der zweite Controller immer voll ist')], '🎮'))
    return ('<section%s id="%s"><div class="wrap">\n'
            '<div class="sm-b"><div class="sm-bt"><span class="eyebrow">%s Bereich %d von %d</span><h2>%s</h2><p class="lede">%s</p>'
            '<div class="sm-2"><div><h3>Was es kann</h3><ul class="sm-l">%s</ul></div><div><h3>Worauf du achtest</h3><ul class="sm-l">%s</ul></div></div>%s</div>'
            '<figure class="sm-f">%s</figure></div>\n%s%s\n</div></section>\n'
            % (' class="band"' if i % 2 else '', bid, emo, i + 1, len(BEREICHE), titel + '.', satz,
               ''.join('<li>%s</li>' % x for x in kann), ''.join('<li>%s</li>' % x for x in achte),
               (('<p class="sm-n">%s</p>' % hinweis) if hinweis else '') + '<p style="margin:20px 0 0"><a class="btn sec" href="/multimedia/%s.html">Schritt für Schritt: %s</a></p>' % (bid, titel), sh.pic(foto, alt),
               ('<h3 class="sm-mh">Modelle im Vergleich</h3>%s<div class="sm-mg">%s</div>' % (sh.tabelle(mods, AKTUELL), ''.join(sh.karte(m, AKTUELL) for m in mods))) if mods else '', extra))


def main():
    v = (ROOT / 'infrarotheizung.html').read_text(encoding='utf-8')
    kopf, fuss = v[:v.index('<main id="main">')], v[v.index('</main>'):]
    fuss = re.sub(r'<script>\n/\* Infrarotheizung-Kosten-Rechner.*?</script>\n?', '', fuss, count=1, flags=re.S)
    assert 'Kosten-Rechner' not in fuss
    title = 'Multimedia zu Hause: Fernseher, Soundbar, Streaming – Strom-Daheim'
    desc = 'Heimkino einrichten: worauf es bei Fernseher, Soundbar, Streaming-Box und Beamer ankommt, wie alles zusammenhängt, und konkrete Modelle mit Preis.'
    ogd = 'Fernseher, Soundbar, Streaming-Box, Musik in mehreren Räumen und Beamer: was es gibt, wie du es anschließt und welche Geräte ihr Geld wert sind.'
    kopf = re.sub(r'<title>.*?</title>', '<title>%s</title>' % title, kopf, count=1)
    for prop, val in (('og:title', title), ('og:description', ogd), ('og:url', 'https://strom-daheim.de/multimedia.html'), ('og:image', 'https://strom-daheim.de/assets/og/multimedia.jpg')):
        kopf, n = re.subn(r'<meta property="%s" content="[^"]*">' % prop, '<meta property="%s" content="%s">' % (prop, val), kopf, count=1)
        assert n == 1, prop
    kopf, n = re.subn(r'<meta name="description" content="[^"]*">', '<meta name="description" content="%s">' % desc, kopf, count=1)
    assert n == 1
    kopf = kopf.replace('https://strom-daheim.de/infrarotheizung.html', 'https://strom-daheim.de/multimedia.html')
    kopf = re.sub(r'<script type="application/ld\+json" id="ld">.*?</script>\n?', '', kopf, flags=re.S)
    kopf = re.sub(r'<meta name="checked" content="[^"]*">', '', kopf)
    assert 'canonical" href="https://strom-daheim.de/multimedia.html' in kopf
    kopf = kopf.replace('</style>', sh.CSS + '.sm-nav.n5{grid-template-columns:repeat(5,1fr)}@media(max-width:1000px){.sm-nav.n5{grid-template-columns:1fr 1fr}}\n</style>', 1)

    nav = ''.join('<li><a href="#%s"><b>%d</b>%s</a></li>' % (b[0], i + 1, b[2]) for i, b in enumerate(BEREICHE))
    namen = '{%s}' % ','.join("'%s':['%s','%s']" % (m[0], m[2], (sh.eur(min(m[4], AKTUELL.get(m[0], m[4]))).replace('&nbsp;', ' ') if m[4] else 'Preis beim Händler')) for m in MODELLE)

    def frage(name, leg, opts):
        return '<fieldset><legend>%s</legend><div class="sm-ch">%s</div></fieldset>' % (leg, ''.join('<label><input type="radio" name="%s" value="%s"%s><span>%s</span></label>' % (name, val, ' checked' if k == 0 else '', t) for k, (val, t) in enumerate(opts)))

    def pk(k, titel, ids, text):
        return '<article><span class="k">%s</span><h3>%s</h3><ul>%s</ul><p>%s</p></article>' % (k, titel, ''.join('<li><a href="#m-%s">%s</a></li>' % (i, next(m[2] for m in MODELLE if m[0] == i)) for i in ids), text)

    m = '''<main id="main">
<div class="hero">
  <picture><source type="image/webp" srcset="assets/multimedia-m.webp 800w, assets/multimedia.webp 1280w" sizes="100vw"><img src="assets/multimedia.jpg" srcset="assets/multimedia-m.jpg 800w, assets/multimedia.jpg 1280w" sizes="100vw" alt="Dunkles Wohnzimmer am Abend mit großem Fernseher, Soundbar und warmem Licht hinter dem Bildschirm" width="1280" height="720" fetchpriority="high" decoding="async" style="object-position:72%% 50%%"></picture>
  <video class="hero-film" muted loop playsinline preload="none" aria-hidden="true" tabindex="-1" data-film="assets/multimedia" style="object-position:72%% 50%%"></video>
  <button class="hero-stop" type="button" aria-pressed="false">Film anhalten</button>
  <div class="wrap">
    <span class="eyebrow">Ratgeber · Stand %(stand_lang)s</span>
    <h1>Multimedia: Bild und Ton zu Hause.</h1>
    <p>Fernseher, Soundbar, Streaming, Musik in jedem Raum und Beamer. Was es gibt, wie du es anschließt und welche Geräte ihr Geld wert sind.</p>
    <div class="jump"><a class="pri" href="#finder">Was passt zu mir?</a><a href="#bereiche">Alle Bereiche</a><a href="#anschluss">So schließt du es an</a><a href="/smarthome.html">Zum Smarthome</a></div>
  </div>
</div>

<section id="start"><div class="wrap">
<div class="head"><span class="eyebrow">Der Einstieg</span><h2>In drei Schritten zum besseren Abend.</h2><p class="lede">Du musst nicht alles auf einmal kaufen. Diese Reihenfolge bringt am meisten für dein Geld.</p></div>
<ol class="sm-st" style="padding:0;margin:0">
<li><h3>Erst der Ton</h3><p>Eine Soundbar verbessert jeden Fernseher. Das ist der günstigste Schritt mit der größten Wirkung.</p></li>
<li><h3>Dann die Quelle</h3><p>Eine Streaming-Box macht einen alten Fernseher wieder schnell und kann dein Smarthome steuern.</p></li>
<li><h3>Zuletzt das Bild</h3><p>Ein neuer Fernseher lohnt sich, wenn der alte zu klein ist oder kein 4K kann. Miss vorher den Platz.</p></li>
</ol>
</div></section>

<section class="band" id="bereiche"><div class="wrap">
<div class="head"><span class="eyebrow">Überblick</span><h2>Acht Bausteine für Bild und Ton.</h2><p class="lede">Zu jedem steht unten, was er kann, worauf du achtest und welche Modelle wir empfehlen.</p></div>
<ol class="sm-nav n5" style="margin-top:0">%(nav)s</ol>
<h3 id="anschluss" style="margin-top:clamp(32px,5vw,52px)">So hängt alles zusammen.</h3>
%(kette)s
<p class="hint" style="margin-top:12px">Die Soundbar kommt an den HDMI-Anschluss des Fernsehers, der mit eARC oder ARC beschriftet ist. Alles andere steckst du an die übrigen HDMI-Anschlüsse.</p>
</div></section>

<section id="finder"><div class="wrap">
<div class="head"><span class="eyebrow">Finder</span><h2>Was passt zu mir?</h2><p class="lede">Vier Fragen, ein Vorschlag für Ton und Streaming.</p></div>
<div class="sm-fd"><form id="sm-form" onsubmit="return false">
%(f1)s%(f2)s%(f3)s%(f4)s
</form><div class="sm-res" id="sm-out" aria-live="polite"></div></div>
<p class="hint" style="margin-top:16px">Der Vorschlag folgt festen Regeln: Zu einem Fernseher ohne HDMI eARC passt die kleine Soundbar mit optischem Eingang, zu großen Räumen die große, sonst die mittlere. Mit iPhone das Apple TV, sonst der Google TV Streamer.</p>
</div></section>

%(bereiche)s
<section class="band" id="pakete"><div class="wrap">
<div class="head"><span class="eyebrow">Startpakete</span><h2>Drei Wege zum Heimkino.</h2><p class="lede">Zusammengestellt aus den Modellen oben. Tippe auf ein Gerät für Preis, Dafür und Dagegen.</p></div>
<div class="sm-pk">%(pakete)s</div>
</div></section>

<section id="smarthome"><div class="wrap read">
<div class="head"><span class="eyebrow">Verbinden</span><h2>Multimedia und Smarthome.</h2><p class="lede">Die Streaming-Box ist oft schon die Zentrale. Dann arbeiten Licht, Rollläden und Film zusammen.</p></div>
<ul class="sm-si">
<li><b>Filmabend</b>Ein Befehl dimmt das Licht, fährt die Rollläden herunter und schaltet den Fernseher ein.</li>
<li><b>Zentrale inklusive</b>Der Google TV Streamer steuert Google Home, das Apple TV steuert Apple Home, beide verstehen Matter.</li>
<li><b>Standby abschalten</b>Eine smarte Steckdose nimmt Konsole und Zubehör nachts vom Netz und zeigt den Verbrauch.</li>
<li><b>Sicher bleiben</b>Auch Fernseher und Lautsprecher brauchen Updates. Das BSI rät, automatische Updates einzuschalten und jedem Gerät ein eigenes Passwort zu geben.</li>
</ul>
<div class="cta" style="margin-top:24px"><a class="btn" href="/smarthome.html">Zum Smarthome-Ratgeber</a><a class="btn sec" href="/smarthome.html#steckdose">Smarte Steckdosen</a></div>
</div></section>

<section class="band" id="fragen"><div class="wrap read">
<div class="head"><span class="eyebrow">Häufige Fragen</span><h2>Kurz beantwortet.</h2></div>
%(faq)s
</div></section>

<section id="quellen"><div class="wrap read">
<div class="cta"><a class="btn" href="#finder">Zum Finder</a><a class="btn sec" href="/stromkosten/fernseher.html">Stromkosten eines Fernsehers</a></div>
<p class="hint" style="margin-top:18px">Was Konsole und Router an Strom brauchen, steht unter <a href="/stromkosten/spielkonsole.html">Spielkonsole</a> und <a href="/stromkosten/wlan-router.html">WLAN-Router</a>. Wo dein Strom sonst bleibt, zeigt <a href="/stromfresser.html">Stromfresser finden</a>.</p>
<div class="src" style="margin-top:32px"><b>Quellen</b><ol>
%(quellen)s
</ol><p style="margin-top:12px">Geprüft am %(stand)s. Preise sind unverbindliche Preisempfehlungen der Hersteller oder, wo angegeben, der Preis im Shop des Herstellers an diesem Tag. „Preis-Leistung“ ist unsere Einschätzung aus Preis und Ausstattung. Wir haben kein Gerät selbst getestet.</p></div>
</div></section>
''' % dict(stand=STAND, stand_lang=STAND_LANG, nav=nav, kette=KETTE,
           f1=frage('tv', 'Welchen Ton-Ausgang hat dein Fernseher?', [('neu', 'Hat HDMI mit ARC oder eARC'), ('alt', 'Nur optischer Ausgang')]),
           f2=frage('raum', 'Wie groß ist der Raum?', [('mittel', 'Normales Wohnzimmer'), ('klein', 'Klein, bis etwa 15 m²'), ('gross', 'Groß und offen')]),
           f3=frage('atmos', 'Ist dir Raumklang wichtig?', [('ja', 'Ja, gern Dolby Atmos'), ('nein', 'Hauptsache klare Stimmen')]),
           f4=frage('handy', 'Welches Handy nutzt du?', [('android', 'Android'), ('iphone', 'iPhone')]),
           bereiche=''.join(bereich(i, b) for i, b in enumerate(BEREICHE)),
           pakete=pk('Kleines Zimmer', 'Besserer Ton für wenig Geld', ['sonos-ray', 'google-streamer'], 'Passt an jeden Fernseher mit optischem Ausgang.')
           + pk('Wohnzimmer', 'Das runde Paket', ['sonos-beam', 'google-streamer', 'sonos-era100'], 'Dolby Atmos vorn, später zwei Lautsprecher nach hinten.')
           + pk('Apple-Haushalt', 'Alles in einer App', ['apple-tv', 'sonos-beam', 'sonos-era100'], 'Das Apple TV steuert zugleich Apple Home, die Lautsprecher spielen per AirPlay&nbsp;2.'),
           faq='\n'.join('<details><summary>%s</summary><div><p>%s</p></div></details>' % x for x in FAQ),
           quellen='\n'.join('<li>%s <a href="%s" target="_blank" rel="noopener">%s</a></li>' % (t, u, d) for _, t, u, d in sorted(QUELLEN)))
    assert sorted(q[0] for q in QUELLEN) == list(range(1, len(QUELLEN) + 1))
    for mo in MODELLE:
        assert any(b[0] == mo[1] for b in BEREICHE) and 1 <= mo[11] <= len(QUELLEN), mo[0]
    out = kopf + m + '</main>' + fuss[len('</main>'):].replace('<script>\n/* Besucherzähler', sh.FILM + SCRIPT.replace('__NAMEN__', namen) + '<script>\n/* Besucherzähler', 1)
    (ROOT / 'multimedia.html').write_text(out, encoding='utf-8')
    print('multimedia.html geschrieben:', len(out), 'Zeichen,', len(MODELLE), 'Modelle')


if __name__ == '__main__':
    main()
