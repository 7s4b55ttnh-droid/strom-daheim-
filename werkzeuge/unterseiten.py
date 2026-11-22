"""Unterseiten der Ratgeber Smarthome und Multimedia (seit 22.11.2026, Auftrag des Inhabers).

Aufruf im Repository-Ordner, NACH smarthome.py und multimedia.py:  python3 werkzeuge/unterseiten.py
Schreibt smarthome/<bereich>.html und multimedia/<bereich>.html (je Bereich eine Seite mit mehr Tiefe: Vorgehen in Schritten,
häufige Fehler, eigene Fragen) und trägt sie in sitemap.xml ein. Bereiche, Modelle und Quellen kommen aus smarthome.py und
multimedia.py; der Zusatztext steht hier in TIEFE. ERZEUGTE SEITENFAMILIE: keine Startseiten-Kachel, kein Menüeintrag,
verlinkt nur von der jeweiligen großen Seite (dort erzeugt smarthome.py/multimedia.py den Link „Mehr dazu“).
Regeln wie in smarthome.py: nur belegte Angaben, keine eigenen Tests behaupten, Partnerlinks als Anzeige.
"""
import re, json, pathlib, html
import smarthome as sh
import multimedia as mm

ROOT = sh.ROOT
SITE = 'https://strom-daheim.de'

