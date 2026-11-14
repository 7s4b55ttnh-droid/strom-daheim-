/* Strom-Daheim als App: Dieser Helfer läuft nur, wenn die Seite auf dem Startbildschirm installiert wurde (Anmeldung in site.js).
   Er legt besuchte Seiten auf dem Gerät ab, damit sie auch ohne Netz öffnen. Es wird nichts übertragen und nichts ausgewertet.
   Regeln: Seiten, Stile, Skripte und Daten kommen immer zuerst frisch aus dem Netz (Ablage nur als Rückfall), Bilder zuerst aus der Ablage.
   Nach größeren Umbauten V hochzählen, dann räumt der Helfer die alte Ablage auf. */
var V = 'sd-1', START = ['/', '/site.css', '/site.js', '/favicon.svg'];
self.addEventListener('install', function (e) { e.waitUntil(caches.open(V).then(function (c) { return c.addAll(START); }).then(function () { return self.skipWaiting(); })); });
self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (ks) { return Promise.all(ks.filter(function (k) { return k !== V; }).map(function (k) { return caches.delete(k); })); }).then(function () { return self.clients.claim(); }));
});
function put(req, res) { if (res && res.ok && res.type === 'basic') { var copy = res.clone(); caches.open(V).then(function (c) { c.put(req, copy); }); } return res; }
function offline() {
  return new Response('<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Kein Netz</title>' +
    '<body style="font:17px/1.5 system-ui,sans-serif;margin:0;min-height:100vh;display:grid;place-items:center;background:#000;color:#f5f5f7;text-align:center;padding:24px;box-sizing:border-box">' +
    '<div><h1 style="font-size:1.6rem;margin:0 0 10px">Gerade kein Netz.</h1><p style="margin:0 0 18px;color:#9a9aa0">Seiten, die du schon geöffnet hast, gehen weiter. Diese hier war noch nicht dabei.</p>' +
    '<p><a href="/" style="color:#ffb81c;font-weight:600">Zur Startseite</a></p></div>', { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } });
}
self.addEventListener('fetch', function (e) {
  var req = e.request, url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== location.origin) return;
  if (/\.(?:jpe?g|png|webp|svg|gif|woff2?)$/i.test(url.pathname)) {          /* Bilder: zuerst die Ablage, im Hintergrund auffrischen */
    e.respondWith(caches.match(req).then(function (hit) {
      var net = fetch(req).then(function (res) { return put(req, res); }).catch(function () { return hit; });
      return hit || net;
    }));
    return;
  }
  e.respondWith(fetch(req).then(function (res) { return put(req, res); }).catch(function () {      /* alles andere: zuerst das Netz */
    return caches.match(req, { ignoreSearch: req.mode === 'navigate' }).then(function (hit) { return hit || (req.mode === 'navigate' ? offline() : Response.error()); });
  }));
});
