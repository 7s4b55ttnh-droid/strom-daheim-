"""KI-Kennzeichnung für Bilder, die die Seite verlassen (Teilen-Bilder assets/og/*.jpg, Pins assets/pins/*.jpg).

Setzt oben rechts eine kleine Marke "KI-generiert" ins Bild und schreibt die Kennzeichnung zusätzlich
maschinenlesbar in die Datei (XMP, IPTC DigitalSourceType trainedAlgorithmicMedia; Pinterest liest das).
Bereits gestempelte Dateien werden erkannt und übersprungen, doppelt stempeln geht also nicht.

Aufruf:  python3 ki_stempel.py <datei.jpg> [weitere ...]
Im Code:  from ki_stempel import stempel; stempel('assets/og/x.jpg')

Auf den Webseiten selbst setzt site.js die Marke über jedes Foto (Klasse .ki-marke), dort NICHT ins Bild stempeln:
Die Fotos werden je nach Bildschirm beschnitten, eine eingebrannte Ecke wäre oft abgeschnitten.
"""
import sys
from PIL import Image, ImageDraw, ImageFont

TEXT = 'Mit KI erstellt'
MERKER = 'trainedAlgorithmicMedia'
XMP = ('<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>'
       '<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
       '<rdf:Description rdf:about="" xmlns:Iptc4xmpExt="http://iptc.org/std/Iptc4xmpExt/2008-02-29/" '
       'xmlns:dc="http://purl.org/dc/elements/1.1/" '
       'Iptc4xmpExt:DigitalSourceType="http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia">'
       '<dc:description><rdf:Alt><rdf:li xml:lang="x-default">KI-generiertes Beispielbild</rdf:li></rdf:Alt></dc:description>'
       '</rdf:Description></rdf:RDF></x:xmpmeta><?xpacket end="w"?>')
SCHRIFTEN = ['/usr/share/fonts/opentype/inter/Inter-SemiBold.otf',
             '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']


def schon_gestempelt(pfad):
    with open(pfad, 'rb') as f:
        return MERKER.encode() in f.read()


def _schrift(px):
    for s in SCHRIFTEN:
        try:
            return ImageFont.truetype(s, px)
        except OSError:
            pass
    return ImageFont.load_default()


def stempel(pfad, ziel=None, qualitaet=86):
    """Marke oben rechts einbrennen und XMP setzen. Gibt False zurück, wenn die Datei schon gestempelt war."""
    ziel = ziel or pfad
    if ziel == pfad and schon_gestempelt(pfad):
        return False
    im = Image.open(pfad).convert('RGB')
    w, h = im.size
    px = max(14, round(min(w, h * 1.6) * 0.022))          # 1200x630 -> 22 px, 1000x1500 -> 22 px
    f = _schrift(px)
    l, t, r, b = f.getbbox(TEXT)
    pad_x, pad_y, rand = round(px * .6), round(px * .38), round(px * 1.1)
    bw, bh = (r - l) + 2 * pad_x, (b - t) + 2 * pad_y
    x0, y0 = w - rand - bw, rand
    ebene = Image.new('RGBA', im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ebene)
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), radius=bh // 2, fill=(12, 12, 12, 175))
    d.text((x0 + pad_x - l, y0 + pad_y - t), TEXT, font=f, fill=(255, 255, 255, 240))
    im = Image.alpha_composite(im.convert('RGBA'), ebene).convert('RGB')
    im.save(ziel, quality=qualitaet, optimize=True, progressive=True, xmp=XMP.encode('utf-8'))
    return True


if __name__ == '__main__':
    neu = sum(stempel(p) for p in sys.argv[1:])
    print('gestempelt: %d, schon vorher: %d' % (neu, len(sys.argv[1:]) - neu))