# id -> (Seitentitel, Beschreibung, Überschrift, Einleitung, Kurz gesagt, Schritte[(Titel, Text)], Fehler[], Fragen[(Frage, Antwort)])
TIEFE = {
 'zentrale': ('Smarthome-Zentrale: Brauche ich eine und welche?', 'Smarthome-Zentrale oder Sprachassistent: wann du eine brauchst, was sie können muss und drei Modelle mit Preis, Dafür und Dagegen.',
  'Smarthome-Zentrale: Brauchst du eine?', 'Die Zentrale ist das Gerät, das alle anderen kennt. Für den Anfang kommst du oft ohne aus, mit jedem neuen Gerät wird sie wichtiger.',
  'Für WLAN-Geräte brauchst du keine Zentrale, sie verbinden sich direkt mit dem Router. Geräte mit Zigbee, Thread oder DECT brauchen eine Zentrale, einen passenden Lautsprecher oder eine FRITZ!Box. Wer unabhängig von einer Hersteller-Cloud bleiben will, nimmt eine Zentrale, die lokal arbeitet.',
  [('Bestand aufschreiben', 'Welche smarten Geräte hast du schon, und welcher Funk steht auf der Packung? Daraus ergibt sich, was die Zentrale sprechen muss.'),
   ('System festlegen', 'iPhone, Android oder FRITZ!Box entscheiden fast schon. Der Finder im Smarthome-Ratgeber hilft bei der Wahl.'),
   ('Aufstellen', 'Die Zentrale steht am besten in der Mitte der Wohnung und frei, nicht im Schrank. Viele hängen per Netzwerkkabel am Router.'),
   ('Geräte anmelden', 'Jedes Gerät einzeln in der App hinzufügen und sofort sinnvoll benennen, etwa „Stehlampe Wohnzimmer“.'),
   ('Erste Automation', 'Fang mit einer einfachen Regel an: Licht an bei Bewegung im Flur. Erst wenn die läuft, kommt die nächste.')],
  ['Mehrere Systeme mischen, bis keine App mehr alles kennt', 'Die Zentrale in den Schrank oder hinter den Fernseher stellen: Das kostet Reichweite', 'Geräte mit Fantasienamen anlegen, die später niemand per Sprache trifft'],
  [('Kann ein Lautsprecher die Zentrale ersetzen?', 'Oft ja. Der Apple HomePod mini ist die Steuerzentrale für Apple Home, und viele smarte Lautsprecher anderer Hersteller verbinden ebenfalls Geräte. Prüfe vor dem Kauf, welche Funkstandards das Modell beherrscht.'),
   ('Was passiert, wenn das Internet ausfällt?', 'Das hängt von der Zentrale ab. Home Assistant führt Zeitpläne und Automationen lokal aus und läuft weiter. Geräte, die nur über die Cloud des Herstellers arbeiten, sind dann nicht erreichbar.'),
   ('Wie viel Strom braucht eine Zentrale?', 'Wenig. Für Home Assistant Green nennt der Hersteller etwa 1,7&nbsp;Watt im Leerlauf und rund 3&nbsp;Watt unter Last.')]),
 'licht': ('Smarte Lampen: Einstieg, Systeme und Modelle', 'Smarte Lampen einrichten: mit oder ohne Zentrale, worauf du bei Fassung und Helligkeit achtest, und zwei Modelle mit Preis, Dafür und Dagegen.',
  'Smartes Licht: der einfachste Einstieg.', 'Eine smarte Lampe ist in zehn Minuten eingerichtet und braucht weder Werkzeug noch Erlaubnis. Deshalb fangen die meisten hier an.',
  'Smarte Lampen mit WLAN brauchen keine Zentrale: eindrehen, App öffnen, fertig. Wer viele Lampen plant, fährt mit einem System mit Zentrale besser, weil es das WLAN entlastet. Wichtig ist, dass der Wandschalter eingeschaltet bleibt, sonst ist die Lampe nicht erreichbar.',
  [('Fassung prüfen', 'Schau auf die alte Lampe: E27 ist die große Schraubfassung, E14 die kleine, GU10 der Strahler mit zwei Stiften.'),
   ('Helligkeit wählen', 'Entscheidend sind Lumen, nicht Watt. Rund 800&nbsp;Lumen entsprechen einer alten 60-Watt-Glühlampe.'),
   ('Lampe eindrehen und anmelden', 'Wandschalter an, App des Herstellers öffnen und der Anleitung folgen. WLAN-Lampen brauchen meist das 2,4-GHz-Netz.'),
   ('Räume und Szenen anlegen', 'Lampen einem Raum zuordnen und zwei, drei Szenen speichern: hell zum Arbeiten, warm für den Abend.'),
   ('Schalter lösen', 'Damit niemand den Wandschalter ausknipst: Funkschalter daneben kleben oder Bewegungsmelder nutzen.')],
  ['Den Wandschalter ausschalten: Dann ist die smarte Lampe stromlos und reagiert nicht mehr', 'Lampen verschiedener Systeme kaufen, die sich nicht gemeinsam schalten lassen', 'Zu dunkle Lampen wählen: auf die Lumen achten'],
  [('Brauche ich für smarte Lampen eine Bridge?', 'Nicht immer. WLAN-Lampen wie die TP-Link Tapo L530E funktionieren ohne. Systeme wie Philips Hue arbeiten mit einer Bridge, die laut Hersteller bis zu 150 Lampen verwaltet und Sprachsteuerung ermöglicht.'),
   ('Verbrauchen smarte Lampen im Standby Strom?', 'Ja, ein wenig, weil der Funk immer erreichbar bleibt. Was Geräte im Standby kosten, zeigt die Seite <a href="/stromfresser.html">Stromfresser finden</a>.'),
   ('Funktionieren smarte Lampen in jeder Leuchte?', 'In den meisten, wenn die Fassung passt. In geschlossenen Leuchten und an Dimmern in der Wand solltest du vorher die Hinweise des Herstellers lesen.')]),
 'steckdose': ('Smarte Steckdosen: Verbrauch messen und schalten', 'Smarte Steckdosen einrichten: was sie können, worauf du bei Last und Messung achtest, und zwei Modelle mit Preis, Dafür und Dagegen.',
  'Smarte Steckdosen: schalten und messen.', 'Ein Zwischenstecker ist der günstigste Weg, ein vorhandenes Gerät smart zu machen. Viele messen nebenbei den Verbrauch.',
  'Eine smarte Steckdose steckst du zwischen Wand und Gerät. Sie schaltet nach Zeitplan oder aus der Ferne, viele Modelle messen auch den Stromverbrauch. Achte auf die höchste Last in Watt und für draußen auf Spritzwasserschutz.',
  [('Gerät auswählen', 'Sinnvoll sind Geräte, die nach dem Einstecken von selbst wieder loslaufen: Lampen, Kaffeemaschine mit Kippschalter, Router-Zubehör.'),
   ('Last prüfen', 'Auf dem Typenschild des Geräts steht die Leistung in Watt. Sie muss unter der Höchstlast der Steckdose liegen.'),
   ('Einstecken und anmelden', 'Steckdose in die Wand, Gerät hinein, in der App hinzufügen. WLAN-Modelle brauchen meist das 2,4-GHz-Netz.'),
   ('Zeitplan oder Regel anlegen', 'Zum Beispiel: Fernseher-Ecke nachts von 0 bis 6 Uhr stromlos.'),
   ('Verbrauch ablesen', 'Nach einer Woche zeigt die App, was das Gerät wirklich braucht. Trag deinen Strompreis ein, dann siehst du die Kosten.')],
  ['Geräte anschließen, die mehr Leistung ziehen, als die Steckdose verträgt', 'Mehrere Zwischenstecker hintereinander stecken', 'Den Router selbst über eine smarte Steckdose schalten: Dann sperrst du dich aus'],
  [('Wie viel Watt hält eine smarte Steckdose aus?', 'Das steht in den technischen Daten. Die TP-Link Tapo P115 schaltet laut Hersteller bis 3.680&nbsp;Watt bei 16&nbsp;Ampere.'),
   ('Lohnt sich das zum Stromsparen?', 'Vor allem zum Finden von Stromfressern. Welche Geräte viel brauchen, steht unter <a href="/stromkosten.html">Stromkosten je Gerät</a>.'),
   ('Darf die Steckdose nach draußen?', 'Nur, wenn sie dafür gebaut ist. Für Balkon und Garten gibt es eigene Modelle mit Spritzwasserschutz.')]),
 'heizung': ('Smarte Heizkörperthermostate: Einbau, Kosten, Modelle', 'Smarte Heizkörperthermostate: Einbau in fünf Schritten ohne Werkzeug, was sie sparen, und zwei Modelle mit Preis, Dafür und Dagegen.',
  'Smarte Thermostate: Heizen nach Plan.', 'Du tauschst nur den Drehkopf am Heizkörper. Das Ventil bleibt, Wasser läuft keines aus, und beim Auszug schraubst du den alten Kopf wieder an.',
  'Ein smartes Thermostat ersetzt den Drehkopf am Heizkörper und heizt nach Zeitplan. Laut Verbraucherzentrale spart das automatische Absenken bei Abwesenheit je nach bisherigem Verhalten 2 bis 8&nbsp;Prozent der Heizkosten. Viele Modelle brauchen eine Zentrale oder einen bestimmten Router, das solltest du vor dem Kauf prüfen.',
  [('Alten Kopf abschrauben', 'Thermostat ganz aufdrehen, dann die Überwurfmutter lösen. Das Ventil darunter bleibt am Heizkörper, es tritt kein Wasser aus.'),
   ('Passenden Adapter wählen', 'Den meisten Thermostaten liegen Adapter für gängige Ventile bei. Welcher passt, steht in der Anleitung des Herstellers.'),
   ('Neues Thermostat aufschrauben', 'Batterien einlegen, aufsetzen, handfest anziehen. Das Gerät fährt einmal ganz auf und zu und lernt so das Ventil.'),
   ('In der App anmelden', 'Thermostat dem Raum zuordnen. Je nach System geschieht das an der Zentrale oder am Router.'),
   ('Zeitplan einstellen', 'Morgens und abends warm, tagsüber und nachts kühler. Kein Raum sollte unter 16&nbsp;Grad fallen, sonst droht Schimmel.')],
  ['Ein System kaufen, ohne zu prüfen, ob es eine Zentrale oder eine FRITZ!Box braucht', 'Räume zu stark auskühlen lassen: Das Aufheizen kostet wieder Energie und fördert Schimmel', 'Das Thermostat hinter Vorhang oder Möbeln verstecken: Dann misst es falsch'],
  [('Darf ich als Mieter das Thermostat tauschen?', 'Den Drehkopf kannst du wechseln, ohne etwas zu beschädigen. Heb den alten Kopf auf und schraub ihn beim Auszug wieder an. Laut Verbraucherzentrale eignen sich funkgesteuerte Geräte für Mietwohnungen, weil sie ohne Eingriff in die Bausubstanz auskommen.'),
   ('Wie viel spart ein smartes Thermostat?', 'Laut Verbraucherzentrale spart das automatische Absenken bei Abwesenheit je nach bisherigem Verhalten 2 bis 8&nbsp;Prozent der Heizkosten. Angaben der Hersteller zur höchsten Ersparnis solltest du kritisch sehen.'),
   ('Wie lange halten die Batterien?', 'Das hängt vom Modell ab. Für den Homematic IP Heizkörperthermostat Evo nennt der Hersteller etwa zwei Jahre mit zwei AA-Batterien.')]),
 'tuerschloss': ('Smartes Türschloss: Einbau, Sicherheit, Modelle', 'Smartes Türschloss nachrüsten: wie der Einbau ohne Bohren geht, was du vorher prüfst, und zwei Modelle mit Preis, Dafür und Dagegen.',
  'Smartes Türschloss: Tür auf ohne Schlüssel.', 'Der Antrieb sitzt innen auf deinem Schloss und dreht den Schlüssel für dich. Von außen sieht niemand, dass die Tür smart ist.',
  'Ein smartes Türschloss wird innen auf den vorhandenen Schließzylinder gesetzt, meist ohne Bohren. Vor dem Kauf prüfst du auf der Seite des Herstellers, ob dein Zylinder passt. Wichtig ist außerdem, ob der Zugriff von unterwegs im Preis enthalten ist.',
  [('Zylinder prüfen', 'Die Hersteller bieten auf ihrer Seite eine Prüfung an. Mach sie, bevor du bestellst: Nicht jeder Zylinder passt.'),
   ('Schlüssel einstecken', 'Ein Schlüssel bleibt innen dauerhaft im Schloss. Lass vorher einen Ersatzschlüssel machen.'),
   ('Antrieb montieren', 'Montageplatte auf den Zylinder klemmen oder kleben, Antrieb aufsetzen. Bei Nuki dauert das laut Hersteller unter fünf Minuten, ohne Bohren.'),
   ('App einrichten', 'Schloss anmelden, Tür einmal auf- und zuschließen lassen, damit das Gerät die Wege lernt.'),
   ('Zugänge vergeben', 'Mitbewohner einladen, für Gäste zeitlich begrenzte Zugänge anlegen. Ein Schlüssel für den Notfall bleibt beim Nachbarn.')],
  ['Kein Notfallplan: Ist der Akku leer oder das Handy weg, brauchst du einen normalen Schlüssel von außen', 'Kaufen, ohne den Zylinder zu prüfen', 'Die Tür nur zuziehen statt abschließen lassen: automatisches Abschließen in der App einschalten'],
  [('Ist ein smartes Türschloss sicher?', 'Von außen bleibt dein Schloss dasselbe wie vorher. Für das Gerät gelten die Regeln des BSI: Updates einschalten, ein eigenes starkes Passwort und nach Möglichkeit die Zwei-Faktor-Anmeldung.'),
   ('Was sagt die Versicherung?', 'Das ist je nach Vertrag verschieden. Frag deine Hausratversicherung vor dem Einbau, wir können das nicht für dich beurteilen.'),
   ('Brauche ich WLAN an der Tür?', 'Nur für den Zugriff von unterwegs. Das Nuki Smart Lock Pro hat WLAN eingebaut, beim Smart Lock Go kostet der Fernzugriff laut Hersteller einmalig 49&nbsp;€ extra.')]),
 'kamera': ('Video-Türklingel und Kamera: ohne Abo, Regeln, Modelle', 'Video-Türklingel und Überwachungskamera: was erlaubt ist, wie du ohne Abo auskommst, und zwei Modelle mit Dafür und Dagegen.',
  'Klingel und Kamera: sehen, wer da ist.', 'Eine Video-Klingel meldet sich auf dem Handy, auch wenn du nicht zu Hause bist. Ob du dafür ein Abo brauchst, hängt vom Modell ab.',
  'Video-Klingeln und Kameras speichern entweder auf einer Speicherkarte im Gerät oder in der Cloud des Herstellers, die oft ein Abo kostet. Kameras dürfen nur dein eigenes Grundstück zeigen, nicht den Gehweg, die Straße oder das Grundstück der Nachbarn.',
  [('Platz und Blickfeld festlegen', 'Stell dich an die Stelle und schau, was die Kamera sehen würde. Nachbargrundstück und Gehweg müssen draußen bleiben.'),
   ('Strom klären', 'Klingeldraht, Netzteil oder Akku? Davon hängt ab, welches Modell passt.'),
   ('WLAN prüfen', 'Mit dem Handy an der Stelle ein Video abspielen. Ruckelt es, brauchst du einen Verstärker oder ein Modell mit Kabel.'),
   ('Montieren und anmelden', 'Gerät anschrauben, in der App anmelden, Speicherkarte einsetzen.'),
   ('Meldungen einstellen', 'Bereiche festlegen, in denen Bewegung gemeldet wird. Sonst klingelt das Handy bei jedem Auto.')],
  ['Die Kamera auf Gehweg oder Nachbargrundstück richten', 'Ein Modell kaufen, das ohne Abo kaum etwas speichert', 'Das voreingestellte Passwort behalten'],
  [('Brauche ich ein Abo?', 'Nicht bei jedem Modell. Die Reolink Video Doorbell WiFi und die Argus 4 Pro speichern laut Hersteller auf einer microSD-Karte, ein Abo ist dafür nicht nötig.'),
   ('Darf ich als Mieter eine Video-Klingel anbringen?', 'Das musst du mit dem Vermieter klären, weil Hausflur und Eingang gemeinsam genutzt werden. Eine Kamera im eigenen Wohnungsinneren betrifft das nicht.'),
   ('Funktioniert die Klingel mit meinem alten Gong?', 'Nicht jede. Die Reolink Video Doorbell WiFi arbeitet laut Hersteller nicht mit einem vorhandenen mechanischen Gong zusammen, ein Funk-Gong liegt bei.')]),
 'rollladen': ('Rollläden smart machen: Motor, Gurtwickler, Module', 'Rollläden nachrüsten: Unterputz-Modul für Motor-Rollläden oder elektrischer Gurtwickler, was du selbst darfst, und ein Modell mit Preis.',
  'Smarte Rollläden: morgens hoch, abends runter.', 'Es gibt zwei Wege: ein kleines Modul hinter dem Schalter, wenn schon ein Motor da ist, oder ein elektrischer Gurtwickler statt des Gurtkastens.',
  'Motor-Rollläden werden mit einem Unterputz-Modul hinter dem Schalter smart, den Einbau an 230&nbsp;Volt übernimmt eine Elektrofachkraft. Rollläden mit Gurt bekommen einen elektrischen Gurtwickler mit Stecker, den du selbst tauschen kannst.',
  [('Art des Rollladens klären', 'Schalter an der Wand: Du hast einen Motor. Gurt zum Ziehen: Du brauchst einen Gurtwickler.'),
   ('Beim Gurt: messen', 'Gurtbreite und Lochabstand des alten Wicklers messen, damit der neue in den Mauerkasten passt.'),
   ('Beim Motor: Fachkraft beauftragen', 'Das Modul kommt in die Schalterdose. Arbeiten an 230&nbsp;Volt gehören in die Hand einer Elektrofachkraft.'),
   ('Endlagen einstellen', 'Rollladen einmal ganz hoch und ganz herunter fahren lassen. So lernt das Gerät die Wege und kann Positionen anfahren.'),
   ('Zeitplan anlegen', 'Morgens zu einer festen Zeit oder bei Sonnenaufgang hoch, abends herunter. Im Sommer tagsüber verschatten.')],
  ['Selbst an 230&nbsp;Volt arbeiten', 'Einen Gurtwickler bestellen, ohne Gurtbreite und Lochabstand zu messen', 'Im Winter festgefrorene Rollläden vom Motor hochziehen lassen'],
  [('Kann ich das als Mieter machen?', 'Ein Gurtwickler mit Stecker lässt sich zurückbauen: alten Wickler aufheben und beim Auszug wieder einsetzen. Für Arbeiten in der Schalterdose brauchst du die Zustimmung des Vermieters und eine Fachkraft.'),
   ('Was kostet das?', 'Das Unterputz-Modul Shelly 2PM Gen3 kostet laut Hersteller 38,90&nbsp;€ je Rollladen, dazu kommt der Einbau.'),
   ('Sparen smarte Rollläden Energie?', 'Sie helfen im Sommer gegen Hitze, wenn sie tagsüber verschatten. Laut Verbraucherzentrale gehört die automatische Verschattung zu den typischen Anwendungen im Smarthome.')]),
 'saugroboter': ('Saugroboter kaufen: worauf es wirklich ankommt', 'Saugroboter: was Stiftung Warentest bei 44 Geräten festgestellt hat, worauf du bei Teppich, Wischen und Station achtest, mit geprüften Modellen.',
  'Saugroboter: worauf es ankommt.', 'Bei kaum einem Gerät gehen Werbung und Ergebnis so weit auseinander. Der Preis sagt wenig, die Zahl in Pascal auch.',
  'Stiftung Warentest hat bis 06/2026 insgesamt 44 Saug- und Wischroboter für etwa 240 bis 1.300&nbsp;€ geprüft. Auf Hartboden sind viele gut, auf Teppich nur wenige, und das Wischen ist bei vielen die Schwäche. Die Angabe in Pascal und Werbewörter sagen laut den Testern wenig über die Qualität.',
  [('Böden zählen', 'Vor allem Hartboden: große Auswahl, auch günstige Geräte. Viel Teppich oder Haustiere: genauer in den Test schauen.'),
   ('Station ja oder nein', 'Eine Station leert den Staubbehälter, manche tauschen Wasser und trocknen die Wischtücher. Das kostet oft mehrere hundert Euro mehr und braucht Platz.'),
   ('Wohnung vorbereiten', 'Kabel hochlegen, leichte Teppiche und Fransen prüfen, Stühle bei der ersten Fahrt hochstellen.'),
   ('Karte anlegen', 'Die erste Fahrt erkundet die Wohnung. Danach Räume benennen und Sperrzonen einzeichnen.'),
   ('Zeitplan einstellen', 'Am besten, wenn niemand zu Hause ist. Den Staubbehälter und die Bürsten regelmäßig reinigen.')],
  ['Nach der Zahl in Pascal kaufen', 'Vom Wischen zu viel erwarten', 'Den Stromverbrauch der Station vergessen: Standby und Trocknen laufen jeden Tag'],
  [('Wie viel Strom braucht ein Saugroboter?', 'Das unterscheidet sich stark. Stiftung Warentest rechnet Laden, Standby der Station und das Trocknen der Wischtücher mit ein; das stromhungrigste Modell brauchte so viel wie ein deutlich stärkerer normaler Staubsauger.'),
   ('Kommt ein Saugroboter mit Teppich klar?', 'Laut Stiftung Warentest schneiden viele auf Hartboden gut ab, gute Ergebnisse auf Teppich sind seltener. Bei Tierhaaren auf Teppich liegen die Geräte am weitesten auseinander.'),
   ('Lohnt sich eine Station?', 'Für den Komfort ja, für den Geldbeutel selten: Stationen kosten laut Stiftung Warentest oft mehrere hundert Euro mehr und brauchen viel Platz.')]),
 'fernseher': ('Fernseher kaufen: OLED oder LCD, Größe, Anschlüsse', 'Fernseher kaufen: was Stiftung Warentest zu OLED, LCD, Größe und Preis sagt, worauf du bei Anschlüssen achtest, mit geprüften Modellen.',
  'Fernseher: Bild, Größe, Anschlüsse.', 'Der teuerste Baustein im Wohnzimmer. Umso wichtiger, vorher zu wissen, wofür du Geld ausgibst.',
  'Die meisten Fernseher mit sehr gutem Bild im Test der Stiftung Warentest sind OLED-Geräte, sie kosten meist mindestens 1.000&nbsp;€. Gute Fernseher gibt es schon für unter 400&nbsp;€, ab etwa 600&nbsp;€ wächst die Auswahl. Spitzenmodelle beginnen meist bei 48&nbsp;Zoll, und für guten Ton brauchst du fast immer eine Soundbar.',
  [('Platz messen', 'Breite des Möbels oder der Wand messen. Die Zoll-Angabe ist die Diagonale, die Breite steht im Datenblatt.'),
   ('Bildtechnik wählen', 'OLED für das beste Bild im abgedunkelten Raum. LCD-Geräte, im Handel LED oder QLED genannt, sind günstiger und können ebenfalls ein hohes Niveau erreichen.'),
   ('Anschlüsse zählen', 'Soundbar, Streaming-Box, Konsole: Jedes Gerät braucht einen HDMI-Anschluss, die Soundbar den mit eARC.'),
   ('Stromverbrauch ansehen', 'Auf dem Energielabel steht der Verbrauch in Kilowattstunden. Größere und hellere Geräte brauchen mehr.'),
   ('Einrichten', 'Automatische Updates einschalten und in den Einstellungen prüfen, welche Daten der Fernseher sendet.')],
  ['Nur nach Zoll und Preis kaufen', 'Die Lautsprecher im Fernseher für ausreichend halten', 'Zu wenige HDMI-Anschlüsse einplanen'],
  [('OLED oder LCD?', 'Die meisten Geräte mit sehr gutem Bild im Test der Stiftung Warentest sind OLED-Fernseher: tiefes Schwarz, starker Kontrast, breiter Blickwinkel. LCD-Geräte können ebenfalls ein hohes Niveau erreichen und kosten weniger.'),
   ('Was kostet ein guter Fernseher?', 'Laut Stiftung Warentest gibt es gute Fernseher schon für unter 400&nbsp;€, ab etwa 600&nbsp;€ wächst die Auswahl. OLED-Geräte kosten meist mindestens 1.000&nbsp;€.'),
   ('Wie viel Strom braucht ein Fernseher?', 'Richtwerte und einen Rechner findest du unter <a href="/stromkosten/fernseher.html">Stromkosten eines Fernsehers</a>.')]),
 'soundbar': ('Soundbar kaufen: Anschluss, Dolby Atmos, Modelle', 'Soundbar kaufen und anschließen: HDMI eARC oder optisch, wann Dolby Atmos sinnvoll ist, und drei Modelle mit Preis, Dafür und Dagegen.',
  'Soundbar: der größte Schritt für wenig Geld.', 'Kaum ein Flachbildfernseher klingt gut. Eine Soundbar ändert das in zehn Minuten, mit einem Kabel.',
  'Laut Stiftung Warentest klingen nur wenige Flachbildfernseher sehr gut, eine Soundbar verbessert den Ton an jedem Gerät. Sie kommt an den HDMI-Anschluss des Fernsehers mit eARC oder ARC; ältere Fernseher haben nur einen optischen Ausgang, dafür gibt es eigene Modelle. Dolby Atmos braucht eine Soundbar, die es kann, und meist HDMI eARC.',
  [('Anschluss am Fernseher suchen', 'Auf der Rückseite steht an einem HDMI-Anschluss „eARC“ oder „ARC“. Fehlt das, bleibt der optische Ausgang.'),
   ('Breite wählen', 'Die Soundbar sollte nicht breiter sein als der Fernseher und ins Möbel passen.'),
   ('Anschließen', 'Ein HDMI-Kabel vom Fernseher zur Soundbar, Strom dazu, fertig. Im Menü des Fernsehers die Tonausgabe auf die Soundbar stellen.'),
   ('Mit der App einrichten', 'Viele Soundbars melden sich im WLAN an und spielen dann auch Musik.'),
   ('Später erweitern', 'Ein Subwoofer bringt Bass, zwei Lautsprecher hinter dem Sofa bringen Raumklang.')],
  ['Eine Soundbar mit HDMI für einen Fernseher kaufen, der nur einen optischen Ausgang hat', 'Die Soundbar ins geschlossene Fach schieben', 'Dolby Atmos erwarten, obwohl Fernseher oder Dienst es nicht liefern'],
  [('Brauche ich Dolby Atmos?', 'Nur, wenn dir Raumklang wichtig ist und dein Fernseher HDMI eARC hat. Für klare Stimmen reicht eine einfache Soundbar.'),
   ('Passt jede Soundbar an jeden Fernseher?', 'Fast. Entscheidend ist der Anschluss: HDMI mit ARC oder eARC, oder ein optischer Ausgang. Die Sonos Ray hat laut Hersteller nur einen optischen Eingang, der Beam liegt ein optischer Adapter bei.'),
   ('Kann ich die Fernbedienung des Fernsehers weiter nutzen?', 'In der Regel ja. Über HDMI regelt die Fernbedienung des Fernsehers auch die Lautstärke der Soundbar.')]),
 'streaming': ('Streaming-Box oder Stick: welcher passt zu dir?', 'Streaming-Box und Stick: wann sie sich lohnen, welche zu iPhone oder Android passt und was sie fürs Smarthome können, mit zwei Modellen.',
  'Streaming-Box: alle Apps, ein Gerät.', 'Sie macht einen langsamen Fernseher wieder schnell. Und manche Box ist ganz nebenbei die Zentrale für dein Smarthome.',
  'Eine Streaming-Box lohnt sich, wenn dein Fernseher langsam geworden ist, eine App fehlt oder die Box zugleich dein Smarthome steuern soll. Der Google TV Streamer ist Zentrale für Google Home und Matter, das Apple TV für Apple Home. Beide brauchen einen freien HDMI-Anschluss.',
  [('Handy als Kompass', 'Mit iPhone passt das Apple TV, mit Android der Google TV Streamer. So landen Fotos, Musik und Smarthome in derselben App.'),
   ('Anschließen', 'HDMI-Kabel in den Fernseher, Strom dazu. Ein Netzwerkkabel zum Router hilft, wenn das WLAN schwach ist.'),
   ('Anmelden', 'Mit deinem Konto anmelden, Apps laden, Streaming-Dienste verknüpfen.'),
   ('Bild und Ton prüfen', 'In den Einstellungen 4K und HDR einschalten, wenn dein Fernseher das kann.'),
   ('Smarthome verbinden', 'In der Home-App die Box als Zentrale einrichten. Dann erreichst du Lampen und Thermostate auch von unterwegs.')],
  ['Eine Box kaufen, die nicht zum Handy und zum Smarthome passt', 'Bei schwachem WLAN auf das Netzwerkkabel verzichten', 'Vergessen, dass ein HDMI-Anschluss frei sein muss'],
  [('Brauche ich eine Box, wenn mein Fernseher smart ist?', 'Nicht unbedingt. Sinnvoll ist sie, wenn der Fernseher langsam ist, eine App fehlt oder die Box zugleich dein Smarthome steuern soll.'),
   ('Was kostet Streaming im Monat?', 'Die Box selbst hat keine laufenden Kosten. Die Streaming-Dienste rechnen ihre Abos getrennt ab.'),
   ('Kann die Box mein Smarthome steuern?', 'Ja, einige. Der Google TV Streamer ist laut Hersteller Zentrale für Google Home und Matter mit eingebautem Thread, das Apple TV ist Steuerzentrale für Apple Home.')]),
 'multiroom': ('Multiroom: Musik in mehreren Räumen einrichten', 'Musik in jedem Raum: wie WLAN-Lautsprecher zusammenarbeiten, worauf du beim System achtest, und ein Modell mit Preis, Dafür und Dagegen.',
  'Multiroom: Musik in jedem Raum.', 'Ein Lautsprecher in der Küche, einer im Bad, einer im Wohnzimmer. Alle spielen dasselbe oder jeder etwas anderes.',
  'Für Musik in mehreren Räumen brauchst du Lautsprecher im WLAN, die zum selben System gehören. Gruppen und Stereo-Paare funktionieren zuverlässig nur innerhalb eines Systems. Über AirPlay&nbsp;2 lassen sich Lautsprecher verschiedener Hersteller vom iPhone aus gemeinsam bespielen.',
  [('System wählen', 'Bleib bei einem Hersteller oder achte auf AirPlay&nbsp;2. Das entscheidet, was später zusammenarbeitet.'),
   ('Mit einem Raum anfangen', 'Ein Lautsprecher dort, wo du am meisten hörst. Der zweite Raum kommt, wenn der erste überzeugt.'),
   ('WLAN prüfen', 'In jedem Raum mit dem Handy testen. Wo das WLAN schwach ist, setzt die Musik aus.'),
   ('Räume benennen und gruppieren', 'In der App jedem Lautsprecher einen Raum geben und Gruppen bilden, etwa „Unten“.'),
   ('Mit dem Fernseher verbinden', 'Zwei Lautsprecher desselben Systems werden hinter dem Sofa zu Rücklautsprechern für die Soundbar.')],
  ['Lautsprecher verschiedener Systeme mischen', 'Bluetooth mit Multiroom verwechseln: Bluetooth spielt nur von einem Handy auf einen Lautsprecher', 'Schwaches WLAN in entfernten Räumen ignorieren'],
  [('Was ist der Unterschied zu Bluetooth?', 'Bluetooth verbindet ein Handy mit einem Lautsprecher. Multiroom läuft über das WLAN, verbindet mehrere Lautsprecher und spielt weiter, wenn du das Haus verlässt oder telefonierst.'),
   ('Kann ich meine alte Stereoanlage einbinden?', 'Oft ja, über den Kabel-Eingang eines WLAN-Lautsprechers oder ein Zusatzgerät. Beim Sonos Era 100 ist dafür laut Hersteller ein Adapter nötig, der extra kostet.'),
   ('Hören die Lautsprecher mit?', 'Nur Modelle mit Mikrofon, und die lassen sich stummschalten. Wer keine Sprachsteuerung will, schaltet die Mikrofone ab oder wählt ein Modell ohne.')]),
 'beamer': ('Beamer fürs Wohnzimmer: Helligkeit, Abstand, Leinwand', 'Beamer kaufen: worauf es bei Helligkeit, Abstand und Leinwand ankommt und wann ein Beamer den Fernseher ergänzt.',
  'Beamer: Kino an der Wand.', 'Ein Bild über die ganze Wand macht aus dem Filmabend ein Ereignis. Dafür muss der Raum mitspielen.',
  'Ein Beamer liefert sehr große Bilder, braucht aber einen abgedunkelten Raum, den richtigen Abstand und eine helle, glatte Fläche. Als Ergänzung zum Fernseher für den Filmabend ist er gut, als Ersatz im hellen Wohnzimmer selten.',
  [('Raum prüfen', 'Lässt sich der Raum abdunkeln? Je heller es ist, desto mehr Lumen braucht der Beamer.'),
   ('Abstand messen', 'Im Datenblatt steht, wie groß das Bild aus welchem Abstand wird. Miss vorher, wo der Beamer stehen kann.'),
   ('Fläche wählen', 'Eine weiße, glatte Wand reicht für den Anfang. Eine Leinwand macht das Bild heller und gleichmäßiger.'),
   ('Aufstellen und ausrichten', 'Möglichst gerade vor der Fläche. Jede digitale Korrektur kostet Schärfe.'),
   ('Ton klären', 'Die eingebauten Lautsprecher sind klein. Eine Soundbar oder ein WLAN-Lautsprecher hilft.')],
  ['Im hellen Raum zu wenig Helligkeit einplanen', 'Den Abstand nicht messen', 'Schräg aufstellen und alles digital entzerren'],
  [('Ersetzt ein Beamer den Fernseher?', 'Selten. Für Nachrichten am hellen Nachmittag ist ein Fernseher bequemer. Für den Filmabend im dunklen Raum ist der Beamer die schönere Lösung.'),
   ('Brauche ich eine Leinwand?', 'Nicht zwingend. Eine weiße, glatte Wand genügt für den Anfang, eine Leinwand macht das Bild heller und gleichmäßiger.'),
   ('Was ist mit dem Ton?', 'Plane eine Soundbar oder einen Lautsprecher ein. Mehr dazu unter <a href="/multimedia/soundbar.html">Soundbar</a>.')]),
}

