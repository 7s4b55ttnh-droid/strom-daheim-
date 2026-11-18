/* Strom-Daheim, Zusatzbausteine (Stile in mehr.css). Alles läuft im Browser, nichts wird übertragen.
   1. sdBild: Rechenergebnis als Bild speichern oder teilen. Der Knopf erscheint von selbst neben jedem „Ergebnis teilen“, wenn daneben Kennzahlen (.res) stehen.
   2. Schnell-Check „Lohnt sich das bei mir?“: Dialog mit drei Angaben, öffnet über jedes Element mit data-check. Rechnet mit dem Rechenkern des Planers (bkw-planer.js) und den Sonnendaten der Region.
   3. Balkon-Vorschau: <div id="bv"> im Planer. Fotos assets/bv-<ort>-<anzahl>.jpg (Beispielbilder, mit KI erstellt).
   4. Tausch-Rechner: Karte unter der Rangliste auf stromfresser.html. Liest Gerät, Verbrauch und Strompreis aus der Rangliste.
   5. Weitermachen: Hinweis für Wiederkehrer auf der Startseite, liest nur, welche Rechner im Browser einen Stand abgelegt haben. */
(function(){
'use strict';
var d=document;
function f(n,k){return n.toLocaleString('de-DE',{minimumFractionDigits:k||0,maximumFractionDigits:k||0})}
function zahl(t){var m=String(t).replace(/\./g,'').replace(',','.').match(/-?\d+(\.\d+)?/);return m?+m[0]:NaN}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
var I={bild:'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4v11m0 0-4-4m4 4 4-4M5 19h14"/></svg>',x:'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg>'};

/* ---------- 1. Ergebnis als Bild ---------- */
function umbruch(x,t,w){var out=[],z='';String(t).split(/\s+/).forEach(function(wort){var p=z?z+' '+wort:wort;if(x.measureText(p).width>w&&z){out.push(z);z=wort}else z=p});if(z)out.push(z);return out}
function sdBild(o,rueck){var W=1080,H=1350,c=d.createElement('canvas');c.width=W;c.height=H;var x=c.getContext('2d'),F='system-ui,-apple-system,"Segoe UI",Roboto,sans-serif',y=0,m=84;
 var g=x.createLinearGradient(0,0,W,H);g.addColorStop(0,'#16181d');g.addColorStop(1,'#0b0c0f');x.fillStyle=g;x.fillRect(0,0,W,H);
 x.fillStyle='#ffd60a';x.beginPath();x.moveTo(m+26,m);x.lineTo(m,m+44);x.lineTo(m+20,m+44);x.lineTo(m+14,m+78);x.lineTo(m+46,m+30);x.lineTo(m+25,m+30);x.closePath();x.fill();
 x.fillStyle='#f5f5f7';x.textBaseline='alphabetic';x.font='700 38px '+F;x.fillText('Strom-Daheim',m+64,m+52);
 y=m+170;x.font='700 62px '+F;umbruch(x,o.titel,W-2*m).slice(0,3).forEach(function(z){x.fillText(z,m,y);y+=74});
 var z0=o.zahlen[0];if(z0){y+=70;x.fillStyle='#ffd60a';x.font='800 150px '+F;var gr=150;while(x.measureText(z0[0]).width>W-2*m&&gr>70){gr-=10;x.font='800 '+gr+'px '+F}x.fillText(z0[0],m,y+gr*.62);y+=gr*.62+56;x.fillStyle='#f5f5f7';x.font='600 40px '+F;umbruch(x,z0[1],W-2*m).slice(0,2).forEach(function(z){x.fillText(z,m,y);y+=50})}
 y+=34;var rest=o.zahlen.slice(1,5),sp=(W-2*m-36)/2;rest.forEach(function(z,i){var cx=m+(i%2)*(sp+36),cy=y+Math.floor(i/2)*176;x.fillStyle='rgba(255,255,255,.07)';if(x.roundRect){x.beginPath();x.roundRect(cx,cy,sp,152,24);x.fill()}else x.fillRect(cx,cy,sp,152);
  x.fillStyle='#f5f5f7';x.font='700 50px '+F;var gr=50;while(x.measureText(z[0]).width>sp-48&&gr>28){gr-=4;x.font='700 '+gr+'px '+F}x.fillText(z[0],cx+24,cy+68);x.fillStyle='#b9b9c0';x.font='500 27px '+F;x.fillText(umbruch(x,z[1],sp-48)[0]||'',cx+24,cy+116)});
 y+=Math.ceil(rest.length/2)*176+30;
 if(o.text){x.fillStyle='#d2d2d7';x.font='500 33px '+F;var L=umbruch(x,o.text,W-2*m),max=Math.max(0,Math.floor((H-150-y)/46));L.slice(0,max).forEach(function(z,i){x.fillText(i===max-1&&L.length>max?z.replace(/\s*\S*$/,' …'):z,m,y+34);y+=46})}
 x.fillStyle='#8e8e93';x.font='500 28px '+F;x.fillText('strom-daheim.de · Richtwert aus dem Rechner, Stand '+new Date().toLocaleDateString('de-DE'),m,H-66);
 c.toBlob(function(bl){if(!bl){rueck('Das Bild ließ sich gerade nicht erstellen.');return}var datei=(o.datei||'strom-daheim-ergebnis')+'.png',fl=new File([bl],datei,{type:'image/png'});
  if(navigator.canShare&&navigator.canShare({files:[fl]})){navigator.share({files:[fl],title:o.titel}).then(function(){rueck('Geteilt.')},function(){rueck('')});return}
  var a=d.createElement('a');a.href=URL.createObjectURL(bl);a.download=datei;d.body.appendChild(a);a.click();a.remove();rueck('Gespeichert als '+datei+'.')},'image/png')}
window.sdBild=sdBild;
function bildKnoepfe(){[].forEach.call(d.querySelectorAll('.acts'),function(acts){var box=acts.parentElement,res=box&&box.querySelector('.res');if(!res||acts.querySelector('[data-bild]'))return;
  var b=d.createElement('button');b.type='button';b.className='abtn';b.setAttribute('data-bild','');b.innerHTML=I.bild+'Als Bild speichern';acts.appendChild(b);
  var st=d.createElement('p');st.className='hint';st.setAttribute('role','status');st.style.margin='0';st.hidden=true;acts.insertAdjacentElement('afterend',st);
  b.addEventListener('click',function(){var zahlen=[].map.call(res.children,function(k){var w=k.querySelector('b'),t=k.querySelector('span');return w&&w.textContent.trim()&&w.textContent.trim()!=='–'?[w.textContent.trim(),t?t.textContent.trim():'']:null}).filter(Boolean);
   if(!zahlen.length){st.hidden=false;st.textContent='Erst rechnen, dann speichern: Es steht noch kein Ergebnis da.';return}
   var hi=res.querySelector('.hi');if(hi){var w=hi.querySelector('b').textContent.trim();zahlen.sort(function(a,c){return (c[0]===w)-(a[0]===w)})}
   var v=box.querySelector('.verdict p'),h=d.querySelector('h1');sdBild({titel:h?h.textContent.trim():d.title,zahlen:zahlen,text:v?v.textContent.trim():'',datei:'strom-daheim-'+(location.pathname.replace(/^\/|\.html$/g,'')||'ergebnis')},function(t){st.hidden=!t;st.textContent=t})})})}

/* ---------- 2. Schnell-Check ---------- */
var CT=32,KOSTEN=350,WP=900;     /* wie die Voreinstellungen im Planer: 32 ct je kWh, 2 Module zu je 450 Wp, 100 € Wechselrichter + 2 × 125 € */
function kern(cb){if(window.BKW){cb();return}var s=d.createElement('script');s.src='/bkw-planer.js';s.onload=cb;s.onerror=function(){cb(1)};d.head.appendChild(s)}
var regionen={};
function region(plz,cb){var r=plz.slice(0,2);if(r==='11')r='10';if(regionen[r]){cb(regionen[r]);return}
 fetch('/assets/pv/'+r+'.json').then(function(q){if(!q.ok)throw 0;return q.json()}).then(function(j){regionen[r]=BKW.decode(j);cb(regionen[r])}).catch(function(){cb(null)})}
function rechne(daten,dir,kwh){var y=BKW.simulate(daten,{groups:[{wp:WP,tilt:90,azim:dir}],shade:{horizon:0,sky:1},cap:800,kwh:kwh,base:Math.round(kwh*0.038),presence:'teils',shift:false,bat:null,keep:false}).y;
 var y1=y.saved*CT/100,cum=0,pay=Infinity;for(var j=0;j<40;j++){var v=y1*Math.pow(1-0.005,j)*Math.pow(1+0.02,j);if(pay===Infinity&&cum+v>=KOSTEN&&v>0)pay=j+(KOSTEN-cum)/v;cum+=v}
 return {eur:y1,pv:y.pv,self:y.self,pay:pay}}
window.sdCheck={rechne:function(plz,dir,kwh,cb){kern(function(){region(plz,function(dt){cb(dt?rechne(dt,dir,kwh):null)})})}};
var dlg=null,Z={plz:'',dir:0,kwh:2500},lauf=0;
function check(){if(!dlg){dlg=d.createElement('dialog');dlg.className='mx-dlg';dlg.setAttribute('aria-labelledby','mx-h');
  try{var s=JSON.parse(localStorage.getItem('bkwp')||'null');if(s&&/^\d{5}$/.test(s.plz||''))Z.plz=s.plz}catch(e){}
  dlg.innerHTML='<div class="mx-dlg-in"><button type="button" class="mx-x" aria-label="Schließen">'+I.x+'</button><h2 id="mx-h">Lohnt sich ein Balkonkraftwerk bei mir?</h2><p class="mx-sub">Drei Angaben, eine Zahl. Gerechnet mit den Sonnendaten deiner Region.</p>'+
   '<div class="mx-q"><label for="mx-plz">1. Deine Postleitzahl</label><input type="text" id="mx-plz" inputmode="numeric" maxlength="5" autocomplete="postal-code" value="'+Z.plz+'"></div>'+
   '<div class="mx-q"><b id="mx-l2">2. Wohin zeigt dein Balkon?</b><div class="mx-chips" role="group" aria-labelledby="mx-l2" data-k="dir"><button type="button" data-v="0" aria-pressed="true">Süden</button><button type="button" data-v="45" aria-pressed="false">Südost oder Südwest</button><button type="button" data-v="90" aria-pressed="false">Osten oder Westen</button><button type="button" data-v="180" aria-pressed="false">Norden</button></div></div>'+
   '<div class="mx-q"><b id="mx-l3">3. Dein Stromverbrauch im Jahr</b><div class="mx-chips" role="group" aria-labelledby="mx-l3" data-k="kwh"><button type="button" data-v="1500" aria-pressed="false">1.500 kWh</button><button type="button" data-v="2500" aria-pressed="true">2.500 kWh</button><button type="button" data-v="3500" aria-pressed="false">3.500 kWh</button><button type="button" data-v="4500" aria-pressed="false">4.500 kWh</button></div><small>Steht auf deiner Jahresabrechnung. Ungefähr reicht.</small></div>'+
   '<div class="mx-out leer" aria-live="polite"><span>Gib deine Postleitzahl ein, dann steht hier dein Ergebnis.</span></div>'+
   '<div class="mx-go"><a class="mx-btn" href="/balkonkraftwerk-planer.html">Genau planen</a><a class="mx-btn ghost" href="/#vergleich" data-set hidden>Passende Sets ansehen</a><button type="button" class="mx-btn ghost" data-b hidden>'+I.bild+'Als Bild speichern</button></div></div>';
  d.body.appendChild(dlg);var out=dlg.querySelector('.mx-out'),go=dlg.querySelector('.mx-go a'),bb=dlg.querySelector('[data-b]'),sets=dlg.querySelector('[data-set]'),letzt=null;
  function neu(){var plz=Z.plz;go.href='/balkonkraftwerk-planer.html'+(/^\d{5}$/.test(plz)?'?p='+plz+'&n=2&a='+Z.dir+'&v='+Z.kwh:'');
   if(!/^\d{5}$/.test(plz)){out.className='mx-out leer';out.innerHTML='<span>Gib deine Postleitzahl ein, dann steht hier dein Ergebnis.</span>';bb.hidden=sets.hidden=true;return}
   var nr=++lauf;out.className='mx-out leer';out.innerHTML='<span>Einen Moment, ich hole die Sonnendaten …</span>';
   window.sdCheck.rechne(plz,Z.dir,Z.kwh,function(r){if(nr!==lauf)return;if(!r){out.innerHTML='<span>Diese Postleitzahl kennen wir nicht. Stimmen die ersten beiden Ziffern?</span>';bb.hidden=sets.hidden=true;return}
    letzt=r;var jahre=isFinite(r.pay)?f(r.pay,1)+' Jahren':'mehr als 40 Jahren',lang=r.pay>12;out.className='mx-out';
    out.innerHTML='<b>'+f(Math.round(r.eur))+' €</b><span>sparst du etwa im Jahr</span><p>Zwei Module mit zusammen 900 Wp senkrecht am Geländer liefern bei dir rund '+f(Math.round(r.pv/10)*10)+' kWh, davon nutzt du etwa '+f(Math.round(r.self/10)*10)+' kWh selbst. Bezahlt nach etwa '+jahre+', gerechnet mit '+CT+' ct je kWh und '+KOSTEN+' € Anschaffung.'+(lang?' Das rechnet sich hier nur langsam.':'')+'</p>';bb.hidden=sets.hidden=false})}
  dlg.addEventListener('click',function(ev){var b=ev.target.closest('.mx-chips button');if(b){var g=b.parentElement;[].forEach.call(g.children,function(k){k.setAttribute('aria-pressed',k===b?'true':'false')});Z[g.dataset.k]=+b.dataset.v;neu();return}
   if(ev.target.closest('.mx-x')||ev.target===dlg||ev.target.closest('[data-set]')){dlg.close();return}
   if(ev.target.closest('[data-b]')&&letzt)sdBild({titel:'Lohnt sich ein Balkonkraftwerk bei mir?',zahlen:[[f(Math.round(letzt.eur))+' €','sparst du etwa im Jahr'],[f(Math.round(letzt.pv/10)*10)+' kWh','Solarstrom im Jahr'],[isFinite(letzt.pay)?f(letzt.pay,1)+' Jahre':'über 40 Jahre','bis die Anlage bezahlt ist']],text:'Zwei Module mit 900 Wp am Geländer, Balkon nach '+({0:'Süden',45:'Südost oder Südwest',90:'Osten oder Westen',180:'Norden'})[Z.dir]+', Postleitzahl '+Z.plz+', '+f(Z.kwh)+' kWh Verbrauch im Jahr.',datei:'strom-daheim-balkonkraftwerk'},function(t){if(t){var p=out.querySelector('p');if(p)p.insertAdjacentText('beforeend',' '+t)}})});
  dlg.querySelector('#mx-plz').addEventListener('input',function(){this.value=this.value.replace(/\D/g,'').slice(0,5);Z.plz=this.value;neu()});dlg._neu=neu}
 if(dlg.showModal)dlg.showModal();else dlg.setAttribute('open','');dlg._neu()}
d.addEventListener('click',function(ev){var t=ev.target.closest&&ev.target.closest('[data-check]');if(!t)return;ev.preventDefault();check()});

/* ---------- 3. Balkon-Vorschau ---------- */
function vorschau(){var el=d.getElementById('bv');if(!el)return;
 var ORT={balkon:{name:'Am Balkongeländer',n:[0,1,2],tilt:90,alt:'Balkon eines Mehrfamilienhauses',text:['So sieht der Balkon ohne Module aus.','Ein Modul senkrecht am Geländer. Der einfachste Einstieg: braucht keinen Platz auf dem Balkon.','Zwei Module senkrecht am Geländer. Die übliche Größe für ein Balkonkraftwerk.']},
  garten:{name:'Im Garten aufgeständert',n:[0,2,4],tilt:30,alt:'Garten mit Terrasse hinter einem Reihenhaus',text:['So sieht der Garten ohne Module aus.','Zwei Module auf Ständern, etwa 30 Grad geneigt. Bringt im Sommer mehr als senkrecht am Geländer, braucht aber Platz und einen sicheren Stand gegen Wind.','Vier Module in einer Reihe. Was bei dieser Größe gilt, steht weiter unten bei „Was erlaubt ist“.']}};
 var ort='balkon',idx=2;
 el.innerHTML='<figure><img class="alt" alt="" decoding="async"><img class="neu" alt="" decoding="async"></figure><div class="mx-bv-r"><div><span id="bv-l1">Wo?</span><div class="mx-chips" role="group" aria-labelledby="bv-l1" data-k="ort"></div></div><div><span id="bv-l2">Wie viele Module?</span><div class="mx-chips" role="group" aria-labelledby="bv-l2" data-k="n"></div></div></div><p class="mx-bv-t" aria-live="polite"></p><div class="mx-go"><a class="mx-btn" href="#planer">Mit dieser Aufstellung rechnen</a><a class="mx-btn ghost" href="/#vergleich">Welches Set kaufen?</a></div>';
 var alt=el.querySelector('img.alt'),neu=el.querySelector('img.neu'),c1=el.querySelector('[data-k="ort"]'),c2=el.querySelector('[data-k="n"]'),txt=el.querySelector('.mx-bv-t'),go=el.querySelector('.mx-go a');
 function wort(n){return n===0?'Ohne':n===1?'1 Modul':n+' Module'}
 function zeig(erst){var O=ORT[ort],n=O.n[idx],src='/assets/bv-'+ort+'-'+n+'.jpg',a=O.alt+(n?', '+wort(n).replace('Modul','Solarmodul')+' '+(ort==='balkon'?'am Geländer':'auf dem Rasen'):', ohne Solarmodule')+'. Beispielbild';
  c1.innerHTML=Object.keys(ORT).map(function(k){return '<button type="button" data-v="'+k+'" aria-pressed="'+(k===ort)+'">'+ORT[k].name+'</button>'}).join('');
  c2.innerHTML=O.n.map(function(m,i){return '<button type="button" data-v="'+i+'" aria-pressed="'+(i===idx)+'">'+wort(m)+'</button>'}).join('');
  txt.textContent=O.text[idx];go.hidden=!n;go.href='?n='+Math.min(4,n||2)+'&t='+O.tilt+'#planer';
  if(erst){alt.src=src;alt.alt=a;return}var b=new Image();b.onload=function(){neu.src=src;neu.alt=a;neu.classList.add('da');setTimeout(function(){alt.src=src;alt.alt=a;neu.classList.remove('da')},950)};b.src=src}
 el.addEventListener('click',function(ev){var b=ev.target.closest('.mx-chips button');if(!b)return;var k=b.parentElement.dataset.k;if(k==='ort'){ort=b.dataset.v;idx=ORT[ort].n.length-2}else idx=+b.dataset.v;zeig();var s=el.querySelector('[data-k="'+k+'"] [aria-pressed="true"]');if(s)s.focus()});
 zeig(true);window.sdVorschau={stand:function(){return [ort,ORT[ort].n[idx],go.getAttribute('href')]}}}

/* ---------- 4. Tausch-Rechner ---------- */
function tausch(){var rank=d.getElementById('rank'),gp=d.getElementById('gp');if(!rank||!gp)return;var mods=rank.closest('.card');if(!mods)return;
 var k=d.createElement('div');k.className='card mx-t';k.innerHTML='<h3>Lohnt sich ein neues Gerät?</h3><p>Trag ein, was das neue Gerät laut Energielabel im Jahr braucht und was es kostet.</p><div class="mx-t-f"><label class="voll">Welches Gerät willst du ersetzen?<select id="mx-t-g"></select></label><label>Neues Gerät, kWh im Jahr<input id="mx-t-k" type="text" inputmode="decimal" value="100"></label><label>Kaufpreis in €<input id="mx-t-p" type="text" inputmode="decimal" value="500"></label></div><p class="mx-t-o" aria-live="polite"></p><small>Auf dem Energielabel steht der Verbrauch bei Kühl- und Gefriergeräten pro Jahr, bei Waschmaschine und Spülmaschine je 100 Durchgänge und beim Fernseher je 1.000 Stunden. Rechne das auf deine Nutzung um.</small>';
 mods.insertAdjacentElement('afterend',k);var sel=k.querySelector('select'),out=k.querySelector('.mx-t-o'),wahl='';
 var kauf=d.createElement('p');kauf.className='mx-t-k';out.insertAdjacentElement('afterend',kauf);
 function lies(){return [].map.call(rank.querySelectorAll('.mrow'),function(r){var n=r.querySelector('.tp b'),s=r.querySelector('.st');return n&&s?[n.textContent.trim(),zahl(s.textContent)]:null}).filter(Boolean)}
 function neu(){var R=lies(),pr=zahl((gp.textContent.match(/bei\s+([\d.,]+)\s*ct/)||[])[1]||'35')/100;if(!R.length){k.hidden=true;return}k.hidden=false;
  if(!R.some(function(r){return r[0]===wahl}))wahl=R[0][0];
  kauf.innerHTML='<a href="https://www.amazon.de/s?k='+encodeURIComponent(wahl+' sparsam').replace(/%20/g,'+')+'&tag=stromdaheim-21" target="_blank" rel="sponsored nofollow noopener">Sparsame Geräte ansehen: '+esc(wahl)+'</a><span class="mx-anz">Anzeige</span>';sel.innerHTML=R.map(function(r){return '<option'+(r[0]===wahl?' selected':'')+'>'+esc(r[0])+'</option>'}).join('');
  var alt=R.filter(function(r){return r[0]===wahl})[0][1],nk=zahl(k.querySelector('#mx-t-k').value),p=zahl(k.querySelector('#mx-t-p').value);
  if(!isFinite(nk)||nk<0){out.textContent='Trag den Jahresverbrauch des neuen Geräts ein.';return}var spar=(alt-nk)*pr;
  if(spar<=0){out.textContent='Das neue Gerät braucht nicht weniger als dein jetziges ('+f(Math.round(alt))+' kWh im Jahr). Ein Tausch spart keinen Strom.';return}
  out.textContent='Dein Gerät braucht jetzt rund '+f(Math.round(alt))+' kWh im Jahr. Das neue spart etwa '+f(Math.round(spar))+' € im Jahr.'+(isFinite(p)&&p>0?' Der Kaufpreis ist nach rund '+f(p/spar,p/spar<10?1:0)+' Jahren wieder drin, bei gleichbleibendem Strompreis.':'')}
 sel.addEventListener('change',function(){wahl=sel.value;neu()});k.addEventListener('input',function(ev){if(ev.target!==sel)neu()});
 new MutationObserver(neu).observe(rank,{childList:true,subtree:true,characterData:true});new MutationObserver(neu).observe(gp,{childList:true,characterData:true,subtree:true});neu()}

/* ---------- 5. Weitermachen ---------- */
function weiter(){var ziel=d.querySelector('#alles .wrap');if(!ziel||!d.getElementById('s1'))return;var L=[['bkwp','/balkonkraftwerk-planer.html','Dein Balkonkraftwerk-Plan'],['sdwl','/was-lohnt-sich.html','Dein Plan in 5 Fragen'],['sfr','/stromfresser.html','Deine Stromfresser'],['zaehler','/zaehlerstand.html','Deine Zählerstände']],h='';
 try{L.forEach(function(x){if(localStorage.getItem(x[0]))h+='<a href="'+x[1]+'">'+x[2]+'</a>'})}catch(e){}
 if(!h)return;var b=d.createElement('div');b.className='mx-w';b.innerHTML='<p><b>Schön, dass du wieder da bist.</b> Mach weiter, wo du warst:</p><div>'+h+'</div>';ziel.insertBefore(b,ziel.firstChild)}

function los(){bildKnoepfe();vorschau();tausch();weiter()}
if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',los);else los();
})();
