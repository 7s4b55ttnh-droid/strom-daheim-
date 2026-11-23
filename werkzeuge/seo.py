"""Strom-Daheim: strukturierte Daten (JSON-LD), Kasten „Kurz gesagt“, Kopfangaben für Suchmaschinen und llms.txt.
Aufruf im Repository-Ordner: python3 werkzeuge/seo.py
Neue Seite: Eintrag in KURZ ergänzen (zwei Sätze, nur Fakten, die auf der Seite stehen) und das Skript erneut ausführen.

Kopfangaben (seit 14.11.2026): Das Skript ergänzt og:url, kürzt eine zu lange Beschreibung im Suchergebnis auf ganze Sätze
bis 160 Zeichen (og:description behält den vollen Text) und meldet Titel, die ohne „ – Strom-Daheim“ länger als 60 Zeichen sind.
Solche Titel bitte von Hand kürzen: Das wichtigste Suchwort steht vorn. Außerdem: große Bildvorschau für Google erlauben
(robots max-image-preview:large), Tag der ersten Veröffentlichung merken (werkzeuge/erstdatum.json, trägt sich selbst ein),
Angaben zur Website auf der Startseite (WebSite) und Titel und Beschreibung in suche.json nachziehen."""
import re, json, html, pathlib, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = 'https://strom-daheim.de'
NAME = 'Strom-Daheim'
KURZ = {
    'ebike.html': 'Fast jedes „E-Bike“ ist rechtlich ein Pedelec: Der Motor hilft nur beim Treten, mit höchstens 250&nbsp;Watt und bis 25&nbsp;km/h. Dafür brauchst du laut ADAC weder Führerschein noch Kennzeichen. Eine Akkuladung reicht laut ADAC für 50 bis 100&nbsp;Kilometer und kostet bei 500&nbsp;Wattstunden und 35&nbsp;Cent je Kilowattstunde rund 18&nbsp;Cent. Der Akku hält etwa 500 bis 1.000 Ladezyklen, am längsten bei 20 bis 80&nbsp;Prozent Ladestand. 2025 kostete ein E-Bike im Schnitt 2.550&nbsp;€ (Zweirad-Industrie-Verband).',
    'multimedia.html': 'Der günstigste Schritt zu besserem Heimkino ist der Ton: Laut Stiftung Warentest klingen nur wenige Flachbildfernseher sehr gut, eine Soundbar verbessert jedes Gerät. Sie kommt an den HDMI-Anschluss mit eARC oder ARC, ältere Fernseher haben nur einen optischen Ausgang. Die meisten Fernseher mit sehr gutem Bild sind OLED-Geräte und kosten meist mindestens 1.000&nbsp;€, gute Fernseher gibt es schon für unter 400&nbsp;€. Eine Streaming-Box kann zugleich die Zentrale fürs Smarthome sein.',
    'smarthome.html': 'Für den Einstieg ins Smarthome reichen ein WLAN, ein Handy und ein erstes Gerät, etwa eine smarte Lampe oder eine Steckdose mit WLAN, die keine Zentrale braucht. Welches System passt, entscheiden meist Handy und Router: Apple Home für das iPhone, FRITZ! für die FRITZ!Box, sonst Alexa oder Google Home. Wer beim Kauf auf den Standard Matter achtet, bleibt flexibel. Das automatische Absenken der Heizung spart laut Verbraucherzentrale 2 bis 8&nbsp;Prozent der Heizkosten.',
    'heizungspumpe.html': 'Eine alte, ungeregelte Heizungspumpe kann laut Umweltbundesamt über 200&nbsp;kWh Strom im Jahr brauchen, eine Hocheffizienzpumpe rund 40&nbsp;kWh. Der Tausch kostet den Fachbetrieb ein bis zwei Stunden, wird mit 15&nbsp;Prozent bezuschusst und hat sich mit hydraulischem Abgleich nach etwa 3 bis 4 Jahren bezahlt gemacht.',
    'infrarotheizung.html': 'Eine Infrarotheizung macht aus einer Kilowattstunde Strom höchstens eine Kilowattstunde Wärme. Laut ADAC braucht ein Raum im gut gedämmten Neubau 20 bis 40&nbsp;W je m², im sanierten Altbau 60 bis 100&nbsp;W. Als Zusatzheizung für Bad oder Gästezimmer ist sie sinnvoll, als Hauptheizung im Altbau teuer; Förderung gibt es keine. Im Bestand ist sie als neue Heizung seit Juli 2026 nur in deutlich besser gedämmten Häusern erlaubt, mit Ausnahmen.',
    'luftentfeuchter.html': 'Die Luftfeuchte in Wohnräumen sollte laut Umweltbundesamt zwischen 40 und 60&nbsp;Prozent liegen; liegt sie dauerhaft darüber, droht laut Stiftung Warentest Schimmel. Ein Luftentfeuchter mit Kompressor braucht nach Herstellerangaben meist 150 bis 300&nbsp;W und passt in beheizte Räume, ein Adsorptionsgerät arbeitet auch im kalten Keller, braucht je Liter Wasser aber ein Mehrfaches an Strom. Die Ursache der Feuchte behebt keines der Geräte.',
    'balkonkraftwerk-foerderung.html': 'Einen Zuschuss vom Bund gibt es für Balkonkraftwerke nicht. Im November 2026 zahlt Mecklenburg-Vorpommern 500 € an Mieter, Hamburg fördert Haushalte mit geringem Einkommen mit bis zu 500 €. Sachsen und Berlin haben ihre Programme 2026 beendet. Viele Städte fördern selbst, die Töpfe sind aber oft schnell leer. Überall gilt: 0 Prozent Mehrwertsteuer.',
    'balkonkraftwerk-speicher.html': 'Bei zwei Modulen lohnt sich ein Speicher meist nicht: Er braucht in unserer Modellrechnung 6 bis 15 Jahre, bis er sich bezahlt hat. Bei vier Modulen und Verbrauch am Abend sind es 2,5 bis 6 Jahre. Günstiger ist es oft, Spülmaschine und Waschmaschine in die Mittagszeit zu legen.',
    'was-lohnt-sich.html': 'Der Einstieg stellt fünf Fragen zu Wohnform, Platz, E-Auto, Heizung und deinen Zahlen. Daraus entsteht nach festen, nachlesbaren Regeln eine Reihenfolge: zuerst, was du selbst entscheiden kannst und was am meisten Strom betrifft. Postleitzahl, Verbrauch und Strompreis merkt sich dein Browser, damit alle Rechner danach schon ausgefüllt sind.',
    'solar-rechner.html': 'Der Solar-Rechner geht ein typisches Jahr Stunde für Stunde durch und zeigt, wie viel Strom deine Dachanlage liefert, wie viel du davon selbst nutzt und nach wie vielen Jahren sie bezahlt ist. Ohne eigenes Angebot rechnet er mit 1.200&nbsp;€ je kWp und 500&nbsp;€ je kWh Speicher, das liegt in der Spanne von 1.100 bis 1.400&nbsp;€ je kWp und 350 bis 700&nbsp;€ je kWh. Speicher, E-Auto und Wärmepumpe kannst du zuschalten.',
    'solar-atlas.html': 'Der Solar-Atlas zeigt für 95 Regionen in Deutschland, wie viel Strom eine Solaranlage liefert: Ein Süddach bringt je nach Region rund 1.010 bis 1.240&nbsp;kWh je kWp im Jahr, ein Balkonkraftwerk mit 900&nbsp;Wp senkrecht am Südbalkon rund 650 bis 780&nbsp;kWh. Grundlage sind die Sonnendaten von PVGIS aus den Jahren 2005 bis 2023.',
    'strompreis-heute.html': 'Die Seite zeigt den Börsenstrompreis für Deutschland Stunde für Stunde und sucht das günstigste Zeitfenster für Waschmaschine, Spülmaschine oder E-Auto. Wichtig ist das nur mit einem dynamischen Tarif: Auf den Börsenpreis kommen in jeder Stunde Netzentgelt, Steuern und Umlagen.',
    'balkonkraftwerk-planer.html': 'Der Planer rechnet mit den Sonnendaten deiner Region aus, was ein Balkonkraftwerk an deinem Balkon bringt: Zwei Module mit zusammen 900&nbsp;Wp liefern senkrecht an einem Südbalkon je nach Region etwa 650 bis 780&nbsp;kWh im Jahr, schräg aufgestellt 900 bis 1.110&nbsp;kWh. Geld spart nur der Teil, den du selbst nutzt; wie viel das bei deinem Verbrauch ist und ob sich ein Speicher lohnt, zeigt der Vergleich.',
    'anleitung-balkonkraftwerk.html': 'Ein Balkonkraftwerk mit höchstens 960&nbsp;Watt Modulleistung und 800&nbsp;Watt Wechselrichter darf in die normale Haushaltssteckdose, die Montage schaffst du an einem Nachmittag. Danach meldest du es innerhalb eines Monats im Marktstammdatenregister an; zur Miete brauchst du für Brüstung oder Fassade die Zustimmung des Vermieters, die er nicht grundlos verweigern darf.',
    'e-auto.html': 'Zuhause laden kostet etwa 5 bis 8&nbsp;€ pro 100&nbsp;km, an öffentlichen Säulen zahlst du meist deutlich mehr (39 bis 89&nbsp;ct pro kWh). Für regelmäßiges Laden ist eine Wallbox mit 11&nbsp;kW sicherer und schneller als die Haushaltssteckdose.',
    'anleitung-wallbox.html': 'Eine Wallbox kostet mit Einbau im Standardfall etwa 800 bis 2.200&nbsp;€, anschließen darf sie nur ein eingetragener Elektrofachbetrieb. Sie wird beim Netzbetreiber angemeldet, und als steuerbare Verbrauchseinrichtung nach §&nbsp;14a sparst du etwa 110 bis 190&nbsp;€ Netzentgelt im Jahr.',
    'powerstation.html': 'Für Router, Handys und Licht reicht eine kleine Powerstation mit etwa 250&nbsp;Wh, für Kühlschrank und Licht über einen Tag braucht es rund 1.000&nbsp;Wh. Eine Powerstation versorgt nur Geräte, die direkt in ihr stecken, und darf nie über ein Kabel ins Hausnetz einspeisen.',
    'stromtarif.html': 'In der Grundversorgung zahlst du im Schnitt 40,54&nbsp;ct pro kWh, günstige Tarife liegen bei 33,48&nbsp;ct: Bei 2.500&nbsp;kWh sind das rund 177&nbsp;€ im Jahr. Der Wechsel ist kostenlos, technisch in 24 Stunden erledigt, und der Strom fließt ohne Unterbrechung weiter.',
    'stromfresser.html': 'Zwei Personen in einer Wohnung brauchen laut Stromspiegel 2025 im Schnitt 1.900&nbsp;kWh im Jahr; der Vergleich auf dieser Seite zeigt deine Klasse von A bis G. Die größten Stromfresser findest du mit einem Strommessgerät zwischen Steckdose und Gerät, Standby summiert sich dabei oft mehr als gedacht.',
    'waermepumpe.html': 'Im Altbau erreichen Luft-Wasser-Wärmepumpen laut Fraunhofer ISE im Mittel eine Jahresarbeitszahl von 3,4. Ob dein Haus passt, zeigt der 55-Grad-Test. Die KfW fördert seit 21. Juli 2026 mit 30&nbsp;% plus Boni, höchstens 70 bis 80&nbsp;% von 28.000&nbsp;€ Kosten.',
    'pv-anlage.html': 'Eine Photovoltaik-Anlage mit 10&nbsp;kWp kostet 2026 rund 12.000&nbsp;€, mit 10-kWh-Speicher rund 17.000&nbsp;€, und erzeugt etwa 9.000 bis 11.000&nbsp;kWh im Jahr. Lohnend ist vor allem der selbst genutzte Strom, denn die feste Einspeisevergütung für neue kleine Anlagen soll ab 2027 wegfallen; beschlossen ist das noch nicht.',
    'energielabel.html': 'Seit März 2021 gilt für viele Geräte wieder die Skala A bis G, und die beste Klasse A ist bewusst fast leer. Wichtiger als der Buchstabe ist die kWh-Zahl: Ein Kühlschrank von 2002 braucht bis zu 330&nbsp;kWh im Jahr, das beste neue Gerät 90 bis 125&nbsp;kWh.',
    'black-friday.html': 'Black Friday ist am 27. November 2026, Cyber Monday am 30. November. Ein Rabatt soll sich grundsätzlich auf den niedrigsten Preis der letzten 30 Tage beziehen, die UVP sagt wenig. Prüfe den Preisverlauf, lass dich von Countdowns nicht drängen und rechne vorher aus, ob sich ein Gerät wie Powerstation oder Balkonkraftwerk für dich lohnt.',
    'kuehlschrank.html': 'Ein Kühlschrank braucht nur 7&nbsp;°C, ein Gefrierschrank −18&nbsp;°C. Jedes Grad kälter kostet etwa 6&nbsp;Prozent mehr Strom, und schon 5&nbsp;mm Eis bedeuten rund 30&nbsp;Prozent mehr Energie, deshalb ab 1&nbsp;cm Eis abtauen. Ob die Türdichtung schließt, zeigt ein eingeklemmtes Blatt Papier.',
    'waesche-trocknen.html': 'Ein Wärmepumpentrockner braucht laut Umweltbundesamt etwa 0,7 bis 1&nbsp;kWh pro Trocknung, ein alter Trockner ohne Wärmepumpe rund 3,4&nbsp;kWh. Der Wäscheständer kostet keinen Strom, eine Ladung mit 5&nbsp;kg gibt aber bis zu 2&nbsp;Liter Wasser an die Raumluft ab: mehrmals täglich 5 bis 10 Minuten stoßlüften und die Luftfeuchte bei 40 bis 60&nbsp;Prozent halten.',
    'backen.html': 'Ein Backofen braucht bei 200&nbsp;°C laut EnBW etwa 1,5 bis 2&nbsp;kWh pro Stunde, ein Blech Plätzchen kostet also nur wenige Cent. Am meisten sparst du, wenn du nicht vorheizt (laut Verbraucherzentrale bis zu 20&nbsp;Prozent), mit Umluft 20 bis 30&nbsp;°C niedriger und auf zwei oder drei Blechen gleichzeitig backst und die Tür geschlossen lässt.',
    'spuelmaschine.html': 'Eine volle Spülmaschine im Eco-Programm braucht laut Umweltbundesamt rund 10&nbsp;Liter Wasser und weniger als 1&nbsp;kWh, ein sparsames Gerät etwa 0,54&nbsp;kWh, das sind rund 17&nbsp;ct Strom. Laut Universität Bonn brauchen Haushalte mit Maschine im Schnitt 50&nbsp;Prozent weniger Wasser und 28&nbsp;Prozent weniger Energie als beim Spülen von Hand; nicht vorspülen und nur voll starten.',
    'stromsteuer-2027.html': 'Die Stromsteuer soll zum 1.&nbsp;Januar 2027 für alle Verbraucher von 2,05 auf 0,1&nbsp;Cent je Kilowattstunde sinken, das europäische Mindestmaß. Darauf hat sich der Koalitionsausschuss von CDU, CSU und SPD in der Nacht zum 18.&nbsp;November 2026 geeinigt; ein Gesetz gibt es noch nicht. Mit Mehrwertsteuer sind das rund 2,3&nbsp;Cent je Kilowattstunde, bei 2.800&nbsp;kWh im Jahr etwa 65&nbsp;Euro, wenn dein Anbieter die Senkung voll weitergibt. Finanziert ist sie bisher nur für 2027.',
    'strompreise-2027.html': 'Laut Verivox erhöhen 329 Grundversorger ihre Strompreise für Dezember bis Februar, die meisten zum 1.&nbsp;Januar 2027, im Schnitt um etwa 8&nbsp;Prozent (Stand 21.11.2026); bei 4.000&nbsp;kWh sind das rund 128&nbsp;€ mehr im Jahr. Gründe sind vor allem höhere Einkaufspreise und Umlagen, die von 2,95 auf 3,62&nbsp;ct pro kWh steigen. Bei einer Erhöhung zum 1.&nbsp;Januar muss deine Kündigung bis 31.&nbsp;Dezember beim Anbieter sein.',
    'led-lampen.html': 'Gute LED-Lampen brauchen laut Verbraucherzentrale Hamburg rund 90&nbsp;Prozent weniger Strom als eine Glühlampe gleicher Helligkeit. Eine LED mit etwa 700&nbsp;Lumen statt einer Halogenlampe spart laut Verbraucherzentrale in zehn Jahren mehr als 100&nbsp;€, wenn sie rund drei Stunden am Tag brennt. Beim Kauf zählen Lumen, Lichtfarbe in Kelvin und ein Farbwiedergabe-Wert von mindestens 80.',
    'durchlauferhitzer.html': 'Eine Dusche von sechs Minuten mit 10 Litern pro Minute braucht mit Durchlauferhitzer rund 2&nbsp;kWh Strom, bei 32&nbsp;Cent also gut 60&nbsp;Cent. Ein Sparduschkopf unter 9&nbsp;Litern pro Minute kann den Warmwasserverbrauch um bis zu die Hälfte senken, ein elektronisches Gerät statt eines hydraulischen spart laut Verbraucherzentrale bis zu 30&nbsp;Prozent Strom.',
    'zaehlerstand.html': 'Abgelesen wird die Zahl vor dem Komma, beim digitalen Zähler der Wert hinter 1.8.0; 2.8.0 ist die Einspeisung. Ändert sich der Preis zum 1.&nbsp;Januar, darf der Grundversorger den Verbrauch sonst zeitanteilig schätzen, darum lohnt ein eigener Stand mit Foto. Aus zwei Zählerständen zeigt der Rechner, ob der monatliche Abschlag reicht.',
    'waschmaschine.html': 'Fast der ganze Strom beim Waschen geht ins Aufheizen: Ein älteres Gerät braucht voll beladen bei 60&nbsp;°C rund 1,1&nbsp;kWh, bei 40&nbsp;°C 0,6 und bei 30&nbsp;°C 0,4&nbsp;kWh. 40 statt 60&nbsp;°C spart laut Umweltbundesamt 35 bis 40&nbsp;Prozent Energie, bei vier Wäschen pro Woche rund 33&nbsp;€ im Jahr; Eco-Programm, volle Trommel und hohe Schleuderzahl sparen zusätzlich.',
    'weihnachten-strom.html': 'An Heiligabend und den Feiertagen braucht ein Haushalt laut Wien Energie etwa doppelt so viel Strom wie an einem normalen Wintertag, bis zu 10&nbsp;kWh mehr pro Tag. Größter Posten ist meist der Backofen mit 1,5 bis 2&nbsp;kWh pro Stunde, eine Gans kostet so 1,40 bis 2,60&nbsp;€; LED-Lichterketten fallen kaum ins Gewicht.',
    'kochen.html': 'Beim Kochen spart der Deckel am meisten, je nach Quelle 10&nbsp;Prozent bis zwei Drittel. Wasser bis etwa einen Liter erhitzt der Wasserkocher mit rund einem Drittel weniger Energie als der Herd, ein Schnellkochtopf halbiert den Verbrauch etwa. Induktion braucht laut Stiftung Warentest 290 bis 340&nbsp;kWh im Jahr, Glaskeramik 360 bis 430&nbsp;kWh.',
    'weihnachtsbeleuchtung.html': 'Eine LED-Lichterkette mit 5&nbsp;W kostet laut Verbraucherzentrale NRW für vier Wochen mit acht Stunden am Tag etwa 40&nbsp;Cent, eine alte Glühlampen-Kette mit 50&nbsp;W rund 4&nbsp;€. Strom aus Batterien ist etwa 300-mal so teuer wie aus der Steckdose. Für draußen brauchst du Ketten mit mindestens Schutzart IP44 und ein Prüfzeichen wie VDE, GS oder TÜV.',
    'lueften.html': 'Im Winter reichen drei bis zehn Minuten Stoßlüften, drei- bis viermal am Tag, und kein Raum sollte unter 16&nbsp;°C fallen. Liegt die Luftfeuchte länger über 50&nbsp;Prozent, solltest du lüften. Schimmel wächst, wenn an einer Wand längere Zeit 80&nbsp;Prozent Feuchte herrschen; kleine Flächen bis etwa einen halben Quadratmeter entfernst du mit Ethanol 70 bis 80&nbsp;Prozent.',
    'heizluefter.html': 'Heizlüfter, Ölradiator und Infrarotheizung machen aus einer Kilowattstunde Strom eine Kilowattstunde Wärme, keines davon ist sparsamer als das andere. Ein Heizlüfter mit 2.000&nbsp;W kostet bei 32&nbsp;ct pro kWh rund 64&nbsp;ct pro Stunde, Strom ist je kWh gut zweieinhalb- bis dreimal so teuer wie Gas. Heizlüfter gehören direkt in die Wandsteckdose, nicht an eine Mehrfachsteckdose.',
    'klimageraet.html': 'Ein mobiles Klimagerät (Monoblock) kostet etwa 250 bis 1.000&nbsp;€, ist laut Stiftung Warentest aber bis zu siebenmal weniger effizient als ein fest eingebautes Split-Gerät. Das Split-Gerät kostet 800 bis 2.500&nbsp;€ plus Einbau durch einen Kältetechnik-Fachbetrieb und braucht im Jahr Strom für etwa 52 bis 120&nbsp;€, ein Monoblock für 100 bis 150&nbsp;€. In der Mietwohnung brauchst du für ein Split-Gerät die Erlaubnis des Vermieters.',
    'smart-meter.html': 'Einen Smart Meter musst du ab 6.000&nbsp;kWh Jahresverbrauch, mit einem steuerbaren Gerät nach §&nbsp;14a oder mit einer Solaranlage über 7&nbsp;kW bekommen, im Haushalt kostet er dann höchstens 40 bis 50&nbsp;€ im Jahr. Alle anderen bekommen bis 2032 einen digitalen Zähler für höchstens 25&nbsp;€ im Jahr und können einen Smart Meter freiwillig für 100&nbsp;€ einmalig und 30&nbsp;€ im Jahr bestellen.',
    'solar-laden.html': 'Mit PV-Überschussladen lädst du dein E-Auto mit Solarstrom, der 6 bis 14&nbsp;ct pro kWh kostet statt rund 37&nbsp;ct aus dem Netz. Dafür braucht es eine Dachanlage ab etwa 6 bis 10&nbsp;kWp und mindestens rund 1,4&nbsp;kW Überschuss. Ein Balkonkraftwerk mit 800&nbsp;W reicht dafür nicht.',
}
WERKZEUGE = {'balkonkraftwerk-planer.html': 'Balkonkraftwerk-Planer', 'strompreis-heute.html': 'Strompreis heute', 'solar-atlas.html': 'Solar-Atlas', 'solar-rechner.html': 'Solar-Rechner', 'was-lohnt-sich.html': 'Einstieg in 5 Fragen', 'strompreis-morgen.html': 'Strompreis morgen', 'strompreis-ampel.html': 'Strompreis-Ampel', 'stromkosten.html': 'Stromkosten-Rechner'}     # Seite -> Name des Werkzeugs (bekommt zusätzlich WebApplication)
SKIP_LD = {'impressum.html', 'datenschutz.html', '404.html', 'index.html'}
LD_RE = re.compile(r'<script type="application/ld\+json" id="ld">.*?</script>\n?', re.S)
SITE_RE = re.compile(r'<script type="application/ld\+json" id="ld-site">.*?</script>\n?', re.S)
ERST = ROOT / 'werkzeuge' / 'erstdatum.json'      # Tag der ersten Veröffentlichung je Seite, für datePublished
def kurz_desc(d, mx=160, mn=90):
    """Beschreibung fürs Suchergebnis: höchstens mx Zeichen, an einer Satzgrenze gekürzt. Geht das nicht, bleibt sie, wie sie ist."""
    if len(d) <= mx:
        return d
    out = ''
    for part in re.split(r'(?<=[.!?])\s+', d):
        if len(out) + len(part) + (1 if out else 0) > mx:
            break
        out = (out + ' ' + part).strip()
    return out if len(out) >= mn else d


