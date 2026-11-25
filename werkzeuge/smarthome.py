"""Smarthome-Ratgeber (seit 22.11.2026, Auftrag des Inhabers): schreibt smarthome.html neu.

Aufruf im Repository-Ordner:  python3 werkzeuge/smarthome.py   (danach wie immer: fusszeile.py und seo.py)

Die Seite ist ein Einsteiger- und Kaufratgeber: wie anfangen, welches System, was es je Bereich gibt, konkrete Modelle.
REGELN
- Kopf, Menü und Fußzeile kommen aus infrarotheizung.html (Vorlage), nur <main> und die Seiten-Stile sind von hier.
- Modelle stehen in MODELLE. Jede Angabe (Preis, Funk, Akku, Abo) stammt von der Herstellerseite, Quelle steht in QUELLEN.
  Preis = unverbindliche Preisempfehlung des Herstellers am Tag STAND, nie ein Amazon-Preis. Fehlt die UVP, steht kein Preis da.
- „Preis-Leistung“ ist unsere Einschätzung aus Preis und Ausstattung. Wir haben kein Gerät selbst getestet, das steht auf der Seite.
- Stiftung Warentest: nur „geprüft, MM/JJJJ“ mit Link, keine Noten, kein „Testsieger“.
- Links zu Amazon sind Suchlinks mit dem Modellnamen, immer mit „Anzeige“ und rel="sponsored nofollow noopener".
- Fotos sind KI-Bilder ohne Marken und Menschen (assets/smarthome*.jpg); site.js setzt die KI-Marke.
"""
import re, pathlib, urllib.parse, html

ROOT = pathlib.Path(__file__).resolve().parent.parent
STAND = '22.11.2026'
STAND_LANG = '22. November 2026'
TAG = 'stromdaheim-21'


def amz(q):
    return 'https://www.amazon.de/s?k=%s&amp;tag=%s' % (urllib.parse.quote_plus(q), TAG)


# tink (Awin 13686, zugelassen 23.11.2026): Produktseiten, am 23.11.2026 über die Suche von tink.de geprüft.
# 25.11.2026: hue-white und fritz-thermo entfernt (Link-Wächter: tink-Seiten 404).
TINK = {
    'tado-x': 'tado-smartes-heizkoerper-thermostat-x-zusatzprodukt',
    'nuki-pro': 'nuki-smart-lock-pro-5-gen',
    'nuki-go': 'nuki-smart-lock-go',
    'hue-start': 'philips-hue-starter-set-mit-bridge-pro-und-2-white-and-color-ambiance-e27-lampen-1110-lm',
    'homepod-mini': 'apple-homepod-mini-2-gen',
    'tapo-p115': 'tp-link-tapo-p115-smarte-wlan-steckdose-rund',
    'hmip-evo': 'homematic-ip-heizkorperthermostat-evo-n',
    'echo-dot': 'amazon-echo-dot-5th-gen-smart-lautsprecher-mit-alexa',
    'fire-tv': 'amazon-fire-tv-stick-4k-plus-2025-release',
    'hmip-rauch': 'homematic-ip-rauchwarnmelder-mit-q-label',
    'sonos-ray': 'sonos-ray',
    'sonos-beam': 'sonos-beam-gen-2-smarte-tv-soundbar',
    'sonos-arc': 'sonos-arc-ultra-premium-soundbar-mit-dolby-atm',
}


def awin(mid, ziel):
    return 'https://www.awin1.com/cread.php?awinmid=%s&amp;awinaffid=3156925&amp;ued=%s' % (mid, urllib.parse.quote(ziel, safe=''))


def tink(mid):
    if mid not in TINK:
        return ''
    return '<a class="btn ghost sm-tk" href="%s" rel="sponsored nofollow noopener" target="_blank">Bei tink ansehen</a>' % awin(13686, 'https://www.tink.de/p/' + TINK[mid])


def pic(name, alt, sizes='(max-width:900px) 100vw, 520px', cls=''):
    return ('<picture><source type="image/webp" srcset="assets/%s-m.webp 800w, assets/%s.webp 1280w" sizes="%s">'
            '<img src="assets/%s.jpg" srcset="assets/%s-m.jpg 800w, assets/%s.jpg 1280w" sizes="%s" alt="%s" width="1280" height="720" loading="lazy" decoding="async"%s></picture>'
            % (name, name, sizes, name, name, name, sizes, alt, cls))


# Bereiche: (id, Emoji, Titel, Foto, Bildtext, Satz, kann[], achte[], Hinweis)
BEREICHE = [
    ('zentrale', '🧠', 'Zentrale und Sprachassistent', 'smarthome-zentrale', 'Kleiner Lautsprecher, weiße Zentrale und Türsensor auf einem Sideboard',
     'Die Zentrale verbindet deine Geräte und führt Automationen aus. Ein smarter Lautsprecher kann diese Rolle oft mit übernehmen.',
     ['Geräte verschiedener Hersteller in einer App bündeln', 'Abläufe starten: „Wenn die Tür aufgeht, geh das Flurlicht an“', 'Sprachbefehle und Steuerung von unterwegs'],
     ['Passt sie zu deinem Handy und zu den Geräten, die du schon hast?', 'Läuft sie auch ohne Internet weiter?', 'Welche Funkstandards spricht sie: Zigbee, Thread, Matter, DECT?'], ''),
    ('licht', '💡', 'Licht', 'smarthome-licht', 'Wohnzimmerecke am Abend mit einer warm leuchtenden Stehlampe und einer blaugrün leuchtenden Tischlampe',
     'Der einfachste Einstieg: alte Lampe raus, smarte Lampe rein. Kein Werkzeug, keine Erlaubnis nötig.',
     ['Per App, Sprache oder Zeitplan schalten und dimmen', 'Lichtfarbe von warm bis kalt, viele auch farbig', 'Anwesenheit vortäuschen, wenn du im Urlaub bist'],
     ['Fassung (E27, E14, GU10) und Helligkeit in Lumen', 'Mit oder ohne Zentrale? WLAN-Lampen brauchen keine, belasten bei vielen Lampen aber das WLAN', 'Der Wandschalter muss an bleiben, sonst ist die Lampe nicht erreichbar'], ''),
    ('steckdose', '🔌', 'Steckdosen', 'smarthome-steckdose', 'Weißer Zwischenstecker mit leuchtender Anzeige in einer Wandsteckdose, dahinter eine Tischlampe',
     'Ein Zwischenstecker macht fast jedes Gerät schaltbar und zeigt bei vielen Modellen, wie viel Strom es zieht.',
     ['Geräte nach Zeitplan oder aus der Ferne ein- und ausschalten', 'Stromverbrauch messen und Stromfresser finden', 'Standby-Geräte nachts ganz vom Netz nehmen'],
     ['Höchste Last in Watt: für Heizlüfter oder Waschmaschine wichtig', 'Mit Verbrauchsmessung oder ohne', 'Für draußen nur Modelle mit Spritzwasserschutz'], ''),
    ('heizung', '🌡️', 'Heizung', 'smarthome-heizung', 'Weißes smartes Thermostat mit der Anzeige 21 an einem Heizkörper unter dem Fenster',
     'Smarte Thermostate ersetzen den Drehknopf am Heizkörper. Den alten Kopf schraubst du ab, den neuen an. Wasser läuft dabei keines aus.',
     ['Heizen nach Zeitplan: morgens warm, tagsüber kühler', 'Absenken, wenn niemand da ist oder ein Fenster offen steht', 'Temperatur von unterwegs ändern'],
     ['Braucht das Thermostat eine Zentrale oder einen bestimmten Router?', 'Batterie oder Akku, und wie lange hält sie?', 'Kostet die App etwas, und laufen Zeitpläne auch ohne Internet?'],
     'Laut Verbraucherzentrale spart das automatische Absenken bei Abwesenheit je nach bisherigem Verhalten 2 bis 8&nbsp;Prozent der Heizkosten. Herstellerangaben zur höchsten Ersparnis solltest du kritisch sehen.'),
    ('tuerschloss', '🔐', 'Türschloss', 'smarthome-tuerschloss', 'Schwarzer runder Schlossantrieb an der Innenseite einer weißen Wohnungstür',
     'Ein smartes Schloss sitzt innen auf dem vorhandenen Zylinder und dreht den Schlüssel für dich. Von außen sieht die Tür aus wie vorher.',
     ['Tür mit dem Handy, per Code oder automatisch beim Heimkommen öffnen', 'Gästen oder Handwerkern Zugang auf Zeit geben', 'Sehen, ob abgeschlossen ist'],
     ['Passt es auf deinen Schließzylinder? Die Hersteller haben dafür eine Prüfung auf ihrer Seite', 'Akku oder Batterien', 'Ist der Zugriff von unterwegs im Preis enthalten?'],
     'In einer Mietwohnung bleibt der Zylinder unverändert, das Schloss lässt sich beim Auszug wieder abnehmen. Frag bei Zweifeln trotzdem deinen Vermieter und deine Hausratversicherung.'),
    ('kamera', '🚪', 'Klingel und Kamera', 'smarthome-kamera', 'Hauseingang am Abend mit schwarzer Video-Türklingel neben der Holztür und kleiner Kamera unter dem Vordach',
     'Eine Video-Klingel zeigt auf dem Handy, wer vor der Tür steht, auch wenn du nicht zu Hause bist. Kameras behalten Eingang oder Garten im Blick.',
     ['Mit Besuchern sprechen, ohne die Tür zu öffnen', 'Meldung aufs Handy, wenn sich jemand nähert', 'Aufnahmen auf Speicherkarte oder in der Cloud'],
     ['Speichert sie lokal, oder brauchst du ein Abo?', 'Strom aus dem Klingeldraht, vom Netzteil oder vom Akku', 'WLAN-Empfang an der Haustür vorher mit dem Handy prüfen'],
     'Richte Kameras nur auf dein eigenes Grundstück. Gehweg, Straße und das Grundstück der Nachbarn dürfen nicht im Bild sein.'),
    ('rollladen', '🪟', 'Rollläden', 'smarthome-rollladen', 'Schlafzimmerfenster am Morgen mit halb geöffnetem Rollladen, Sonnenstreifen auf dem Holzboden',
     'Rollläden fahren morgens von selbst hoch und abends herunter. Bei Motor-Rollläden reicht ein kleines Modul hinter dem Schalter, bei Gurten ein elektrischer Gurtwickler.',
     ['Nach Uhrzeit oder Sonnenstand öffnen und schließen', 'Im Sommer tagsüber verschatten', 'Alle Rollläden mit einem Befehl fahren'],
     ['Motor mit Endschaltern oder Gurt? Danach richtet sich das Gerät', 'Unterputz-Module arbeiten an 230&nbsp;Volt: Einbau durch eine Elektrofachkraft', 'Gurtwickler mit Stecker kannst du selbst tauschen'], ''),
    ('saugroboter', '🧹', 'Saugroboter', 'smarthome-saugroboter', 'Runder schwarzer Saugroboter auf Eichenparkett vor einem Teppich, hinten die weiße Ladestation',
     'Der Roboter saugt, während du weg bist. Viele wischen auch, und eine Station leert den Staubbehälter von selbst.',
     ['Nach Zeitplan oder per App starten', 'Einzelne Räume reinigen oder aussparen', 'Mit Station: Staub absaugen, Wasser tauschen, Wischtücher trocknen'],
     ['Vor allem Hartboden oder viel Teppich? Auf Teppich sind laut Stiftung Warentest nur wenige gut', 'Wischen ist bei vielen Modellen die Schwäche', 'Die Zahl in Pascal und Werbewörter sagen wenig über die Qualität'],
     'Stiftung Warentest hat bis 06/2026 insgesamt 44 Saug- und Wischroboter geprüft, sie kosten etwa 240 bis 1.300&nbsp;€. Der Preis sagt laut den Testern nicht immer etwas über die Qualität.'),
    ('sensoren', '🚨', 'Sensoren und Rauchmelder', 'smarthome-sensoren', 'Heller Flur mit einem weißen Rauchmelder an der Decke und einem kleinen Kontakt am Fensterrahmen',
     'Sensoren sind die Sinne des Smarthomes: Sie melden offene Fenster, Bewegung, Rauch oder Wasser und stoßen Abläufe an.',
     ['Fenster offen? Dann regelt das Thermostat die Heizung herunter', 'Bewegung im Flur schaltet das Licht', 'Vernetzte Rauchmelder schlagen gemeinsam Alarm'],
     ['Funk: Viele Sensoren nutzen Zigbee, Thread oder Bluetooth und brauchen eine Zentrale', 'Batterie: Knopfzellen halten laut Herstellern oft mehrere Jahre', 'Beim Rauchmelder auf das Q-Label und eine fest eingebaute Batterie achten'], ''),
    ('schalter', '🎚️', 'Lichtschalter', 'smarthome-schalter', 'Weißer Wandschalter und daneben ein kleiner Funk-Schalter mit vier Tasten in einer Wandhalterung',
     'Smarte Lampen brauchen Dauerstrom. Ein Funk-Schalter oder ein Modul hinter dem Wandschalter sorgt dafür, dass trotzdem jeder das Licht wie gewohnt bedient.',
     ['Licht schalten und dimmen, ohne zum Handy zu greifen', 'Szenen per Tastendruck: Lesen, Kochen, Filmabend', 'Funk-Schalter klebst du dorthin, wo nie ein Schalter war'],
     ['Passt der Schalter zu deinem Lampensystem?', 'Funk-Schalter mit Batterie brauchen kein Kabel und eignen sich für die Mietwohnung', 'Arbeiten in der Schalterdose sind Arbeiten an 230&nbsp;Volt und gehören in die Hand einer Elektrofachkraft'], ''),
    ('garten', '💧', 'Bewässerung', 'smarthome-garten', 'Grauer Bewässerungscomputer an einem Außenwasserhahn, im Hintergrund ein Rasensprenger im Morgenlicht',
     'Ein Bewässerungscomputer am Außenhahn gießt nach Zeitplan, auch wenn du im Urlaub bist.',
     ['Rasen und Beete zu festen Zeiten wässern', 'Zeitpläne per App ändern oder pausieren', 'Mit Wetterdaten oder einem Bodenfeuchte-Sensor das Gießen auslassen, wenn es nicht nötig ist'],
     ['Braucht das Gerät eine eigene Zentrale (Gateway)?', 'Reicht der Funk bis zum Wasserhahn?', 'Vor dem ersten Frost abnehmen und frostfrei lagern'], ''),
]