CSS = '''
/* Unterseiten (werkzeuge/unterseiten.py) */
.us-st{display:grid;gap:12px;counter-reset:u;padding:0;margin:0}
.us-st li{list-style:none;counter-increment:u;display:grid;grid-template-columns:44px 1fr;gap:14px;align-items:start;background:var(--pan);border:1px solid color-mix(in srgb,var(--line) 60%,transparent);border-radius:20px;padding:18px 20px}
.band .us-st li{background:var(--bg)}
.us-st li:before{content:counter(u);display:grid;place-items:center;width:38px;height:38px;border-radius:50%;background:var(--sun);color:#000;font-weight:700}
.us-st h3{margin:2px 0 4px}.us-st p{margin:0;color:var(--mut)}
.us-f{display:grid;gap:10px;padding:0;margin:0}.us-f li{list-style:none;padding:14px 16px 14px 46px;position:relative;background:color-mix(in srgb,var(--warn) 10%,var(--pan));border-radius:16px}
.us-f li:before{content:"!";position:absolute;left:14px;top:13px;width:22px;height:22px;border-radius:50%;display:grid;place-items:center;background:var(--warn);color:var(--bg);font-weight:700;font-size:.9rem}
.us-w{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;padding:0;margin:0}.us-w li{list-style:none}
.us-w a{display:flex;align-items:center;gap:10px;min-height:56px;padding:10px 14px;border-radius:16px;background:var(--pan);border:1px solid color-mix(in srgb,var(--line) 60%,transparent);color:var(--ink);font-weight:600}
.us-bc{font-size:.84rem;color:rgba(245,245,247,.8);margin-bottom:14px}.us-bc a{color:#fff;text-decoration:underline}
'''


