"""Prüft das Strompreis-Archiv: je Monat Seite und CSV vorhanden, Durchschnitt auf der Seite = Durchschnitt der CSV, Quellenangabe da,
letzter gespeicherter Tag höchstens 3 Tage alt. Aufruf: python3 werkzeuge/archiv-test.py  (endet mit „ALLE TESTS BESTANDEN“)"""
import sys, re, json, pathlib, datetime
ROOT = pathlib.Path(__file__).resolve().parent.parent; sys.path.insert(0, str(ROOT / 'werkzeuge')); import preisarchiv as p
bad = 0
def ok(c, t):
    global bad; print(('ok   ' if c else 'FEHLER ') + t); bad += 0 if c else 1
d = p.laden(); monate = sorted({k[:7] for k in d}); fehl = []; falsch = []; quelle = []
for ym in monate:
    f = ROOT / 'strompreis' / (ym + '.html'); c = ROOT / 'assets' / 'strompreis' / (ym + '.csv')
    if not f.exists() or not c.exists(): fehl.append(ym); continue
    w = [float(l.split(';')[2].replace(',', '.')) for l in c.read_text(encoding='utf-8').splitlines()[2:]]
    s = f.read_text(encoding='utf-8'); m = re.search(r'<div><b>([−\d,]+) ct</b><span>Durchschnitt', s)
    if not m or m.group(1) != p.z(sum(w) / len(w)): falsch.append(ym)
    if 'SMARD.de' not in s or 'CC BY 4.0' not in s: quelle.append(ym)
ok(len(monate) >= 23, '%d Monate gespeichert (%s bis %s)' % (len(monate), monate[0], monate[-1]))
ok(not fehl, 'jede Monatsseite und jede CSV ist da ' + ' '.join(fehl))
ok(not falsch, 'Durchschnitt auf der Seite = Durchschnitt der CSV ' + ' '.join(falsch))
ok(not quelle, 'Quelle und Lizenz stehen auf jeder Monatsseite ' + ' '.join(quelle))
alter = (datetime.date.today() - datetime.date.fromisoformat(max(d))).days
ok(alter <= 3, 'letzter gespeicherter Tag: %s (%d Tage alt)' % (max(d), alter))
u = (ROOT / 'strompreis-archiv.html').read_text(encoding='utf-8'); ok(all('/strompreis/%s.html' % ym in u for ym in monate), 'Übersicht verlinkt alle Monate')
sm = (ROOT / 'sitemap.xml').read_text(encoding='utf-8'); ok(all('/strompreis/%s.html</loc>' % ym in sm for ym in monate), 'alle Monate stehen in der Sitemap')
print('\n%d FEHLER' % bad if bad else '\nALLE TESTS BESTANDEN'); sys.exit(1 if bad else 0)