# Modelle: (id, Bereich, Name, Art, Preis in €, Preis-Hinweis, P/L, für wen, pro[], con[], Suchbegriff, Quelle-Nr.)
MODELLE = [
    ('ha-green', 'zentrale', 'Home Assistant Green', 'Zentrale für Tüftler', 179, 'UVP', 'Sehr gut', 'Alle, die unabhängig von einer Hersteller-Cloud bleiben wollen',
     ['Läuft lokal, auch wenn das Internet ausfällt', 'Deine Daten bleiben auf dem Gerät', 'Braucht nur etwa 1,7&nbsp;Watt im Leerlauf'],
     ['Für Zigbee und Thread ist ein zusätzlicher Funkstick nötig', 'Mehr Einarbeitung als bei Alexa oder Google'], 'Home Assistant Green', 3),
    ('fritz-gateway', 'zentrale', 'FRITZ!Smart Gateway', 'Zentrale für die FRITZ!Box', 79.99, 'UVP', 'Gut', 'Haushalte mit FRITZ!Box',
     ['Verbindet DECT, Zigbee und Matter', 'Bedienung über die Oberfläche der FRITZ!Box'],
     ['Gedacht für das FRITZ!-Heimnetz'], 'FRITZ!Smart Gateway', 4),
    ('homepod-mini', 'zentrale', 'Apple HomePod mini', 'Lautsprecher und Steuerzentrale', None, '', 'Gut', 'Haushalte mit iPhone',
     ['Steuerzentrale für Apple Home, auch von unterwegs', 'Unterstützt Matter', 'Misst Temperatur und Luftfeuchte im Raum'],
     ['Einrichtung nur mit der Home-App von Apple', 'Ohne iPhone wenig sinnvoll'], 'Apple HomePod mini', 5),
    ('nest-hub', 'zentrale', 'Google Nest Hub (2. Generation)', 'Lautsprecher mit Bildschirm', 99.99, 'UVP', 'Gut', 'Android-Haushalte, die Geräte auch per Fingertipp steuern wollen',
     ['Bildschirm mit 7&nbsp;Zoll: Geräte per Tippen oder Sprache steuern', 'Keine Kamera eingebaut', 'Schlafsensor ohne Armband'],
     ['Welche Funkstandards er beherrscht, nennt die Produktseite nicht'], 'Google Nest Hub 2. Generation', 16),
    ('hue-start', 'licht', 'Philips Hue Starter-Set', '2 farbige E27-Lampen und Hue Bridge Pro', 219.99, 'UVP', 'Gut', 'Alle, die das Licht im ganzen Zuhause ausbauen wollen',
     ['Je Lampe bis zu 1.100&nbsp;Lumen', 'Die Bridge Pro verwaltet bis zu 150 Lampen', 'Funktioniert mit Alexa, Google Home und Apple Home, Matter über die Bridge'],
     ['Der teuerste Einstieg auf dieser Seite', 'Für Sprachsteuerung ist die Bridge nötig'], 'Philips Hue Starter Set E27 White Color Ambiance Bridge Pro', 6),
    ('tapo-l530e', 'licht', 'TP-Link Tapo L530E', 'Farbige E27-Lampe mit WLAN', None, '', 'Sehr gut', 'Einsteiger, die eine oder zwei Lampen smart machen wollen',
     ['Keine Zentrale nötig', '806&nbsp;Lumen, so hell wie eine 60-Watt-Glühlampe', 'Weiß von 2.500 bis 6.500&nbsp;Kelvin und 16&nbsp;Millionen Farben', 'Funktioniert mit Alexa und Google'],
     ['Nur 2,4-GHz-WLAN', 'Farbwechsel und Dimmen nur über App und Cloud', 'Apple Home nennt der Hersteller nicht'], 'TP-Link Tapo L530E', 7),
    ('hue-white', 'licht', 'Philips Hue White E27 (1.100 Lumen)', 'Einzelne Lampe, warmweiß', 24.99, 'UVP', 'Sehr gut', 'Der günstige Einstieg in Philips Hue',
     ['1.100&nbsp;Lumen, deutlich heller als eine 60-Watt-Glühlampe', 'Funktioniert per Bluetooth auch ohne Bridge, auf etwa 9&nbsp;Meter', 'Lässt sich später mit einer Bridge ins große System holen'],
     ['Nur Warmweiß mit 2.700&nbsp;Kelvin, keine Farben', 'Sprachassistenten brauchen die Bridge'], 'Philips Hue White E27 1100 Lumen', 17),
    ('fritz-energy', 'steckdose', 'FRITZ!Smart Energy 200', 'Steckdose mit Verbrauchsmessung', 39.99, 'UVP', 'Gut', 'Haushalte mit FRITZ!Box',
     ['Misst den Stromverbrauch', 'Läuft über die FRITZ!Box, keine weitere Zentrale'],
     ['Gedacht für das FRITZ!-Heimnetz'], 'FRITZ!Smart Energy 200', 4),
    ('tapo-p115', 'steckdose', 'TP-Link Tapo P115', 'Kleine WLAN-Steckdose mit Verbrauchsmessung', None, '', 'Sehr gut', 'Einsteiger ohne Zentrale',
     ['Keine Zentrale nötig', 'Schaltet bis 3.680&nbsp;Watt (16&nbsp;A)', 'Zeigt den Verbrauch und rechnet mit deinem Strompreis', 'Funktioniert mit Alexa und Google'],
     ['Nur 2,4-GHz-WLAN', 'Matter und Apple Home nennt der Hersteller bei diesem Modell nicht'], 'TP-Link Tapo P115', 8),
    ('shelly-plug', 'steckdose', 'Shelly Plug M Gen3', 'Kleine Steckdose mit Verbrauchsmessung', 9.93, 'Preis im Shop des Herstellers', 'Sehr gut', 'Alle, die mehrere Steckdosen günstig ausstatten wollen',
     ['Die günstigste Steckdose auf dieser Seite', 'Misst den Stromverbrauch', 'Unterstützt Matter'],
     ['Die Höchstlast steht im Datenblatt, vor dem Kauf prüfen'], 'Shelly Plug M Gen3', 18),
    ('fritz-thermo', 'heizung', 'FRITZ!Smart Thermo 302', 'Heizkörperthermostat', 54.99, 'UVP', 'Sehr gut', 'Haushalte mit FRITZ!Box',
     ['Läuft über die FRITZ!Box, keine weitere Zentrale', 'Von der Stiftung Warentest geprüft (09/2023, damals als FRITZ!DECT 302)'],
     ['Gedacht für das FRITZ!-Heimnetz'], 'FRITZ!Smart Thermo 302', 4),
    ('hmip-evo', 'heizung', 'Homematic IP Heizkörperthermostat Evo', 'Heizkörperthermostat', None, '', 'Gut', 'Alle, die ein System ohne Abo aufbauen wollen',
     ['Zwei AA-Batterien halten laut Hersteller etwa zwei Jahre', 'Leiser Motor, Anzeige lässt sich drehen', 'Die App erhebt laut Hersteller außer der IP-Adresse keine persönlichen Daten', 'Sicherheits-Updates für mehr als fünf Jahre zugesagt', 'Von der Stiftung Warentest geprüft (09/2023)'],
     ['Braucht den Homematic IP Access Point oder die Zentrale CCU3'], 'Homematic IP Heizkörperthermostat Evo', 9),
    ('tado-x', 'heizung', 'tado° Smartes Heizkörper-Thermostat X', 'Heizkörperthermostat', 99.99, 'UVP', 'Gut', 'Alle, die Alexa, Google Home oder Apple Home nutzen',
     ['Funktioniert mit Alexa, Google Home, Apple Home und SmartThings', 'Senkt die Temperatur automatisch, wenn du das Haus verlässt', 'Vom Hersteller für den Einbau in Eigenregie gedacht, auch zur Miete'],
     ['Für den Start verkauft tado° ein eigenes Starter-Kit, das einzelne Thermostat ist die Ergänzung dazu', 'Vor dem Kauf prüfen, welche Funktionen ein Abo brauchen'], 'tado Smartes Heizkörper-Thermostat X', 19),
    ('fritz-control', 'heizung', 'FRITZ!Smart Control 350', 'Tür- und Fensterkontakt', 34.99, 'UVP', 'Gut', 'Ergänzung zum FRITZ!-Thermostat',
     ['Meldet ein offenes Fenster, das Thermostat senkt dann die Heizung ab', 'Lässt sich mit Automationen verknüpfen, etwa Licht aus beim Verlassen der Wohnung'],
     ['Gedacht für das FRITZ!-Heimnetz'], 'FRITZ!Smart Control 350', 20),
    ('nuki-pro', 'tuerschloss', 'Nuki Smart Lock Pro (5. Generation)', 'Türschloss mit Akku', 279, 'UVP', 'Gut', 'Alle, die Komfort ohne Zusatzkosten wollen',
     ['WLAN eingebaut, keine Bridge nötig', 'Matter über Thread', 'Zugriff von unterwegs ist im Preis enthalten', 'Montage innen an der Tür in unter fünf Minuten, ohne Bohren', 'Eingebauter Akku, in etwa zwei Stunden geladen'],
     ['Teuer', 'Passt nur auf geeignete Zylinder, vorher beim Hersteller prüfen'], 'Nuki Smart Lock Pro 5. Generation', 10),
    ('nuki-go', 'tuerschloss', 'Nuki Smart Lock Go', 'Türschloss mit Batterien', 149, 'UVP', 'Sehr gut', 'Einsteiger und Mietwohnungen',
     ['Fast halb so teuer wie das Pro', 'Passt auf viele Zylinder, auch auf ausgewählte Knaufzylinder'],
     ['Zugriff von unterwegs kostet einmalig 49&nbsp;€ extra', 'Vier AA-Batterien statt Akku', 'Nur eine Geschwindigkeit'], 'Nuki Smart Lock Go', 10),
    ('reolink-klingel', 'kamera', 'Reolink Video Doorbell WiFi', 'Video-Türklingel mit Kabel', None, '', 'Sehr gut', 'Hausbesitzer, die kein Abo wollen',
     ['Kein Abo nötig, speichert auf microSD bis 256&nbsp;GB', '5&nbsp;Megapixel, WLAN mit 2,4 und 5&nbsp;GHz', 'Erkennt Personen ohne Aufpreis', 'Ein Funk-Gong liegt bei'],
     ['Braucht Strom vom Klingeldraht (12 bis 24&nbsp;Volt) oder vom Netzteil, kein Akku', 'Arbeitet nicht mit einem vorhandenen mechanischen Gong zusammen'], 'Reolink Video Doorbell WiFi', 11),
    ('reolink-argus', 'kamera', 'Reolink Argus 4 Pro', 'Akku-Kamera für draußen', None, '', 'Gut', 'Garten, Carport und Stellen ohne Steckdose',
     ['Läuft mit Akku, kein Kabel nötig', '4K-Auflösung mit breitem Blickwinkel, farbige Nachtsicht', 'Speichert auf microSD, kein Abo nötig', 'Wetterfest nach IP66, WLAN&nbsp;6'],
     ['Das Solarpanel zum Nachladen kostet extra', 'Nachts leuchten Strahler, einen unsichtbaren Infrarot-Modus gibt es nicht'], 'Reolink Argus 4 Pro', 12),
    ('reolink-e1', 'kamera', 'Reolink E1 Pro', 'Schwenkbare Kamera für innen', None, '', 'Gut', 'Wohnung, Flur und Haustier im Blick',
     ['5&nbsp;Megapixel, schwenkt und folgt Bewegungen', 'Speichert auf microSD bis 512&nbsp;GB', 'Erkennt Personen und Haustiere', 'Privatmodus: dreht die Kamera weg und schaltet Aufnahme und Ton ab'],
     ['Nur für innen'], 'Reolink E1 Pro', 21),
    ('shelly-2pm', 'rollladen', 'Shelly 2PM Gen3', 'Unterputz-Modul für Motor-Rollläden', 38.90, 'UVP', 'Sehr gut', 'Eigentümer mit Motor-Rollläden',
     ['Passt in die Schalterdose hinter dem Rollladenschalter', 'WLAN und Matter, keine Zentrale nötig', 'Fährt auf Position und misst den Stromverbrauch', 'Funktioniert mit Alexa, Google Home und Home Assistant'],
     ['Arbeit an 230&nbsp;Volt: Einbau durch eine Elektrofachkraft', 'Der Motor braucht richtig eingestellte Endschalter'], 'Shelly 2PM Gen3', 13),
    ('qrevo-curv', 'saugroboter', 'Roborock Qrevo Curv', 'Saug- und Wischroboter mit Station', 1499, 'UVP', 'Gut', 'Wohnungen mit Hartboden und Türschwellen',
     ['Station leert den Staub, wäscht die Wischtücher mit 75&nbsp;Grad heißem Wasser und trocknet sie', 'Kommt laut Hersteller über Schwellen bis 3&nbsp;cm, über doppelte bis 4&nbsp;cm', 'Erkennt Hindernisse mit Kamera'],
     ['Die Station braucht 45&nbsp;×&nbsp;45&nbsp;×&nbsp;45&nbsp;cm Platz', 'Matter ist erst für ein späteres Update angekündigt', 'Hat eine Kamera: vorher die Datenschutz-Einstellungen ansehen'], 'Roborock Qrevo Curv', 22),
    ('saros-10', 'saugroboter', 'Roborock Saros 10', 'Flacher Saug- und Wischroboter mit Station', 1499, 'UVP', 'Gut', 'Wohnungen mit niedrigen Möbeln',
     ['Nur knapp 8&nbsp;cm hoch, der Sensor fährt ein', 'Station wäscht die Wischtücher mit bis zu 80&nbsp;Grad und leert den Staub', 'Unterstützt Matter'],
     ['Teuer', 'Hat eine Kamera: vorher die Datenschutz-Einstellungen ansehen'], 'Roborock Saros 10', 23),
    ('hmip-rauch', 'sensoren', 'Homematic IP Rauchwarnmelder mit Q-Label', 'Vernetzter Rauchmelder', None, '', 'Offen', 'Alle, die mehrere Räume und Etagen gemeinsam absichern wollen',
     ['Bis zu 40 Melder per Funk vernetzbar: Schlägt einer an, warnen alle', 'Fest eingebaute Batterien, laut Hersteller typisch etwa 10 Jahre', 'Sirene mit mehr als 85&nbsp;Dezibel in 3&nbsp;m Abstand', 'Trägt das Q-Label'],
     ['Batterien nicht wechselbar: Danach wird der ganze Melder getauscht', 'Eigener Funk auf 868&nbsp;MHz, gedacht für das System von Homematic IP'], 'Homematic IP Rauchwarnmelder Q-Label', 24),
    ('shelly-blu-dw', 'sensoren', 'Shelly BLU Door/Window ZB', 'Tür- und Fensterkontakt', 17.9, 'UVP', 'Sehr gut', 'Alle, die Fenster überwachen und die Heizung daran koppeln wollen',
     ['Erkennt offen und zu, bei Kippfenstern auch den Neigungswinkel', 'Misst zusätzlich die Helligkeit', 'Zigbee 3.0 und Bluetooth', 'Knopfzelle CR2032 liegt bei, laut Hersteller bis zu 5 Jahre Laufzeit'],
     ['Für die Shelly-App ist ein Gateway oder ein anderes Shelly-Gerät am Strom nötig', 'Reichweite in Räumen laut Hersteller bis zu 10&nbsp;m'], 'Shelly BLU Door Window ZB', 25),
    ('hue-dimmer', 'schalter', 'Philips Hue Dimmschalter', 'Funk-Schalter zum Kleben oder Schrauben', 21.99, 'Preis im Shop des Herstellers', 'Sehr gut', 'Mieter und alle, die ohne Kabel einen Schalter mehr wollen',
     ['Kein Kabel: Wandplatte kleben oder schrauben', 'Der Schalter haftet magnetisch und lässt sich abnehmen', 'Dimmen und zwischen Lichtszenen wechseln', 'Knopfzelle CR2032 liegt bei'],
     ['Eigene Tastenbelegungen richtest du nur mit der Hue Bridge ein', 'Der Wandschalter der Lampe muss weiter an bleiben'], 'Philips Hue Dimmschalter', 27),
    ('hue-modul', 'schalter', 'Philips Hue Wandschaltermodul', 'Modul hinter dem vorhandenen Lichtschalter', 49.99, 'Preis im Shop des Herstellers', 'Gut', 'Alle mit Hue-Lampen, bei denen der Wandschalter immer wieder versehentlich ausgeht',
     ['Sitzt hinter dem vorhandenen Schalter in der Unterputzdose', 'Die Lampen bleiben erreichbar, egal wer den Schalter drückt', 'Der Schalter kann Szenen aufrufen und Automationen starten', 'Knopfzelle CR2450 liegt bei'],
     ['Braucht die Hue Bridge', 'Einbau in der Schalterdose: Arbeit für eine Elektrofachkraft'], 'Philips Hue Wandschaltermodul', 26),
    ('gardena-water', 'garten', 'GARDENA smart Water Control', 'Bewässerungscomputer für den Wasserhahn', 99.99, 'Preis im Shop des Herstellers', 'Gut', 'Gartenbesitzer mit Rasen und Beeten am Außenhahn',
     ['Bis zu 36 Bewässerungen am Tag, jeweils 1 Minute bis 10 Stunden', 'Zeitpläne passen sich laut Hersteller an Wetterdaten an', 'Die App warnt, wenn Frost angekündigt ist', 'Arbeitet mit Apple Home und Amazon Alexa'],
     ['Die Verbindung ins Internet läuft über das GARDENA smart Gateway', 'Die Bodenfeuchte misst erst der zusätzliche smart Sensor', 'Drei AA-Batterien liegen nicht bei'], 'GARDENA smart Water Control', 28),
    ('echo-dot', 'zentrale', 'Amazon Echo Dot (Version 2022)', 'Kleiner Lautsprecher mit Alexa', 89.99, 'UVP', 'Sehr gut', 'Einsteiger, die per Sprache schalten wollen',
     ['Steuert passende Smarthome-Geräte per Sprache oder mit Routinen', 'Eingebaute Sensoren für Bewegung und Raumtemperatur können Routinen auslösen', 'Taste trennt die Mikrofone elektronisch vom Strom', 'Spielt Musik über WLAN oder Bluetooth'],
     ['Vieles läuft über die Cloud von Amazon', 'Zigbee nennt der Hersteller für dieses Modell nicht'], 'Echo Dot 5. Generation', 30),
    ('bosch-thermo', 'heizung', 'Bosch Smart Home Heizkörper-Thermostat II [+M]', 'Thermostat mit Matter', 84.95, 'Preis im Shop des Herstellers', 'Gut', 'Alle, die Thermostate mit Fensterkontakten und anderen Geräten verknüpfen wollen',
     ['Läuft im System von Bosch oder laut Hersteller in allen Systemen mit Matter', 'Temperatur in Schritten von 0,5&nbsp;Grad, per App oder am Gerät', 'Zeitpläne auf 5 Minuten genau', 'Mehrere Thermostate eines Raums lassen sich zusammenfassen'],
     ['Mit 84,95&nbsp;€ deutlich teurer als die Thermostate von FRITZ! in dieser Liste', 'Der Dienst „Smartes Lüften“ braucht zusätzlich einen Tür- und Fensterkontakt'], 'Bosch Smart Home Heizkörper-Thermostat II', 29),
]

