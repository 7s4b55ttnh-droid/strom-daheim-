/* Solar-Atlas: rechnet für jede Postleitregion die Kennzahlen aus den Sonnendaten (assets/pv) und schreibt atlas.json.
   Aufruf im Ordner werkzeuge/pvdaten:  node atlas.js   (danach python3 ../solaratlas.py im Ordner werkzeuge)
   Dach-Werte: kWh je kWp und Jahr mit 10 % Systemverlusten, so wie PVGIS sie ausweist und wie gegenprobe.js sie prüft.
   Balkonkraftwerk: 900 Wp an 800 W Wechselrichter, gerechnet wie im Planer (Jahresertrag hinter dem Wechselrichter). */
const fs = require('fs'), path = require('path');
const { BKW } = require(path.join(__dirname, '..', '..', 'bkw-planer.js'));
const dir = path.join(__dirname, '..', '..', 'assets', 'pv'), MD = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
const TILT = [15, 35, 45], AZ = [[-90, 'Ost'], [-45, 'Südost'], [0, 'Süd'], [45, 'Südwest'], [90, 'West']];
const out = {};
for (const f of fs.readdirSync(dir).filter(x => /^\d\d\.json$/.test(x)).sort()) {
  const raw = JSON.parse(fs.readFileSync(path.join(dir, f))), data = BKW.decode(raw), plz = f.slice(0, 2);
  const kwp = (tilt, azim) => { const P = BKW.dcPower(data, { wp: 1000, tilt, azim }); let e = 0; for (let i = 0; i < 8760; i++) e += P[i]; return e / 1000 * 0.9; };
  const P = BKW.dcPower(data, { wp: 1000, tilt: 35, azim: 0 }), mon = []; let h = 0;
  for (const d of MD) { let s = 0; for (let i = 0; i < d * 24; i++) s += P[h++]; mon.push(Math.round(s / 1000 * 0.9 * 10) / 10); }
  const bkw = tilt => Math.round(BKW.simulate(data, { groups: [{ wp: 900, tilt, azim: 0 }], kwh: 2500, presence: 'teils' }).y.pv);
  out[plz] = { name: raw.name, lat: raw.lat, lon: raw.lon, ghi: raw.ghi, dach: Math.round(kwp(35, 0)), ow: Math.round((kwp(15, -90) + kwp(15, 90)) / 2), fass: Math.round(kwp(90, 0)),
    bkw90: bkw(90), bkw30: bkw(30), mon, tab: TILT.map(t => AZ.map(a => Math.round(kwp(t, a[0])))) };
}
fs.writeFileSync(path.join(__dirname, 'atlas.json'), JSON.stringify({ stand: new Date().toISOString().slice(0, 10), neigung: TILT, richtung: AZ.map(a => a[1]), regionen: out }));
const v = Object.values(out).map(x => x.dach); console.log(Object.keys(out).length, 'Regionen, Dach Süd 35°:', Math.min(...v), 'bis', Math.max(...v), 'kWh/kWp');