def kopf(s, name, url):
    """og:url ergänzen, Beschreibung kürzen, fehlende og-Angaben nachtragen. Gibt den neuen Seitentext und Hinweise zurück."""
    notes = []
    title = html.unescape(re.search(r'<title>(.*?)</title>', s).group(1))
    core = title.replace(' – ' + NAME, '')
    if len(core) > 60:
        notes.append('Titel ohne Marke %d Zeichen (höchstens 60): %s' % (len(core), core))
    m = re.search(r'<meta name="description" content="([^"]*)">', s)
    if m:
        full = html.unescape(m.group(1))
        if not re.search(r'<meta property="og:description"', s):
            s = s.replace(m.group(0), m.group(0) + '<meta property="og:description" content="%s">' % html.escape(full, quote=True), 1)
        short = kurz_desc(full)
        if short != full:
            s = s.replace(m.group(0), '<meta name="description" content="%s">' % html.escape(short, quote=True), 1)
        elif len(full) > 160:
            notes.append('Beschreibung %d Zeichen, erster Satz zu lang zum Kürzen' % len(full))
    if not re.search(r'<meta property="og:url"', s):
        s = re.sub(r'(<link rel="canonical" href="[^"]*">)', lambda k: k.group(1) + '<meta property="og:url" content="%s">' % url, s, count=1)
    if not re.search(r'<meta name="robots"', s):      # große Bildvorschau in der Google-Suche und in Discover erlauben
        s = re.sub(r'(<link rel="canonical" href="[^"]*">)', lambda k: k.group(1) + '<meta name="robots" content="max-image-preview:large">', s, count=1)
    if 'href="/feed.xml"' not in s:                    # RSS-Feed mit den neuesten Ratgebern
        s = re.sub(r'(<link rel="canonical" href="[^"]*">)', lambda k: k.group(1) + '<link rel="alternate" type="application/rss+xml" title="%s: neue Ratgeber" href="/feed.xml">' % NAME, s, count=1)
    if 'rel="manifest"' not in s:                       # als App installierbar (manifest.webmanifest, sw.js, Anmeldung in site.js)
        s = re.sub(r'(<link rel="canonical" href="[^"]*">)', lambda k: k.group(1) + '<link rel="manifest" href="/manifest.webmanifest">', s, count=1)
    if not re.search(r'<meta property="og:image"', s) and (ROOT / 'assets' / 'og' / 'index.jpg').exists():
        s = re.sub(r'(<meta property="og:url" content="[^"]*">)', lambda k: k.group(1) + '<meta property="og:image" content="%s/assets/og/index.jpg">' % SITE, s, count=1)
    return s, notes


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