# Preis im Shop des Herstellers am Tag STAND, wenn er unter der UVP liegt (id -> Euro). Nur Werte von den Herstellerseiten.
AKTUELL = {'fritz-gateway': 69.99, 'fritz-energy': 29.99, 'fritz-thermo': 44.99, 'fritz-control': 25.99, 'hue-white': 13.19, 'qrevo-curv': 599, 'saros-10': 899, 'shelly-blu-dw': 14.32, 'echo-dot': 34.99, 'tado-x': 54.98}

QUELLEN = [
    (1, 'Verbraucherzentrale: Smart Home, das intelligente Zuhause (Stand 24.02.2026)', 'https://www.verbraucherzentrale.de/wissen/umwelt-haushalt/wohnen/smart-home-das-intelligente-zuhause-6882', 'verbraucherzentrale.de'),
    (2, 'Bundesamt für Sicherheit in der Informationstechnik: Smarthome sicher einrichten', 'https://www.bsi.bund.de/DE/Themen/Verbraucherinnen-und-Verbraucher/Informationen-und-Empfehlungen/Internet-der-Dinge-Smart-leben/Smart-Home/smart-home_node.html', 'bsi.bund.de'),
    (3, 'Nabu Casa: Home Assistant Green (englisch)', 'https://www.home-assistant.io/green/', 'home-assistant.io'),
    (4, 'FRITZ!: Smart-Home-Produkte und Preise', 'https://fritz.com/produkte/smart-home/fritzdect-301/', 'fritz.com'),
    (5, 'Apple: HomePod mini', 'https://www.apple.com/de/homepod-mini/', 'apple.com'),
    (6, 'Philips Hue: Starter-Set mit Hue Bridge Pro', 'https://www.philips-hue.com/de-at/p/hue-white-color-ambiance-starter-set-2-farbfahige-e27-smart-lampen-hue-bridge-pro/8721103107619', 'philips-hue.com'),
    (7, 'TP-Link: Tapo L530E', 'https://www.tp-link.com/de/home-networking/smart-bulb/tapo-l530e/', 'tp-link.com'),
    (8, 'TP-Link: Tapo P115', 'https://www.tp-link.com/de/home-networking/smart-plug/tapo-p115/', 'tp-link.com'),
    (9, 'Homematic IP: Heizkörperthermostat Evo', 'https://homematic-ip.com/de/produkt/heizkoerperthermostat-evo', 'homematic-ip.com'),
    (10, 'Nuki: Smart Lock Pro (5. Generation) und Smart Lock Go', 'https://nuki.io/products/smart-lock-pro-5th-gen', 'nuki.io'),
    (11, 'Reolink: Video Doorbell WiFi', 'https://reolink.com/de/product/reolink-video-doorbell-wifi/', 'reolink.com'),
    (12, 'Reolink: Argus 4 Pro', 'https://reolink.com/de/product/argus-4-pro/', 'reolink.com'),
    (13, 'Shelly: 2PM Gen3', 'https://www.shelly.com/de/products/shelly-2pm-gen3', 'shelly.com'),
    (14, 'Stiftung Warentest: Smarte Heizkörperthermostate im Test (09/2023)', 'https://www.test.de/Heizkoerperthermostat-Test-5115581-0/', 'test.de'),
    (15, 'Stiftung Warentest: Saugroboter im Test (06/2026)', 'https://www.test.de/Saugroboter-im-Test-4806685-0/', 'test.de'),
    (16, 'Google Store: Nest Hub (2. Generation)', 'https://store.google.com/de/product/nest_hub_2nd_gen', 'store.google.com'),
    (17, 'Philips Hue: White A60 E27, 1.100 Lumen', 'https://www.philips-hue.com/de-at/p/hue-white-ambiance-a60---e27-smarte-lampe---1100/8719514288232', 'philips-hue.com'),
    (18, 'Shelly: Plug M Gen3', 'https://www.shelly.com/de/products/shelly-plug-m-gen3', 'shelly.com'),
    (19, 'tado°: Smarte Thermostate, Übersicht und Shop (shop.tado.com)', 'https://www.tado.com/de-de', 'tado.com'),
    (20, 'FRITZ!: Smart Control 350', 'https://fritz.com/produkte/smart-home/fritzdect-350/', 'fritz.com'),
    (21, 'Reolink: E1 Pro', 'https://reolink.com/de/product/e1-pro/', 'reolink.com'),
    (22, 'Roborock: Qrevo Curv', 'https://de.roborock.com/products/roborock-qrevo-curv', 'roborock.com'),
    (23, 'Roborock: Saros 10', 'https://de.roborock.com/products/roborock-saros-10', 'roborock.com'),
    (24, 'Homematic IP: Rauchwarnmelder mit Q-Label', 'https://homematic-ip.com/de/produkt/rauchwarnmelder-mit-q-label', 'homematic-ip.com'),
    (25, 'Shelly: BLU Door/Window ZB', 'https://www.shelly.com/de/products/shelly-blu-door-window-zb-white', 'shelly.com'),
    (26, 'Philips Hue: Wandschaltermodul', 'https://www.philips-hue.com/de-de/p/hue-wandschalter-modul/8719514318045', 'philips-hue.com'),
    (27, 'Philips Hue: Dimmschalter', 'https://www.philips-hue.com/de-de/p/hue-dimmschalter--neuestes-modell-/8719514274617', 'philips-hue.com'),
    (28, 'GARDENA: smart Water Control', 'https://www.gardena.com/de/produkte/bewaesserung/bewaesserungssteuerung/smart-water-control/967045101/', 'gardena.com'),
    (29, 'Bosch Smart Home: Heizkörper-Thermostat II [+M]', 'https://www.bosch-smarthome.com/de/de/produkte/heizung/heizkoerper-thermostat/', 'bosch-smarthome.com'),
    (30, 'Amazon: Echo Dot (Version 2022)', 'https://www.amazon.de/dp/B09B8X9RGM', 'amazon.de'),
]