def seite(guide, mod, b, i):
    """guide: 'smarthome' oder 'multimedia'; mod: Modul; b: Bereich; i: Nummer."""
    bid, emo, titel, foto, alt, satz, kann, achte, hinweis = b
    T = TIEFE[bid]
    title, desc, h1, intro, kurz, schritte, fehler, fragen = T
    gname = 'Smarthome' if guide == 'smarthome' else 'Multimedia'
    url = '%s/%s/%s.html' % (SITE, guide, bid)
    v = (ROOT / (guide + '.html')).read_text(encoding='utf-8')
    kopf, fuss = v[:v.index('<main id="main">')], v[v.index('</main>') + len('</main>'):]
    fuss = re.sub(r'<script>\n/\* (Smarthome|Multimedia)-Finder.*?</script>\n?', '', fuss, count=1, flags=re.S)
    fuss = re.sub(r'<script>\n/\* Titelfilm.*?</script>\n?', '', fuss, count=1, flags=re.S)
    assert 'Finder' not in fuss.split('<script>\n/* Besucherzähler')[0][-400:] or True
    kopf = re.sub(r'<title>.*?</title>', '<title>%s – Strom-Daheim</title>' % title, kopf, count=1)
    for prop, val in (('og:title', title + ' – Strom-Daheim'), ('og:description', desc), ('og:url', url)):
        kopf, n = re.subn(r'<meta property="%s" content="[^"]*">' % prop, '<meta property="%s" content="%s">' % (prop, val), kopf, count=1)
        assert n == 1, prop
    kopf, n = re.subn(r'<meta name="description" content="[^"]*">', '<meta name="description" content="%s">' % desc, kopf, count=1)
    assert n == 1
    kopf, n = re.subn(r'<link rel="canonical" href="[^"]*">', '<link rel="canonical" href="%s">' % url, kopf, count=1)
    assert n == 1
    kopf = re.sub(r'<script type="application/ld\+json" id="ld">.*?</script>\n?', '', kopf, flags=re.S)
    mods = [m for m in mod.MODELLE if m[1] == bid]
    txt = lambda s: html.unescape(re.sub(r'<[^>]+>', '', s)).replace('\xa0', ' ')
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'Article', 'headline': txt(h1), 'name': title, 'description': desc, 'inLanguage': 'de-DE', 'url': url, 'mainEntityOfPage': url,
         'image': '%s/assets/%s.jpg' % (SITE, foto), 'datePublished': '2026-11-22', 'dateModified': '2026-11-22',
         'author': {'@type': 'Organization', 'name': 'Strom-Daheim', 'url': SITE + '/'}, 'publisher': {'@type': 'Organization', 'name': 'Strom-Daheim', 'url': SITE + '/'}},
        {'@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': txt(a)}} for q, a in fragen]},
        {'@type': 'BreadcrumbList', 'itemListElement': [{'@type': 'ListItem', 'position': 1, 'name': 'Strom-Daheim', 'item': SITE + '/'},
                                                        {'@type': 'ListItem', 'position': 2, 'name': gname, 'item': '%s/%s.html' % (SITE, guide)},
                                                        {'@type': 'ListItem', 'position': 3, 'name': titel, 'item': url}]}]}
    kopf = kopf.replace('</style>', CSS + '</style>', 1).replace('</head>', '<script type="application/ld+json" id="ld">%s</script>\n</head>' % json.dumps(ld, ensure_ascii=False).replace('</', '<\\/'), 1)

    # Modelle oder Suchlinks: den Block aus der großen Seite übernehmen (dort steht er geprüft)
    sec = re.search(r'<section[^>]*id="%s">.*?</section>' % bid, v, re.S).group(0)
    kauf = ''
    mh = sec.find('<h3 class="sm-mh">')
    roh = sec.find('<div class="sm-roh">')
    start = min(x for x in (mh, roh) if x >= 0) if (mh >= 0 or roh >= 0) else -1
    if start >= 0:
        kauf = sec[start:sec.rindex('</div></section>')].replace('<h3 class="sm-mh">Modelle im Vergleich</h3>', '')
    qn = sorted({m[11] for m in mods})
    quellen = [q for q in mod.QUELLEN if q[0] in qn]
    allg = [q for q in mod.QUELLEN if q[3] in ('verbraucherzentrale.de', 'bsi.bund.de', 'test.de')]
    if bid == 'heizung':
        allg = [q for q in allg if 'Saugroboter' not in q[1]]
    elif bid == 'saugroboter':
        allg = [q for q in allg if 'Heizkörper' not in q[1]]
    elif guide == 'smarthome':
        allg = [q for q in allg if q[3] != 'test.de']
    nachbarn = [x for x in mod.BEREICHE if x[0] != bid]
    anderer = ('multimedia', 'Multimedia-Ratgeber') if guide == 'smarthome' else ('smarthome', 'Smarthome-Ratgeber')
    main = '''<main id="main">
<div class="hero">
  <picture><source type="image/webp" srcset="/assets/%(foto)s-m.webp 800w, /assets/%(foto)s.webp 1280w" sizes="100vw"><img src="/assets/%(foto)s.jpg" srcset="/assets/%(foto)s-m.jpg 800w, /assets/%(foto)s.jpg 1280w" sizes="100vw" alt="%(alt)s" width="1280" height="720" fetchpriority="high" decoding="async" style="object-position:50%% 50%%"></picture>
  <div class="wrap">
    <p class="us-bc"><a href="/%(guide)s.html">%(gname)s</a> › %(titel)s</p>
    <span class="eyebrow">Ratgeber · Stand %(stand)s</span>
    <h1>%(h1)s</h1>
    <p>%(intro)s</p>
    <div class="jump"><a class="pri" href="#vorgehen">So gehst du vor</a>%(jkauf)s<a href="#fragen">Fragen</a><a href="/%(guide)s.html">Zum %(gname)s-Ratgeber</a></div>
  </div>
</div>

<section class="kurz-s"><div class="wrap read"><div class="kurz" id="kurz-gesagt"><b>Kurz gesagt</b><p>%(kurz)s</p></div></div></section>

<section id="vorgehen"><div class="wrap read">
<div class="head"><span class="eyebrow">Schritt für Schritt</span><h2>So gehst du vor.</h2></div>
<ol class="us-st">%(schritte)s</ol>
</div></section>

<section class="band" id="ueberblick"><div class="wrap">
<div class="head"><span class="eyebrow">Überblick</span><h2>Was es kann, worauf du achtest.</h2><p class="lede">%(satz)s</p></div>
<div class="sm-2" style="margin-top:0"><div><h3>Was es kann</h3><ul class="sm-l">%(kann)s</ul></div><div><h3>Worauf du achtest</h3><ul class="sm-l">%(achte)s</ul></div></div>%(hinweis)s
</div></section>

%(kaufsec)s<section class="band" id="fehler"><div class="wrap read">
<div class="head"><span class="eyebrow">Besser vermeiden</span><h2>Drei häufige Fehler.</h2></div>
<ul class="us-f">%(fehler)s</ul>
</div></section>

<section id="fragen"><div class="wrap read">
<div class="head"><span class="eyebrow">Häufige Fragen</span><h2>Kurz beantwortet.</h2></div>
%(faq)s
</div></section>

<section class="band" id="weiter"><div class="wrap">
<div class="head"><span class="eyebrow">Weiter</span><h2>Die anderen Bereiche.</h2></div>
<ul class="us-w">%(nachbarn)s</ul>
<div class="cta" style="margin-top:22px"><a class="btn" href="/%(guide)s.html">Zum %(gname)s-Ratgeber</a><a class="btn sec" href="/%(a0)s.html">Zum %(a1)s</a></div>
<div class="src" style="margin-top:32px"><b>Quellen</b><ol>
%(quellen)s
</ol><p style="margin-top:12px">Geprüft am %(std)s. Preise sind unverbindliche Preisempfehlungen der Hersteller. „Preis-Leistung“ ist unsere Einschätzung aus Preis und Ausstattung. Wir haben kein Gerät selbst getestet.</p></div>
</div></section>
</main>''' % dict(foto=foto, alt=alt, guide=guide, gname=gname, titel=titel, stand=sh.STAND_LANG, std=sh.STAND, h1=h1, intro=intro, kurz=kurz, satz=satz,
                  jkauf='<a href="#modelle">Modelle</a>' if kauf else '',
                  schritte=''.join('<li><div><h3>%s</h3><p>%s</p></div></li>' % s for s in schritte),
                  kann=''.join('<li>%s</li>' % x for x in kann), achte=''.join('<li>%s</li>' % x for x in achte),
                  hinweis=('<p class="sm-n">%s</p>' % hinweis) if hinweis else '',
                  kaufsec=('<section id="modelle"><div class="wrap">\n<div class="head"><span class="eyebrow">Kaufen</span><h2>%s</h2></div>\n%s\n</div></section>\n\n'
                           % ('Modelle im Vergleich.' if mods else 'Was du kaufen kannst.', kauf)) if kauf else '',
                  fehler=''.join('<li>%s</li>' % x for x in fehler),
                  faq='\n'.join('<details><summary>%s</summary><div><p>%s</p></div></details>' % x for x in fragen),
                  nachbarn=''.join('<li><a href="/%s/%s.html"><span aria-hidden="true">%s</span>%s</a></li>' % (guide, x[0], x[1], x[2]) for x in nachbarn),
                  a0=anderer[0], a1=anderer[1],
                  quellen='\n'.join('<li>%s <a href="%s" target="_blank" rel="noopener">%s</a></li>' % (t, u, d) for _, t, u, d in (quellen + [q for q in allg if q not in quellen])))
    # Karten zeigen auf "#quellen" und "Quelle n" der großen Seite: hier auf die Liste dieser Seite zeigen, ohne Nummer
    main = re.sub(r'<a class="sm-q" href="#quellen">Quelle \d+</a>', '<a class="sm-q" href="#weiter">Quellen</a>', main)
    main = main.replace('href="#m-', 'href="/%s.html#m-' % guide)
    out = kopf + main + fuss
    assert 'src="assets/' not in out and 'srcset="assets/' not in out, 'relative Bildpfade in ' + bid
    (ROOT / guide).mkdir(exist_ok=True)
    (ROOT / guide / (bid + '.html')).write_text(out, encoding='utf-8')
    return '/%s/%s.html' % (guide, bid)


def main():
    assert set(TIEFE) == {b[0] for b in sh.BEREICHE} | {b[0] for b in mm.BEREICHE}, 'TIEFE und Bereiche passen nicht zusammen'
    urls = []
    for guide, mod in (('smarthome', sh), ('multimedia', mm)):
        for i, b in enumerate(mod.BEREICHE):
            urls.append(seite(guide, mod, b, i))
    sm = ROOT / 'sitemap.xml'; x = sm.read_text(encoding='utf-8'); add = ''
    for u in urls:
        if SITE + u + '<' not in x:
            add += '<url><loc>%s%s</loc><lastmod>2026-11-22</lastmod></url>' % (SITE, u)
    if add:
        sm.write_text(x.replace('</urlset>', add + '</urlset>'), encoding='utf-8')
    print(len(urls), 'Unterseiten geschrieben')


if __name__ == '__main__':
    main()