def feed(erst):
    """feed.xml: die 30 neuesten Seiten als RSS, für Feed-Leser und Dienste, die neue Ratgeber abholen. Schreibt sich bei jedem Lauf neu."""
    import email.utils, datetime
    aus = {'impressum.html', 'datenschutz.html', '404.html', 'einbetten.html', 'index.html'}; items = []
    for name, tag in erst.items():
        f = ROOT / name
        if name in aus or not f.exists():
            continue
        s = f.read_text(encoding='utf-8'); t = re.search(r'<title>(.*?)</title>', s, re.S); d = re.search(r'<meta property="og:description" content="([^"]*)">', s) or re.search(r'<meta name="description" content="([^"]*)">', s)
        if t:
            items.append((tag, name, html.unescape(t.group(1)).replace(' – ' + NAME, ''), html.unescape(d.group(1)) if d else ''))
    items.sort(reverse=True); x = lambda v: html.escape(v, quote=False)
    body = ''.join('<item><title>%s</title><link>%s/%s</link><guid isPermaLink="true">%s/%s</guid><pubDate>%s</pubDate><description>%s</description></item>'
                   % (x(t), SITE, n, SITE, n, email.utils.format_datetime(datetime.datetime.fromisoformat(tag + 'T08:00:00+01:00')), x(d)) for tag, n, t, d in items[:30])
    neu = ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel><title>%s: neue Ratgeber und Rechner</title><link>%s/</link>'
           '<description>Neue Ratgeber und Rechner rund um Strom zuhause.</description><language>de-DE</language><atom:link href="%s/feed.xml" rel="self" type="application/rss+xml"/>%s</channel></rss>\n' % (NAME, SITE, SITE, body))
    z = ROOT / 'feed.xml'
    if not z.exists() or z.read_text(encoding='utf-8') != neu:
        z.write_text(neu, encoding='utf-8')
    print('feed.xml', min(30, len(items)), 'Einträge')