# Systeme: (id, Name, für wen, Stärke, Schwäche, Funk)
SYSTEME = [
    ('alexa', 'Amazon Alexa', 'Einsteiger, Android und iPhone', 'Riesige Auswahl an Geräten, günstige Lautsprecher', 'Vieles läuft über die Cloud', 'WLAN, Matter, je nach Lautsprecher Zigbee und Thread'),
    ('google', 'Google Home', 'Android-Nutzer', 'Gut mit Android und Nest-Geräten verzahnt', 'Vieles läuft über die Cloud', 'WLAN, Matter, je nach Gerät Thread'),
    ('apple', 'Apple Home', 'Haushalte mit iPhone', 'Einfache Bedienung, viel läuft lokal im Heimnetz', 'Braucht eine Steuerzentrale von Apple, kleinere Geräteauswahl', 'WLAN, Matter, Thread'),
    ('fritz', 'FRITZ! Smart Home', 'Haushalte mit FRITZ!Box', 'Kein weiteres Gerät nötig, läuft im Router', 'Vor allem Heizung, Steckdosen und Sensoren', 'DECT, mit Gateway auch Zigbee und Matter'),
    ('ha', 'Home Assistant', 'Tüftler und alle, die unabhängig bleiben wollen', 'Verbindet fast alles, läuft lokal und ohne Abo', 'Einrichtung kostet Zeit', 'Alles, je nach Funkstick'),
    ('hmip', 'Homematic IP', 'Wer ein System aus einer Hand will', 'Großes Sortiment für Heizung, Rollläden und Sicherheit, kein Abo', 'Geräte anderer Hersteller nur eingeschränkt', 'Eigener Funk auf 868&nbsp;MHz'),
]

FAQ = [
    ('Was brauche ich für den Einstieg ins Smarthome?', 'Ein WLAN und ein Handy. Für den Anfang reicht eine smarte Lampe oder eine Steckdose mit WLAN, die keine Zentrale braucht. Eine Zentrale lohnt sich, sobald mehrere Geräte zusammenarbeiten sollen.'),
    ('Was kostet ein Smarthome?', 'Eine WLAN-Steckdose oder eine smarte Lampe gibt es schon für kleines Geld. Funkbasierte Einstiegssysteme beginnen laut Verbraucherzentrale bei mehreren hundert Euro, fest verkabelte Systeme kosten mehrere tausend Euro.'),
    ('Geht Smarthome auch in der Mietwohnung?', 'Ja. Funkgesteuerte Geräte eignen sich laut Verbraucherzentrale für Mietwohnungen, weil sie ohne Eingriff in die Bausubstanz auskommen und beim Umzug mitkommen. Lampen, Steckdosen, Thermostate und ein Schloss auf dem vorhandenen Zylinder lassen sich wieder abbauen.'),
    ('Was ist Matter?', 'Matter ist ein gemeinsamer Standard vieler Hersteller. Ein Matter-Gerät lässt sich in Alexa, Google Home, Apple Home und Home Assistant einbinden, egal von welchem Hersteller es stammt. Steht Matter auf der Packung, bist du bei der Wahl des Systems freier.'),
    ('Brauche ich eine Zentrale?', 'Nicht für den Anfang. WLAN-Geräte verbinden sich direkt mit dem Router. Geräte mit Zigbee, Thread oder DECT brauchen eine Zentrale, einen passenden Lautsprecher oder eine FRITZ!Box.'),
    ('Spart ein Smarthome Heizkosten?', 'Etwas. Das automatische Absenken bei Abwesenheit spart laut Verbraucherzentrale je nach bisherigem Verhalten 2 bis 8&nbsp;Prozent der Heizkosten. Wer vorher schon von Hand heruntergedreht hat, spart weniger.'),
    ('Ist ein Smarthome sicher?', 'Mit ein paar Regeln ja: für jedes Gerät ein eigenes Passwort, automatische Updates an, und die Geräte in ein eigenes WLAN oder Gäste-WLAN. Das empfiehlt das Bundesamt für Sicherheit in der Informationstechnik.'),
    ('Funktioniert das Smarthome ohne Internet?', 'Das hängt vom Gerät ab. Viele günstige WLAN-Geräte brauchen die Cloud des Herstellers. Systeme wie Home Assistant führen Zeitpläne und Automationen lokal aus und laufen auch bei einem Ausfall weiter.'),
]


