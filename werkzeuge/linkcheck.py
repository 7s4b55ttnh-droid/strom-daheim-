"""Link-Wächter: prüft alle Links zu fremden Seiten auf strom-daheim.de und stil-daheim.de und schreibt werkzeuge/linkbericht.json.

Läuft täglich über .github/workflows/linkcheck.yml (kostet keine Claude-Nutzung). Die Tagesagenten lesen den Bericht und
ersetzen oder entfernen tote Links. Als tot gilt ein Link erst, wenn er an zwei Läufen hintereinander „Seite nicht gefunden“
(404, 410) meldet oder die Adresse nicht mehr existiert. Sperren gegen automatische Abrufe (403, 429), Serverfehler und
Zeitüberschreitungen zählen nicht, weil die Seite für Menschen meist trotzdem erreichbar ist.
Nicht geprüft: Amazon-Links (prüfen die Tagesagenten selbst) und der Besucherzähler.
Aufruf: python3 werkzeuge/linkcheck.py"""
import json, re, sys, html, pathlib, datetime, urllib.request, urllib.error, socket, concurrent.futures
ROOT = pathlib.Path(__file__).resolve().parent.parent
ZIEL = ROOT / 'werkzeuge' / 'linkbericht.json'
AUS = re.compile(r'^https?://([^/]*\.)?(amazon\.[a-z.]+|amzn\.to|goatcounter\.com|strom-daheim\.de|stil-daheim\.de|schema\.org|w3\.org)(/|$)', re.I)
UA = {'User-Agent': 'Mozilla/5.0 (compatible; Linkpruefung von strom-daheim.de)', 'Accept': 'text/html,*/*;q=0.8', 'Accept-Language': 'de'}
LINK = re.compile(r'<a\s[^>]*href="(https?://[^"]+)"', re.I)


def sammeln():
    """{Adresse: [Seiten, auf denen sie steht]}"""
    wo = {}
    def nimm(seite, text):
        for u in LINK.findall(text):
            u = html.unescape(u).split('#')[0]
            if not AUS.match(u):
                wo.setdefault(u, [])
                if seite not in wo[u]:
                    wo[u].append(seite)
    for f in sorted(list(ROOT.glob('*.html')) + list((ROOT / 'lexikon').glob('*.html'))):
        nimm('strom-daheim.de/' + str(f.relative_to(ROOT)), f.read_text(encoding='utf-8'))
    try:                                                    # Stil-Daheim liegt in einem anderen Repository: Seiten von der Website lesen
        sm = urllib.request.urlopen(urllib.request.Request('https://stil-daheim.de/sitemap.xml', headers=UA), timeout=30).read().decode('utf-8')
        for loc in re.findall(r'<loc>([^<]+)</loc>', sm):
            try:
                nimm(loc.replace('https://', ''), urllib.request.urlopen(urllib.request.Request(loc, headers=UA), timeout=30).read().decode('utf-8', 'replace'))
            except Exception as e:
                print('Seite nicht lesbar:', loc, e)
    except Exception as e:
        print('stil-daheim.de nicht erreichbar:', e)
    return wo


def pruefen(u):
    """Gibt (Adresse, Urteil, Hinweis) zurück. Urteil: ok, tot, unklar."""
    for versuch in range(2):
        try:
            r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=25); r.read(1)
            return u, 'ok', str(r.status)
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                return u, 'tot', 'Seite nicht gefunden (%d)' % e.code
            if versuch:
                return u, 'unklar', 'Antwort %d' % e.code
        except urllib.error.URLError as e:
            if isinstance(e.reason, socket.gaierror):
                return u, 'tot', 'Adresse existiert nicht'
            if versuch:
                return u, 'unklar', str(e.reason)[:80]
        except Exception as e:
            if versuch:
                return u, 'unklar', str(e)[:80]
    return u, 'unklar', ''


def main():
    wo = sammeln(); alt = json.loads(ZIEL.read_text(encoding='utf-8')) if ZIEL.exists() else {}
    verdacht_alt = set(alt.get('verdacht', [])) | {t['url'] for t in alt.get('tot', [])}
    with concurrent.futures.ThreadPoolExecutor(8) as ex:
        erg = list(ex.map(pruefen, sorted(wo)))
    tot = [{'url': u, 'grund': h, 'seiten': wo[u]} for u, urteil, h in erg if urteil == 'tot' and u in verdacht_alt]
    verdacht = sorted(u for u, urteil, h in erg if urteil == 'tot' and u not in verdacht_alt)
    unklar = sum(1 for _, urteil, _ in erg if urteil == 'unklar')
    seit = {t['url']: t.get('seit') for t in alt.get('tot', [])}; heute = datetime.date.today().isoformat()
    for t in tot:
        t['seit'] = seit.get(t['url']) or heute
    neu = {'hinweis': 'Vom Link-Wächter geschrieben (werkzeuge/linkcheck.py). tot = zweimal hintereinander nicht gefunden: bitte ersetzen oder entfernen. verdacht = heute zum ersten Mal nicht gefunden, noch abwarten.',
           'geprueft': len(erg), 'unklar': unklar, 'tot': tot, 'verdacht': verdacht}
    kern = lambda d: json.dumps({k: d.get(k) for k in ('tot', 'verdacht')}, sort_keys=True)
    if not ZIEL.exists() or kern(alt) != kern(neu):         # nur speichern, wenn sich an den Funden etwas ändert
        neu['stand'] = heute
        ZIEL.write_text(json.dumps(neu, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('%d Links geprüft: %d tot, %d Verdacht, %d unklar' % (len(erg), len(tot), len(verdacht), unklar))
    for t in tot:
        print('TOT', t['url'], '|', t['grund'], '|', ', '.join(t['seiten'][:3]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