def run():
    llms = []
    erst = json.loads(ERST.read_text(encoding='utf-8')) if ERST.exists() else {}
    for f in sorted(ROOT.glob('*.html')):
        s = f.read_text(encoding='utf-8')
        name = f.name
        title = re.search(r'<title>(.*?)</title>', s).group(1)
        desc = meta(s, 'description')
        url = SITE + ('/' if name == 'index.html' else '/' + name)
        if name not in {'impressum.html', 'datenschutz.html', '404.html'}:
            llms.append((name, html.unescape(title).replace(' – ' + NAME, ''), meta(s, 'og:description') or desc, url))
            s2, notes = kopf(s, name, url)
            if s2 != s:
                s = s2
                f.write_text(s, encoding='utf-8')
            for n in notes:
                print('HINWEIS', name, n)
            desc = meta(s, 'description')
        if name == 'index.html':                      # Startseite: sagt Google, wie die Website heißt
            org = {'@type': 'Organization', 'name': NAME, 'url': SITE + '/', 'logo': SITE + '/apple-touch-icon.png'}
            site = {'@context': 'https://schema.org', '@graph': [{'@type': 'WebSite', 'name': NAME, 'url': SITE + '/', 'inLanguage': 'de-DE',
                                                                   'description': desc, 'publisher': org}]}
            s = SITE_RE.sub('', s)
            s = s.replace('</head>', '<script type="application/ld+json" id="ld-site">%s</script>\n</head>' % json.dumps(site, ensure_ascii=False).replace('</', '<\\/'), 1)
            f.write_text(s, encoding='utf-8')
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
        if name not in erst:                          # neue Seite: heute zum ersten Mal gesehen
            erst[name] = day or datetime.date.today().isoformat()
        art['datePublished'] = erst[name]
        if day:
            art['dateModified'] = max(day, erst[name])
        if name in KURZ:
            art['abstract'] = text(KURZ[name])
        graph = [art]
        if name in WERKZEUGE:                         # Planer und Rechner-Seiten sind Werkzeuge, das sagen wir Suchmaschinen dazu
            graph.append({'@type': 'WebApplication', 'name': WERKZEUGE[name] + ' von ' + NAME, 'url': url, 'applicationCategory': 'UtilitiesApplication',
                          'operatingSystem': 'Alle, läuft im Browser', 'inLanguage': 'de-DE', 'isAccessibleForFree': True,
                          'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'EUR'}, 'description': desc})
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
    ERST.write_text(json.dumps(erst, ensure_ascii=False, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    feed(erst)
    # llms.txt: Übersicht für KI-Assistenten
    lines = ['# %s' % NAME, '',
             '> Ratgeber-Website zu Strom zuhause in Deutschland: Balkonkraftwerk, Wallbox, E-Auto laden, Wärmepumpe, Stromtarif, Stromsparen und Notstrom. Mit Rechnern, Quellen und Prüfdatum. Finanziert über gekennzeichnete Amazon-Partnerlinks.', '',
             '## Ratgeber und Rechner', '']
    for name, t, d, u in llms:
        lines.append('- [%s](%s): %s' % (t, u, d))
    (ROOT / 'llms.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('llms.txt', len(llms), 'Seiten')
    # suche.json: Titel und Beschreibung folgen der Seite, die Stichwörter (k) bleiben von Hand gepflegt
    sj = ROOT / 'suche.json'
    if sj.exists():
        idx = json.loads(sj.read_text(encoding='utf-8'))
        by = {e['u']: e for e in idx}
        for name, t, d, u in llms:
            key = '/' if name == 'index.html' else '/' + name
            e = by.get(key)
            if e is None:
                print('HINWEIS', name, 'fehlt in suche.json (Eintrag mit u, t, d und Stichwörtern k ergänzen)')
            elif key != '/':
                e['t'], e['d'] = t, d
        sj.write_text(json.dumps(idx, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
        print('suche.json', len(idx), 'Einträge')


if __name__ == '__main__':
    run()
    import frag_index   # frag.json: geprüfte Fragen und Antworten aller Seiten für frag.js (Suche und „Noch eine Frage?“)
    frag_index.main(str(ROOT), ('stromkosten', 'lexikon'))