# Am 23.11.2026 ergänzte Modelle: Preise an diesem Tag geprüft
NEU23 = {'tado-x', 'echo-dot', 'fire-tv', 'shelly-blu-dw', 'hue-dimmer', 'hue-modul', 'sonos-ace', 'airpods-pro3'}


def eur(p):
    if p is None:
        return ''
    s = ('%.2f' % p).replace('.', ',')
    if s.endswith(',00'):
        s = s[:-3]
    return s + '&nbsp;€'


def preiszeile(m, akt):
    """Preis einer Karte: UVP, bei niedrigerem Preis im Shop des Herstellers dieser Preis mit durchgestrichener UVP."""
    preis, ph, a = m[4], m[5], akt.get(m[0])
    if not preis:
        return '<p class="sm-p sm-p0">Preis beim Händler ansehen</p>'
    if a and a < preis:
        return '<p class="sm-p"><b>%s</b> beim Hersteller am %s <s>UVP %s</s></p>' % (eur(a), '23.11.' if m[0] in NEU23 else STAND[:6], eur(preis))
    return '<p class="sm-p"><b>%s</b> %s</p>' % (eur(preis), ph + ' laut Hersteller' if ph == 'UVP' else ph)


def tabelle(mods, akt):
    """Vergleich aller Modelle eines Bereichs in einer Tabelle (ab zwei Modellen)."""
    if len(mods) < 2:
        return ''
    z = ''.join('<tr><td><a href="#m-%s">%s</a></td><td>%s</td><td>%s</td><td>%s</td></tr>' % (m[0], m[2], (eur(min(m[4], akt.get(m[0], m[4]))) if m[4] else 'beim Händler'), m[6], m[7]) for m in mods)
    return '<div class="tbl sm-vt"><table><thead><tr><th>Modell</th><th>Preis</th><th>Preis-Leistung</th><th>Für wen</th></tr></thead><tbody>%s</tbody></table></div>' % z


def karte(m, akt=None):
    mid, ber, name, art, preis, ph, pl, wer, pro, con, such, q = m
    preis_h = preiszeile(m, AKTUELL if akt is None else akt)
    return ('<article class="sm-m" id="m-%s"><div class="sm-mk"><h4>%s</h4><span class="sm-pl sm-pl-%s">Preis-Leistung: %s</span></div>'
            '<p class="sm-a">%s</p>%s<p class="sm-w"><b>Für wen:</b> %s</p>'
            '<div class="sm-pc"><div><p class="sm-h pro">Dafür</p><ul>%s</ul></div><div><p class="sm-h con">Dagegen</p><ul>%s</ul></div></div>'
            '<div class="sm-go"><a class="btn" href="%s" rel="sponsored nofollow noopener" target="_blank">Bei Amazon ansehen</a>%s<span class="tag">Anzeige</span><a class="sm-q" href="#quellen">Quelle %d</a></div></article>'
            % (mid, name, 'a' if pl == 'Sehr gut' else 'b', pl.lower() if pl == 'Offen' else pl, art, preis_h, wer,
               ''.join('<li>%s</li>' % x for x in pro), ''.join('<li>%s</li>' % x for x in con), amz(such), tink(mid), q))


# Suchlinks für Bereiche, in denen wir keine oder nur wenige Modelle einzeln beschreiben: (Suchbegriff, Titel, Untertitel)
SUCH = {
    'sensoren': ([('Bewegungsmelder smart Matter', 'Bewegungsmelder', 'Schaltet Licht, wenn jemand den Raum betritt'), ('Wassermelder smart WLAN', 'Wassermelder', 'Für Waschküche, Bad und Keller'),
                  ('Thermometer Hygrometer smart', 'Temperatur und Luftfeuchte', 'Zeigt, wann gelüftet werden sollte')], '🚨', 'Vor dem Kauf prüfen, ob der Funk zu deiner Zentrale passt.'),
    'garten': ([('Bewässerungscomputer smart WLAN', 'Bewässerungscomputer mit WLAN', 'Für den Außenwasserhahn'), ('Bodenfeuchtesensor smart Garten', 'Bodenfeuchte-Sensor', 'Gießt nur, wenn der Boden trocken ist')], '💧',
               'Vor dem Kauf Gewinde des Wasserhahns und Funkreichweite prüfen.'),
}


def bereich(i, b):
    bid, emo, titel, foto, alt, satz, kann, achte, hinweis = b
    mods = [m for m in MODELLE if m[1] == bid]
    extra = ''
    if bid == 'saugroboter':
        extra = ('<div class="sm-roh"><p>Die Modelle wechseln schnell. Eine gute Grundlage ist der Test der Stiftung Warentest, '
                 'geprüft wurden dort unter anderem diese drei:</p><div class="items">%s</div>'
                 % ''.join('<a class="item" href="%s" rel="sponsored nofollow noopener" target="_blank"><span class="ic" aria-hidden="true">🧹</span><div><b>%s</b><span>Von der Stiftung Warentest geprüft (06/2026)</span></div><span class="go">Ansehen →</span></a>' % (amz(n), n)
                           for n in ('Roborock Qrevo Curv', 'Dreame L40 Ultra AE', 'Ecovacs Deebot T50 Pro Omni')) +
                 '<p class="hint">Die Links führen zu einer Suche bei Amazon.<span class="tag">Anzeige</span> Die Ergebnisse stehen im <a href="https://www.test.de/Saugroboter-im-Test-4806685-0/" target="_blank" rel="noopener">Test bei test.de</a>.</p></div>')
    if bid == 'rollladen':
        extra = ('<div class="sm-roh"><div class="items"><a class="item" href="%s" rel="sponsored nofollow noopener" target="_blank"><span class="ic" aria-hidden="true">🪟</span><div><b>Elektrischer Gurtwickler mit Funk</b><span>Für Rollläden mit Gurt, zum Selbsttauschen</span></div><span class="go">Ansehen →</span></a></div>'
                 '<p class="hint">Der Link führt zu einer Suche bei Amazon.<span class="tag">Anzeige</span> Vor dem Kauf Gurtbreite und Lochabstand des alten Wicklers messen.</p></div>' % amz('elektrischer Gurtwickler smart Funk'))
    if bid in SUCH:
        liste, emoji, tipp = SUCH[bid]
        extra = ('<div class="sm-roh"><p>Weitere Geräte für diesen Bereich:</p><div class="items">%s</div><p class="hint">Die Links führen zu einer Suche bei Amazon.<span class="tag">Anzeige</span> %s</p></div>'
                 % (''.join('<a class="item" href="%s" rel="sponsored nofollow noopener" target="_blank"><span class="ic" aria-hidden="true">%s</span><div><b>%s</b><span>%s</span></div><span class="go">Ansehen →</span></a>' % (amz(q), emoji, t, u) for q, t, u in liste), tipp))
    return ('<section%s id="%s"><div class="wrap">\n'
            '<div class="sm-b"><div class="sm-bt"><span class="eyebrow">%s Bereich %d von %d</span><h2>%s</h2><p class="lede">%s</p>'
            '<div class="sm-2"><div><h3>Was es kann</h3><ul class="sm-l">%s</ul></div><div><h3>Worauf du achtest</h3><ul class="sm-l">%s</ul></div></div>%s</div>'
            '<figure class="sm-f">%s</figure></div>\n%s%s\n</div></section>\n'
            % (' class="band"' if i % 2 else '', bid, emo, i + 1, len(BEREICHE), titel + '.', satz,
               ''.join('<li>%s</li>' % x for x in kann), ''.join('<li>%s</li>' % x for x in achte),
               (('<p class="sm-n">%s</p>' % hinweis) if hinweis else '') + '<p style="margin:20px 0 0"><a class="btn sec" href="/smarthome/%s.html">Schritt für Schritt: %s</a></p>' % (bid, titel), pic(foto, alt),
               ('<h3 class="sm-mh">Modelle im Vergleich</h3>%s<div class="sm-mg">%s</div>' % (tabelle(mods, AKTUELL), ''.join(karte(m) for m in mods))) if mods else '', extra))


HAUS = '''<figure class="sm-haus"><svg viewBox="0 0 720 420" role="group" aria-label="Haus im Schnitt mit elf nummerierten Punkten für die Bereiche des Smarthomes">
<g fill="none" stroke="currentColor" stroke-opacity=".5" stroke-width="2" stroke-linejoin="round" stroke-linecap="round">
<path d="M60 190 360 40l300 150"/><path d="M100 172v208h520V172"/><path d="M100 262h520M360 172v208M30 380h660"/>
<path d="M150 380v-70h50v70"/><rect x="250" y="292" width="60" height="44"/><rect x="430" y="292" width="110" height="52"/><rect x="170" y="198" width="70" height="40"/><rect x="470" y="198" width="80" height="40"/>
<path d="M470 205h80M470 212h80M470 219h80"/><rect x="400" y="350" width="150" height="30" rx="6"/><path d="M130 250v-36M130 214a10 10 0 0 1 20 0"/><rect x="282" y="238" width="60" height="24" rx="3"/><circle cx="590" cy="372" r="8"/>
</g>
<g class="sm-dots" font-weight="700" font-size="15" text-anchor="middle">
<a href="#zentrale"><circle cx="312" cy="226" r="15"/><text x="312" y="231">1</text><title>Zentrale und Sprachassistent</title></a>
<a href="#licht"><circle cx="140" cy="200" r="15"/><text x="140" y="205">2</text><title>Licht</title></a>
<a href="#steckdose"><circle cx="400" cy="330" r="15"/><text x="400" y="335">3</text><title>Steckdosen</title></a>
<a href="#heizung"><circle cx="280" cy="350" r="15"/><text x="280" y="355">4</text><title>Heizung</title></a>
<a href="#tuerschloss"><circle cx="175" cy="345" r="15"/><text x="175" y="350">5</text><title>Türschloss</title></a>
<a href="#kamera"><circle cx="72" cy="320" r="15"/><text x="72" y="325">6</text><title>Klingel und Kamera</title></a>
<a href="#rollladen"><circle cx="510" cy="190" r="15"/><text x="510" y="195">7</text><title>Rollläden</title></a>
<a href="#saugroboter"><circle cx="590" cy="346" r="15"/><text x="590" y="351">8</text><title>Saugroboter</title></a>
<a href="#sensoren"><circle cx="405" cy="200" r="15"/><text x="405" y="205">9</text><title>Sensoren und Rauchmelder</title></a>
<a href="#schalter"><circle cx="124" cy="292" r="15"/><text x="124" y="297" font-size="13">10</text><title>Lichtschalter</title></a>
<a href="#garten"><circle cx="668" cy="356" r="15"/><text x="668" y="361" font-size="13">11</text><title>Bewässerung</title></a>
</g></svg><figcaption>Tippe auf eine Zahl, um zum Bereich zu springen.</figcaption></figure>'''

