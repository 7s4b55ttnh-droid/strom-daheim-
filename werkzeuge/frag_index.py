"""Schreibt frag.json: alle geprüften Fragen und Antworten der Website (aus den FAQ-Angaben jeder Seite) plus die Kurzantwort jeder Seite.
Daraus beantwortet frag.js Fragen in der Suche und im Kasten „Frag den Ratgeber“. Es wird nichts erfunden: Jede Antwort steht so auf einer Seite.
Aufruf: python3 frag_index.py <Ordner mit den fertigen HTML-Seiten> [Unterordner ...]"""
import json, re, sys, html, pathlib


def text(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s))).replace('\xa0', ' ').strip()


def seite(f, url):
    t = f.read_text(encoding='utf-8')
    out = []
    m = re.search(r'<title>(.*?)</title>', t, re.S)
    titel = text(m.group(1)).split(' – ')[0].split(' | ')[0] if m else url
    h1 = re.search(r'<h1[^>]*>(.*?)</h1>', t, re.S)
    k = re.search(r'<div class="kurz"[^>]*>.*?<p>(.*?)</p>', t, re.S)
    if k and h1:
        out.append({'q': text(h1.group(1)), 'a': text(k.group(1)), 'u': url, 't': titel, 'k': 1})
    for blob in re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', t, re.S):
        try:
            d = json.loads(blob)
        except Exception:
            continue
        knoten = d.get('@graph', [d]) if isinstance(d, dict) else d
        for n in knoten:
            if isinstance(n, dict) and n.get('@type') == 'FAQPage':
                for q in n.get('mainEntity', []):
                    a = (q.get('acceptedAnswer') or {}).get('text', '')
                    if q.get('name') and a:
                        out.append({'q': text(q['name']), 'a': text(a), 'u': url, 't': titel})
    return out


def main(root, unter=()):
    root = pathlib.Path(root)
    alle, gesehen = [], set()
    dateien = [(f, '/' + f.name) for f in sorted(root.glob('*.html'))]
    for u in unter:
        dateien += [(f, '/%s/%s' % (u, f.name)) for f in sorted((root / u).glob('*.html'))]
    for f, url in dateien:
        if f.name in ('impressum.html', 'datenschutz.html', '404.html', 'offline.html'):
            continue
        for e in seite(f, '/' if url == '/index.html' else url):
            key = (e['q'].lower(), e['u'])
            if key not in gesehen:
                gesehen.add(key); alle.append(e)
    (root / 'frag.json').write_text(json.dumps(alle, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print('frag.json', len(alle), 'Antworten aus', len({e['u'] for e in alle}), 'Seiten')
    return len(alle)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