FUNK = '''<div class="sm-funk" tabindex="0" role="region" aria-label="Funk-Schema, auf schmalen Bildschirmen seitlich verschiebbar"><svg viewBox="0 0 720 300" role="img" aria-label="Schema: Der Router verbindet WLAN-Geräte direkt. Geräte mit Zigbee, Thread oder DECT laufen über eine Zentrale.">
<g fill="none" stroke="currentColor" stroke-opacity=".45" stroke-width="2" stroke-linecap="round">
<path d="M150 150h110"/><path d="M360 110c60-50 150-60 220-60" stroke-dasharray="2 7"/><path d="M360 150h110"/><path d="M570 150c40 0 50-40 90-40M570 150h90M570 150c40 0 50 40 90 40" stroke-dasharray="7 6"/>
</g>
<g class="sm-box"><rect x="40" y="115" width="110" height="70" rx="14"/><rect x="260" y="115" width="100" height="70" rx="14"/><rect x="470" y="115" width="100" height="70" rx="14"/></g>
<g fill="currentColor" font-size="15" font-weight="700" text-anchor="middle"><text x="95" y="146">Internet</text><text x="310" y="155">Router</text><text x="520" y="155">Zentrale</text></g>
<g fill="currentColor" font-size="13" text-anchor="middle" opacity=".8"><text x="95" y="166">und Cloud</text></g>
<g fill="currentColor" font-size="13.5" font-weight="600"><text x="590" y="44">WLAN-Geräte</text><text x="590" y="62" font-weight="400" opacity=".75">direkt am Router</text>
<text x="666" y="114">Zigbee</text><text x="666" y="155">Thread</text><text x="666" y="195">DECT</text></g>
<g fill="currentColor" font-size="13" opacity=".75"><text x="40" y="250">Gepunktet: WLAN, hohe Reichweite, mehr Stromverbrauch.</text><text x="40" y="272">Gestrichelt: Sparfunk für Sensoren und Thermostate mit Batterie.</text></g>
</svg></div>'''

CSS = '''/* Smarthome-Ratgeber: Stile dieser Seite (werkzeuge/smarthome.py) */
/* Kurzer KI-Film über dem Titelfoto (assets/<name>.mp4/.webm, 10 s, ohne Ton, läuft vor und zurück). Das Foto darunter trägt die KI-Marke. */
.hero-film{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;filter:brightness(.9);opacity:0;transition:opacity 1.2s}.hero-film.an{opacity:1}
.hero-stop{position:absolute;right:max(14px,env(safe-area-inset-right,0px));bottom:34px;z-index:3;display:none;align-items:center;gap:8px;min-height:44px;padding:0 14px;border-radius:999px;background:rgba(0,0,0,.5);color:#fff;font-size:.84rem;font-weight:600;-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px)}.hero-stop.da{display:inline-flex}
@media(prefers-reduced-motion:reduce){.hero-film,.hero-stop{display:none!important}}
.sm-st{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;counter-reset:s}
.sm-st li{list-style:none;background:var(--pan);border:1px solid color-mix(in srgb,var(--line) 60%,transparent);border-radius:22px;padding:22px 20px;counter-increment:s}
.sm-st li:before{content:counter(s);display:grid;place-items:center;width:34px;height:34px;border-radius:50%;background:var(--sun);color:#000;font-weight:700;margin-bottom:12px}
.sm-st h3{margin-bottom:6px}.sm-st p{margin:0;color:var(--mut);font-size:.96rem}
.sm-haus,.sm-funk{margin:clamp(24px,4vw,40px) 0 0;background:var(--pan);border:1px solid color-mix(in srgb,var(--line) 60%,transparent);border-radius:24px;padding:clamp(14px,3vw,28px)}
.band .sm-haus,.band .sm-funk{background:var(--soft);border-color:transparent}
.sm-haus svg,.sm-funk svg{display:block;width:100%;height:auto;color:var(--ink);font-family:inherit}
.sm-haus figcaption{text-align:center;color:var(--mut);font-size:.88rem;margin-top:8px}
.sm-dots circle{fill:var(--sun);stroke:var(--pan);stroke-width:3}.sm-dots text{fill:#000;pointer-events:none}.sm-dots a:hover circle,.sm-dots a:focus circle{fill:var(--ink)}.sm-dots a:hover text,.sm-dots a:focus text{fill:var(--bg)}
.sm-box rect{fill:var(--soft);stroke:currentColor;stroke-opacity:.35;stroke-width:1.5}.band .sm-box rect{fill:var(--pan)}
.sm-nav{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:22px;padding:0}
.sm-nav li{list-style:none}.sm-nav a{display:flex;gap:10px;align-items:center;min-height:56px;padding:10px 14px;border-radius:16px;background:var(--pan);border:1px solid color-mix(in srgb,var(--line) 60%,transparent);color:var(--ink);font-weight:600;font-size:.95rem}
.sm-nav a:hover{text-decoration:none;border-color:var(--sun)}.sm-nav b{display:grid;place-items:center;flex:none;width:26px;height:26px;border-radius:50%;background:var(--sun);color:#000;font-size:.82rem}
.sm-sy{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.sm-sy article{background:var(--soft);border-radius:20px;padding:20px}.sm-sy h3{margin-bottom:4px}.sm-sy .w{color:var(--mut);font-size:.9rem;margin-bottom:12px}
.sm-sy dl{margin:0;display:grid;gap:8px;font-size:.92rem}.sm-sy dt{font-weight:700;font-size:.74rem;letter-spacing:.08em;text-transform:uppercase;color:var(--mut)}.sm-sy dd{margin:0}
.sm-fd{display:grid;grid-template-columns:1fr 1fr;gap:clamp(18px,3vw,36px);align-items:start}
.sm-fd fieldset{border:0;padding:0;margin:0 0 18px}.sm-fd legend{font-weight:700;margin-bottom:8px;padding:0}
.sm-ch{display:flex;flex-wrap:wrap;gap:8px}.sm-ch label{position:relative;cursor:pointer}
.sm-ch input{position:absolute;opacity:0;inset:0}.sm-ch span{display:block;padding:10px 16px;min-height:44px;border-radius:999px;background:var(--soft);font-weight:600;font-size:.94rem;border:2px solid transparent}
.band .sm-ch span{background:var(--bg)}.sm-ch input:checked+span{background:var(--ink);color:var(--bg)}.sm-ch input:focus-visible+span{border-color:var(--sky)}
.sm-res{background:var(--bg);border-radius:24px;padding:clamp(20px,3vw,30px);border:1px solid color-mix(in srgb,var(--line) 60%,transparent);position:sticky;top:84px}
.sm-res .eyebrow{color:var(--mut)}.sm-res h3{font-size:1.6rem;margin:6px 0 10px}.sm-res p{color:var(--mut)}
.sm-res ul{list-style:none;padding:0;margin:14px 0 0;display:grid;gap:8px}.sm-res li a{display:flex;justify-content:space-between;gap:12px;align-items:center;min-height:48px;padding:10px 14px;border-radius:14px;background:var(--pan);color:var(--ink);font-weight:600}
.sm-res li a span{color:var(--mut);font-weight:500;font-size:.86rem;white-space:nowrap}
.sm-b{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:clamp(20px,4vw,48px);align-items:start}
.sm-bt h2{margin:10px 0 12px}.sm-2{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:24px}.sm-2 h3{font-size:1rem;margin-bottom:8px}
.sm-l{margin:0;padding:0;list-style:none;display:grid;gap:8px;font-size:.95rem;color:var(--mut)}.sm-l li{padding-left:18px;position:relative}.sm-l li:before{content:"";position:absolute;left:0;top:.62em;width:7px;height:7px;border-radius:50%;background:var(--sun)}
.sm-n{margin:22px 0 0;padding:14px 16px;border-left:3px solid var(--sun);background:color-mix(in srgb,var(--sun) 9%,transparent);border-radius:0 12px 12px 0;font-size:.94rem}
/* Foto: bewusst NICHT sticky und ohne top. site.js setzt für die KI-Marke position:relative, ein top-Wert schob das Foto dann über die Überschrift (Meldung des Inhabers 23.11.2026). */
.sm-f{margin:0;position:relative;border-radius:24px;overflow:hidden}.sm-f img{display:block;width:100%;height:auto;aspect-ratio:4/3;object-fit:cover}
.sm-mh{margin:clamp(30px,5vw,48px) 0 16px;font-size:1.3rem}
.sm-mg{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}
.sm-m{display:flex;flex-direction:column;gap:10px;background:var(--pan);border:1px solid color-mix(in srgb,var(--line) 60%,transparent);border-radius:22px;padding:22px 20px}
.band .sm-m{background:var(--bg)}
.sm-mk{display:flex;flex-wrap:wrap;justify-content:space-between;gap:8px 12px;align-items:flex-start}.sm-m h4{margin:0;font-size:1.18rem;letter-spacing:-.015em;line-height:1.2}
.sm-pl{flex:none;font-size:.76rem;font-weight:700;padding:5px 10px;border-radius:999px;border:1.5px solid var(--line);white-space:nowrap}.sm-pl-a{background:var(--ok);border-color:var(--ok);color:var(--bg)}
.sm-a{margin:0;color:var(--mut);font-size:.92rem}.sm-p{margin:0}.sm-p b{font-size:1.5rem;letter-spacing:-.02em;margin-right:4px}.sm-p0{color:var(--mut);font-size:.92rem}.sm-p s{color:var(--mut);margin-left:6px;white-space:nowrap}
.sm-vt{margin-bottom:16px}.sm-vt td:first-child{font-weight:600;white-space:normal}.sm-vt td{white-space:normal}.sm-vt a{color:var(--ink);text-decoration:underline}
.sm-w{margin:0;font-size:.93rem}.sm-pc{display:grid;grid-template-columns:1fr 1fr;gap:14px;border-top:1px solid var(--line);padding-top:12px}
.sm-h{margin:0 0 6px;font-size:.74rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase}.sm-h.pro{color:var(--ok)}.sm-h.con{color:var(--warn)}
.sm-pc ul{margin:0;padding-left:16px;font-size:.9rem;color:var(--mut);display:grid;gap:5px}
.sm-go .sm-tk{background:transparent;color:var(--ink);box-shadow:inset 0 0 0 1.5px currentColor}.sm-go{margin-top:auto;padding-top:8px;display:flex;flex-wrap:wrap;gap:8px;align-items:center}.sm-q{margin-left:auto;font-size:.84rem;color:var(--mut);text-decoration:underline}
.sm-roh{margin-top:26px}.sm-roh>p{max-width:70ch;color:var(--mut)}
.sm-pk{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.sm-pk article{background:var(--pan);border-radius:22px;padding:22px 20px;border:1px solid color-mix(in srgb,var(--line) 60%,transparent)}.sm-pk .k{color:var(--mut);font-weight:700;font-size:.84rem}
.sm-pk h3{margin:4px 0 10px;font-size:1.3rem}.sm-pk ul{margin:0;padding:0;list-style:none;display:grid;gap:6px}.sm-pk li a{display:block;padding:9px 12px;border-radius:12px;background:var(--soft);color:var(--ink);font-weight:600;font-size:.93rem}.sm-pk p{color:var(--mut);font-size:.9rem;margin:12px 0 0}
.sm-si{display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:0;margin:0}.sm-si li{list-style:none;background:var(--soft);border-radius:16px;padding:14px 16px;font-size:.95rem}.sm-si b{display:block;margin-bottom:2px}
@media(max-width:1000px){.sm-nav{grid-template-columns:1fr 1fr}.sm-sy{grid-template-columns:1fr 1fr}}
@media(max-width:900px){.sm-st,.sm-pk,.sm-fd,.sm-b{grid-template-columns:1fr}.sm-res{position:static}.sm-f{order:-1}.sm-f img{aspect-ratio:16/9}}
@media(max-width:640px){.sm-sy,.sm-2,.sm-pc,.sm-si{grid-template-columns:1fr}.sm-mg{grid-template-columns:1fr}.sm-haus svg text{font-size:17px}.sm-funk svg{min-width:560px}.sm-funk{overflow-x:auto}}
'''

FILM = '''<script>
/* Titelfilm: startet erst nach dem Laden, nicht bei „Bewegung reduzieren“ oder Datensparmodus; Knopf zum Anhalten. Speichert nichts. */
(function(){var v=document.querySelector('.hero-film'),k=document.querySelector('.hero-stop');if(!v||!k)return;
if(matchMedia('(prefers-reduced-motion:reduce)').matches||(navigator.connection&&navigator.connection.saveData))return;
function los(){var b=v.getAttribute('data-film');v.innerHTML='<source src="'+b+'.webm" type="video/webm"><source src="'+b+'.mp4" type="video/mp4">';v.load();
 v.addEventListener('playing',function(){v.classList.add('an');k.classList.add('da')},{once:true});var p=v.play();if(p&&p.catch)p.catch(function(){})}
k.addEventListener('click',function(){if(v.paused){v.play();k.textContent='Film anhalten';k.setAttribute('aria-pressed','false')}else{v.pause();k.textContent='Film abspielen';k.setAttribute('aria-pressed','true')}});
if(document.readyState==='complete')setTimeout(los,400);else addEventListener('load',function(){setTimeout(los,400)})})();
</script>
'''

SCRIPT = '''<script>
/* Smarthome-Finder: wählt aus fünf Antworten ein System und drei Geräte für den Anfang. Rechnet nur im Browser, speichert nichts. */
(function(){var f=document.getElementById('sm-form');if(!f)return;var out=document.getElementById('sm-out');
var S={apple:['Apple Home','Mit dem iPhone ist Apple Home der kürzeste Weg. Achte beim Kauf auf „Matter“ oder „Apple Home“ auf der Packung.','homepod-mini'],
alexa:['Alexa oder Google Home','Beide funktionieren mit Android und iPhone und haben die größte Auswahl an Geräten. Nimm das System, von dem du schon einen Lautsprecher hast.',''],
fritz:['FRITZ! Smart Home','Deine FRITZ!Box ist schon die Zentrale. Thermostate und Steckdosen meldest du direkt am Router an.','fritz-gateway'],
ha:['Home Assistant','Du willst alles verbinden und unabhängig bleiben. Home Assistant läuft lokal, braucht aber Zeit zum Einrichten.','ha-green']};
var G={licht:['tapo-l530e','hue-start'],heizung:['fritz-thermo','hmip-evo'],sicher:['nuki-go','reolink-klingel'],alles:['tapo-p115','tapo-l530e','hmip-evo']};
var N=__NAMEN__;
function v(n){var e=f.querySelector('input[name="'+n+'"]:checked');return e?e.value:''}
function los(){var sys=v('lust')==='ja'?'ha':v('router')==='ja'&&(v('ziel')==='heizung'||v('ziel')==='alles')?'fritz':v('handy')==='iphone'?'apple':'alexa';
 var L=G[v('ziel')].slice();if(sys==='fritz'){L=L.map(function(x){return x==='hmip-evo'?'fritz-thermo':x==='tapo-p115'?'fritz-energy':x})}
 if(v('wohnen')==='miete'){L=L.filter(function(x){return x!=='reolink-klingel'});if(v('ziel')==='sicher')L.push('reolink-argus')}
 if(S[sys][2]&&L.indexOf(S[sys][2])<0)L.unshift(S[sys][2]);
 var seen={};L=L.filter(function(x){if(seen[x])return false;seen[x]=1;return true}).slice(0,3);
 out.innerHTML='<span class="eyebrow">Dein Einstieg</span><h3>'+S[sys][0]+'</h3><p>'+S[sys][1]+'</p><ul>'+L.map(function(x){return '<li><a href="#m-'+x+'">'+N[x][0]+'<span>'+N[x][1]+'</span></a></li>'}).join('')+'</ul>'+(v('wohnen')==='miete'?'<p style="margin-top:14px;font-size:.9rem">Alles davon lässt sich beim Auszug wieder abbauen.</p>':'')}
f.addEventListener('change',los);los()})();
</script>
'''


def main():
    v = (ROOT / 'infrarotheizung.html').read_text(encoding='utf-8')
    kopf, fuss = v[:v.index('<main id="main">')], v[v.index('</main>'):]
    fuss = re.sub(r'<script>\n/\* Infrarotheizung-Kosten-Rechner.*?</script>\n?', '', fuss, count=1, flags=re.S)
    assert 'Kosten-Rechner' not in fuss, 'Vorlage: Fuß enthält noch das Rechner-Skript der Vorlage'
    title = 'Smarthome für Einsteiger: Systeme, Geräte, Modelle – Strom-Daheim'
    desc = 'Smarthome einrichten: welches System zu dir passt, was es für Licht, Heizung, Tür und Kamera gibt, und konkrete Modelle mit Preis, Dafür und Dagegen.'
    ogd = 'Wie fange ich mit Smarthome an? Systeme im Vergleich, ein Finder für deinen Einstieg und konkrete Modelle für Licht, Heizung, Steckdosen, Türschloss, Kamera und Rollläden.'
    kopf = re.sub(r'<title>.*?</title>', '<title>%s</title>' % title, kopf, count=1)
    for prop, val in (('og:title', title), ('og:description', ogd), ('og:url', 'https://strom-daheim.de/smarthome.html'), ('og:image', 'https://strom-daheim.de/assets/og/smarthome.jpg')):
        kopf, n = re.subn(r'<meta property="%s" content="[^"]*">' % prop, '<meta property="%s" content="%s">' % (prop, val), kopf, count=1)
        assert n == 1, prop
    kopf, n = re.subn(r'<meta name="description" content="[^"]*">', '<meta name="description" content="%s">' % desc, kopf, count=1)
    assert n == 1
    kopf = kopf.replace('https://strom-daheim.de/infrarotheizung.html', 'https://strom-daheim.de/smarthome.html')
    kopf = re.sub(r'<script type="application/ld\+json" id="ld">.*?</script>\n?', '', kopf, flags=re.S)
    kopf = re.sub(r'<meta name="checked" content="[^"]*">', '', kopf)
    assert 'canonical" href="https://strom-daheim.de/smarthome.html' in kopf, 'Vorlage: kanonische Adresse nicht ersetzt'
    kopf = kopf.replace('</style>', CSS + '</style>', 1)

    nav = ''.join('<li><a href="#%s"><b>%d</b>%s</a></li>' % (b[0], i + 1, b[2]) for i, b in enumerate(BEREICHE))
    sys_h = ''.join('<article><h3>%s</h3><p class="w">%s</p><dl><div><dt>Stärke</dt><dd>%s</dd></div><div><dt>Schwäche</dt><dd>%s</dd></div><div><dt>Funk</dt><dd>%s</dd></div></dl></article>' % s[1:] for s in SYSTEME)
    namen = '{%s}' % ','.join("'%s':['%s','%s']" % (m[0], m[2].replace("'", ''), (eur(min(m[4], AKTUELL.get(m[0], m[4]))).replace('&nbsp;', ' ') if m[4] else 'Preis beim Händler')) for m in MODELLE)

    def frage(name, leg, opts):
        return '<fieldset><legend>%s</legend><div class="sm-ch">%s</div></fieldset>' % (leg, ''.join('<label><input type="radio" name="%s" value="%s"%s><span>%s</span></label>' % (name, val, ' checked' if k == 0 else '', t) for k, (val, t) in enumerate(opts)))

    def pk(k, titel, ids, text):
        return '<article><span class="k">%s</span><h3>%s</h3><ul>%s</ul><p>%s</p></article>' % (k, titel, ''.join('<li><a href="#m-%s">%s</a></li>' % (i, next(m[2] for m in MODELLE if m[0] == i)) for i in ids), text)

    m = '''<main id="main">
<div class="hero">
  <picture><source type="image/webp" srcset="assets/smarthome-m.webp 800w, assets/smarthome.webp 1280w" sizes="100vw"><img src="assets/smarthome.jpg" srcset="assets/smarthome-m.jpg 800w, assets/smarthome.jpg 1280w" sizes="100vw" alt="Wohnzimmer in der Dämmerung mit warmem Lichtband hinter dem Sideboard, kleinem Lautsprecher und Wandbedienfeld" width="1280" height="720" fetchpriority="high" decoding="async" style="object-position:70%% 50%%"></picture>
  <video class="hero-film" muted loop playsinline preload="none" aria-hidden="true" tabindex="-1" data-film="assets/smarthome" style="object-position:70%% 50%%"></video>
  <button class="hero-stop" type="button" aria-pressed="false">Film anhalten</button>
  <div class="wrap">
    <span class="eyebrow">Ratgeber · Stand %(stand_lang)s</span>
    <h1>Smarthome: So fängst du an.</h1>
    <p>Welches System zu dir passt, was es für Licht, Heizung, Tür und Kamera gibt und welche Geräte ihr Geld wert sind. Für Miete und Eigentum.</p>
    <div class="jump"><a class="pri" href="#finder">Was passt zu mir?</a><a href="#bereiche">Alle Bereiche</a><a href="#systeme">Systeme vergleichen</a><a href="#pakete">Startpakete</a><a href="/multimedia.html">Multimedia</a></div>
  </div>
</div>

<section id="start"><div class="wrap">
<div class="head"><span class="eyebrow">Der Einstieg</span><h2>In drei Schritten zum ersten Gerät.</h2><p class="lede">Du brauchst kein fertiges Konzept. Fang mit einem Gerät an und bau aus, was sich bewährt.</p></div>
<ol class="sm-st" style="padding:0;margin:0">
<li><h3>Ziel festlegen</h3><p>Was nervt dich am meisten? Kalte Wohnung am Morgen, Licht vergessen, Paket verpasst. Dort fängst du an.</p></li>
<li><h3>System wählen</h3><p>Dein Handy und dein Router entscheiden fast schon. Der <a href="#finder">Finder</a> nimmt dir die Wahl in fünf Fragen ab.</p></li>
<li><h3>Klein anfangen</h3><p>Eine Lampe oder eine Steckdose mit WLAN läuft in zehn Minuten. Achte bei jedem Kauf auf „Matter“, dann bleibst du flexibel.</p></li>
</ol>
</div></section>

<section class="band" id="bereiche"><div class="wrap">
<div class="head"><span class="eyebrow">Überblick</span><h2>Was im Haus smart werden kann.</h2><p class="lede">Elf Bereiche, vom Lichtschalter bis zur Haustür. Zu jedem steht unten, was es kann, worauf du achtest und welche Modelle wir empfehlen.</p></div>
%(haus)s
<ol class="sm-nav">%(nav)s</ol>
</div></section>

<section id="systeme"><div class="wrap">
<div class="head"><span class="eyebrow">Systeme</span><h2>Welches System passt zu dir?</h2><p class="lede">Das System ist die App, in der alles zusammenläuft. Du kannst später wechseln, einfacher ist es, gleich passend zu kaufen.</p></div>
<div class="sm-sy">%(sys)s</div>
<h3 style="margin-top:clamp(32px,5vw,52px)">Funk kurz erklärt.</h3>
%(funk)s
<div class="tbl" style="margin-top:16px"><table><thead><tr><th>Funk</th><th>Braucht eine Zentrale</th><th>Typisch für</th></tr></thead><tbody>
<tr><td>WLAN</td><td>Nein</td><td>Steckdosen, Lampen, Kameras</td></tr>
<tr><td>Zigbee</td><td>Ja</td><td>Lampen, Sensoren, Schalter</td></tr>
<tr><td>Thread</td><td>Ja, einen Thread-Router</td><td>Neue Sensoren, Schlösser, Thermostate</td></tr>
<tr><td>DECT</td><td>Ja, die FRITZ!Box</td><td>Thermostate und Steckdosen von FRITZ!</td></tr>
<tr><td>Matter</td><td>Kein Funk, sondern eine gemeinsame Sprache</td><td>Macht Geräte in mehreren Systemen nutzbar</td></tr>
</tbody></table></div>
<p class="hint">Offene Systeme mit verbreiteten Standards erlauben laut Verbraucherzentrale, Produkte verschiedener Hersteller zu kombinieren. Geschlossene Systeme sind nicht herstellerübergreifend kompatibel.</p>
</div></section>

<section class="band" id="finder"><div class="wrap">
<div class="head"><span class="eyebrow">Finder</span><h2>Was passt zu mir?</h2><p class="lede">Fünf Fragen, ein Vorschlag: dein System und die ersten Geräte.</p></div>
<div class="sm-fd"><form id="sm-form" onsubmit="return false">
%(f1)s%(f2)s%(f3)s%(f4)s%(f5)s
</form><div class="sm-res" id="sm-out" aria-live="polite"></div></div>
<p class="hint" style="margin-top:16px">Der Vorschlag folgt festen Regeln: Wer tüfteln mag, bekommt Home Assistant. Mit FRITZ!Box und dem Ziel Heizung FRITZ!. Mit iPhone Apple Home, sonst Alexa oder Google Home.</p>
</div></section>

%(bereiche)s
<section id="pakete"><div class="wrap">
<div class="head"><span class="eyebrow">Startpakete</span><h2>Drei Wege für den Anfang.</h2><p class="lede">Fertig zusammengestellt aus den Modellen oben. Tippe auf ein Gerät für Preis, Dafür und Dagegen.</p></div>
<div class="sm-pk">%(pakete)s</div>
<div class="cta" style="margin-top:26px"><a class="btn sec" href="/multimedia.html">Fernseher, Soundbar und Streaming: zum Multimedia-Ratgeber</a></div>
</div></section>

<section class="band" id="sicherheit"><div class="wrap read">
<div class="head"><span class="eyebrow">Sicherheit</span><h2>Sechs Regeln, bevor du loslegst.</h2><p class="lede">Die Empfehlungen stammen vom Bundesamt für Sicherheit in der Informationstechnik.</p></div>
<ul class="sm-si">
<li><b>Updates</b>Vor dem Kauf prüfen, wie lange der Hersteller Updates liefert. Automatische Updates einschalten.</li>
<li><b>Passwörter</b>Für jedes Gerät ein eigenes Passwort, für das WLAN mindestens 20 Zeichen.</li>
<li><b>Eigenes WLAN</b>Smarte Geräte in ein getrenntes WLAN oder das Gäste-WLAN hängen.</li>
<li><b>Router</b>Voreingestelltes Passwort ändern, Firmware aktuell halten, UPnP ausschalten.</li>
<li><b>Lokal statt Cloud</b>Nur mit dem Internet verbinden, was den Zugriff von unterwegs wirklich braucht.</li>
<li><b>Daten</b>Vorher klären, welche Sensoren ein Gerät hat, was es speichert und wohin.</li>
</ul>
<h3 style="margin-top:36px">Zur Miete und zu den Kosten.</h3>
<p style="margin-top:10px">Funkgesteuerte Geräte eignen sich laut Verbraucherzentrale für Mietwohnungen: Sie kommen ohne Eingriff in die Bausubstanz aus, lassen sich wieder abbauen und ziehen mit um. Funkbasierte Einstiegssysteme beginnen laut Verbraucherzentrale bei mehreren hundert Euro, fest verkabelte Systeme kosten mehrere tausend Euro. Für Thermostate und Energiemanagement nennt sie eine Förderung über die BEG von bis zu 20&nbsp;Prozent der Kosten.</p>
</div></section>

<section id="fragen"><div class="wrap read">
<div class="head"><span class="eyebrow">Häufige Fragen</span><h2>Kurz beantwortet.</h2></div>
%(faq)s
</div></section>

<section class="band" id="quellen"><div class="wrap read">
<div class="cta"><a class="btn" href="#finder">Zum Finder</a><a class="btn sec" href="/stromfresser.html">Stromfresser finden</a></div>
<p class="hint" style="margin-top:18px">Wie viel Strom deine Geräte brauchen, steht unter <a href="/stromkosten.html">Stromkosten je Gerät</a>. Was smarte Thermostate mit dem Lüften zu tun haben, unter <a href="/lueften.html">Richtig lüften</a>.</p>
<div class="src" style="margin-top:32px"><b>Quellen</b><ol>
%(quellen)s
</ol><p style="margin-top:12px">Geprüft am %(stand)s. Preise sind unverbindliche Preisempfehlungen der Hersteller oder, wo angegeben, der Preis im Shop des Herstellers an diesem Tag. Der Preis im Handel weicht oft ab. „Preis-Leistung“ ist unsere Einschätzung aus Preis und Ausstattung. Wir haben kein Gerät selbst getestet.</p></div>
</div></section>
''' % dict(stand=STAND, stand_lang=STAND_LANG, haus=HAUS, nav=nav, sys=sys_h, funk=FUNK,
           f1=frage('handy', 'Welches Handy nutzt du?', [('android', 'Android'), ('iphone', 'iPhone')]),
           f2=frage('wohnen', 'Wie wohnst du?', [('miete', 'Zur Miete'), ('eigentum', 'Im Eigentum')]),
           f3=frage('router', 'Hast du eine FRITZ!Box?', [('nein', 'Nein oder weiß nicht'), ('ja', 'Ja')]),
           f4=frage('ziel', 'Womit willst du anfangen?', [('licht', 'Licht'), ('heizung', 'Heizung'), ('sicher', 'Tür und Sicherheit'), ('alles', 'Von allem etwas')]),
           f5=frage('lust', 'Magst du tüfteln?', [('nein', 'Soll einfach laufen'), ('ja', 'Ja, gern')]),
           bereiche=''.join(bereich(i, b) for i, b in enumerate(BEREICHE)),
           pakete=pk('Mietwohnung', 'Der schnelle Einstieg', ['tapo-l530e', 'tapo-p115', 'nuki-go'], 'Nichts davon braucht eine Zentrale oder Werkzeug, alles zieht mit um.')
           + pk('Mit FRITZ!Box', 'Heizung im Griff', ['fritz-thermo', 'fritz-energy', 'fritz-gateway'], 'Der Router ist die Zentrale. Das Gateway brauchst du erst für Zigbee- und Matter-Geräte.')
           + pk('Eigenes Haus', 'Rundum versorgt', ['ha-green', 'shelly-2pm', 'reolink-klingel'], 'Lokal gesteuert und ohne Abo. Unterputz-Module baut eine Elektrofachkraft ein.'),
           faq='\n'.join('<details><summary>%s</summary><div><p>%s</p></div></details>' % x for x in FAQ),
           quellen='\n'.join('<li>%s <a href="%s" target="_blank" rel="noopener">%s</a></li>' % (t, u, d) for _, t, u, d in QUELLEN))
    assert [q[0] for q in QUELLEN] == list(range(1, len(QUELLEN) + 1))
    for mo in MODELLE:
        assert any(b[0] == mo[1] for b in BEREICHE) and 1 <= mo[11] <= len(QUELLEN), mo[0]
    out = kopf + m + SCRIPT.replace('__NAMEN__', namen) + fuss.replace('</main>', '</main>', 1)
    out = out.replace(m + SCRIPT.replace('__NAMEN__', namen) + '</main>', m + '</main>\n' + SCRIPT.replace('__NAMEN__', namen)) if False else kopf + m + '</main>' + fuss[len('</main>'):].replace('<script>\n/* Besucherzähler', FILM + SCRIPT.replace('__NAMEN__', namen) + '<script>\n/* Besucherzähler', 1)
    import site_header
    out = site_header.apply(out, 'smarthome')   # Menü mit dieser Seite als aktueller Seite (25.11.2026: sonst erbt sie aria-current der Vorlage)
    (ROOT / 'smarthome.html').write_text(out, encoding='utf-8')
    print('smarthome.html geschrieben:', len(out), 'Zeichen,', len(MODELLE), 'Modelle')


if __name__ == '__main__':
    main()
