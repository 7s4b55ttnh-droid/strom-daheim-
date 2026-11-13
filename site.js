/* Strom-Daheim – gemeinsame Bedienung aller Seiten:
   Menü, Hell/Dunkel, Kopfzeile über dunklen Bildern, Nach oben, Teilen, Drucken. */
(function(){
  var d=document,root=d.documentElement,RM=matchMedia('(prefers-reduced-motion: reduce)').matches;
  function $(s,c){return (c||d).querySelector(s)}
  function $$(s,c){return Array.prototype.slice.call((c||d).querySelectorAll(s))}

  /* Zahlenfelder: Ein Feld vom Typ number verschluckt das deutsche Komma (aus 17,5 wird 175).
     Deshalb als Textfeld mit Zahlentastatur; die Rechner lesen Komma und Punkt. */
  $$('input.vin[type=number]').forEach(function(n){n.type='text';n.setAttribute('inputmode','decimal');n.setAttribute('autocomplete','off')});

  /* Hell/Dunkel: die Startseite hat einen eigenen Schalter, hier nur für die übrigen Seiten */
  var th=$('#th');
  function isDark(){var a=root.dataset.theme;return a?a==='dark':matchMedia('(prefers-color-scheme: dark)').matches}
  if(th&&!th.onclick){th.addEventListener('click',function(){var v=isDark()?'light':'dark';root.dataset.theme=v;try{localStorage.setItem('th',v)}catch(e){}})}

  /* Menü */
  var mb=$('#sh-mb'),sheet=$('#sh-sheet'),cl=$('#sh-close'),lastFocus=null;
  function openMenu(){if(!sheet)return;lastFocus=d.activeElement;sheet.hidden=false;mb.setAttribute('aria-expanded','true');root.style.overflow='hidden';(cl||sheet).focus()}
  function closeMenu(){if(!sheet||sheet.hidden)return;sheet.hidden=true;mb.setAttribute('aria-expanded','false');root.style.overflow='';if(lastFocus&&lastFocus.focus)lastFocus.focus()}
  if(mb&&sheet){
    mb.addEventListener('click',openMenu);
    if(cl)cl.addEventListener('click',closeMenu);
    sheet.addEventListener('click',function(e){if(e.target===sheet||e.target.closest('a'))closeMenu()});
    d.addEventListener('keydown',function(e){
      if(e.key==='Escape')closeMenu();
      if(e.key==='Tab'&&!sheet.hidden){var f=$$('a,button',sheet);if(!f.length)return;var a=f[0],z=f[f.length-1];
        if(e.shiftKey&&d.activeElement===a){e.preventDefault();z.focus()}else if(!e.shiftKey&&d.activeElement===z){e.preventDefault();a.focus()}}
    });
    /* Inhaltsverzeichnis "Auf dieser Seite" aus den Abschnitten mit Überschrift */
    var toc=$('#sh-toc'),wrap=$('#sh-toc-wrap'),seen={};
    if(toc&&wrap){
      $$('main [id]').forEach(function(el){
        if(!/^(SECTION|DIV|ARTICLE)$/.test(el.tagName)||/^s\d$/.test(el.id))return;
        var h=el.querySelector('h2');if(!h||seen[h.textContent])return;
        if(h.closest('[id]')!==el&&!el.contains(h))return;
        seen[h.textContent]=1;
        var a=d.createElement('a');a.href='#'+el.id;a.textContent=h.textContent.replace(/\s+/g,' ').replace(/\.$/,'').trim();toc.appendChild(a);
      });
      if(toc.children.length>1)wrap.hidden=false;
    }
  }

  /* Kopfzeile dunkel, solange sie über einem dunklen Bild liegt */
  var sh=$('#sh'),darks=$$('.scene,.hero,.pic'),tick=0;
  function hdr(){tick=0;if(!sh)return;var y=52,on=false;for(var i=0;i<darks.length;i++){var r=darks[i].getBoundingClientRect();if(r.top<=y&&r.bottom>y){on=true;break}}sh.classList.toggle('ondark',on)}

  /* Nach oben */
  var tt=d.createElement('button');tt.className='totop';tt.type='button';tt.setAttribute('aria-label','Nach oben');
  tt.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 19V5M5 12l7-7 7 7"/></svg>';d.body.appendChild(tt);
  tt.addEventListener('click',function(){scrollTo({top:0,behavior:RM?'auto':'smooth'});var s=$('.skip');if(s)s.blur()});
  function onScroll(){if(!tick){tick=requestAnimationFrame(function(){hdr();tt.classList.toggle('on',scrollY>innerHeight*1.5)})}}
  addEventListener('scroll',onScroll,{passive:true});addEventListener('resize',onScroll);hdr();onScroll();

  /* Hinweis */
  var toastEl=null,toastT=0;
  function toast(msg){if(!toastEl){toastEl=d.createElement('div');toastEl.className='toast';toastEl.setAttribute('role','status');d.body.appendChild(toastEl)}
    toastEl.textContent=msg;toastEl.classList.add('on');clearTimeout(toastT);toastT=setTimeout(function(){toastEl.classList.remove('on')},2600)}
  window.__toast=toast;

  /* Teilen: Text aus dem Ergebnis-Element plus Link zur Seite */
  d.addEventListener('click',function(e){
    var b=e.target.closest('[data-share]');if(!b)return;
    var src=d.getElementById(b.getAttribute('data-share')),sec=b.closest('[id]');
    var url=location.origin+location.pathname+(sec?'#'+sec.id:'');
    var text=(src?src.innerText.replace(/\s+/g,' ').trim():d.title)+' Rechne selbst nach:';
    if(navigator.share){navigator.share({title:d.title,text:text,url:url}).catch(function(){});return}
    var all=text+' '+url;
    if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(all).then(function(){toast('Ergebnis und Link kopiert')},function(){toast('Kopieren nicht möglich')})}
    else{toast('Kopieren nicht möglich')}
  });

  /* Drucken: vorher alle Aufklapptexte öffnen */
  d.addEventListener('click',function(e){if(e.target.closest('[data-print]'))print()});
  var closed=[];
  addEventListener('beforeprint',function(){closed=$$('details:not([open])');closed.forEach(function(x){x.open=true})});
  addEventListener('afterprint',function(){closed.forEach(function(x){x.open=false});closed=[]});
})();

/* Bewegung: Auswahl für Strom-Daheim */
window.__MOTION={reveal:'.card,.item,.hub a,.rows a,ol.steps>li,.tbl,.note,.res>div,.mods',count:'.opt .kw,.res b',tick:'.res b,.kpi b,#k1,#k2,#k3,#k4',
 extra:function(io){var H=innerHeight,A=[].filter.call(document.querySelectorAll('main>section:not(.scene)'),function(s){return s.getBoundingClientRect().top>=H});A.forEach(function(s){s.classList.add('ln');io.observe(s)})}};
/* Bewegung: Inhalte gleiten beim Scrollen sanft ins Bild, Ergebniszahlen zählen einmal hoch.
   Aus bei „Bewegung reduzieren“. Was beim Laden schon sichtbar ist, bleibt ruhig (schnelles Laden). */
(function(){
  if(!('IntersectionObserver' in window)||matchMedia('(prefers-reduced-motion: reduce)').matches)return;
  var C=window.__MOTION||{},d=document,H=innerHeight;
  function ready(f){d.readyState==='loading'?d.addEventListener('DOMContentLoaded',f):f()}
  function count(el){var t=el.textContent,m=t.match(/^(\D*?)(\d{1,3}(?:\.\d{3})+|\d+)(,\d+)?(\D*)$/);
    if(!m||/[–-]/.test(t))return;var dec=m[3]?m[3].length-1:0,v=parseFloat((m[2]+(m[3]||'')).replace(/\./g,'').replace(',','.'));
    if(!(v>0))return;var t0=performance.now(),last=t;el.__c=t0+900;
    (function step(n){if(el.textContent!==last)return;var p=Math.min(1,(n-t0)/700),e=1-Math.pow(1-p,3);
      last=m[1]+(v*e).toLocaleString('de-DE',{minimumFractionDigits:dec,maximumFractionDigits:dec})+m[4];if(p>=1)last=t;el.textContent=last;if(p<1)requestAnimationFrame(step)})(t0)}
  ready(function(){
    var io=new IntersectionObserver(function(es){es.forEach(function(e){if(!e.isIntersecting)return;var el=e.target;io.unobserve(el);
      el.classList.add('in');if(el.classList.contains('rv'))setTimeout(function(){el.classList.remove('rv','in');el.style.removeProperty('--rd')},1400);if(el.__cnt)el.__cnt.forEach(count);
      if(C.onIn)C.onIn(el)})},{rootMargin:'0px 0px -8% 0px',threshold:.08});
    /* Erst alles messen, dann ändern: verhindert wiederholtes Neuberechnen des Layouts */
    var L=[].filter.call(d.querySelectorAll(C.reveal||''),function(el){if(el.closest('.hero,.hd,.sh,.sh-sheet,.sheet-m,header,footer'))return false;
      var po=getComputedStyle(el.parentElement).overflowX;return po!=='auto'&&po!=='scroll'&&el.getBoundingClientRect().top>=H});
    L.forEach(function(el){var sib=0,p=el.previousElementSibling;while(p&&sib<5){if(p.matches(C.reveal))sib++;p=p.previousElementSibling}el.__rd=sib*70;
      if(C.count){var cs=[].slice.call(el.querySelectorAll(C.count));if(el.matches(C.count))cs.push(el);if(cs.length)el.__cnt=cs}});
    L.forEach(function(el){el.style.setProperty('--rd',el.__rd+'ms');el.classList.add('rv');io.observe(el)});
    if(C.extra)C.extra(io);
  });
})();

/* Black-Friday-Leiste: erscheint bis Cyber Monday (30.11.2026), danach automatisch weg. Kann geschlossen werden. */
(()=>{try{if(Date.now()>=Date.parse('2026-12-01T00:00:00+01:00')||/black-friday/.test(location.pathname)||localStorage.getItem('bf26')==='x')return}catch(e){}
const h=document.getElementById('sh');if(!h)return;
const n=Date.now(),bf=Date.parse('2026-11-27T00:00:00+01:00'),d=Math.ceil((bf-n)/864e5);
const t=d>1?'Black Friday in '+d+' Tagen':d===1?'Morgen ist Black Friday':n<Date.parse('2026-11-28T00:00:00+01:00')?'Heute ist Black Friday':'Black Week bis Cyber Monday';
const b=document.createElement('div');b.className='bfbar';
b.innerHTML='<a href="/black-friday.html"><b>'+t+'</b><span class="bfx"> · echte Angebote erkennen</span> <span aria-hidden="true">→</span></a><button type="button" aria-label="Black-Friday-Hinweis schließen">✕</button>';
b.querySelector('button').addEventListener('click',()=>{b.remove();try{localStorage.setItem('bf26','x')}catch(e){}});
h.appendChild(b);document.documentElement.classList.add('bf-on');b.querySelector('button').addEventListener('click',()=>document.documentElement.classList.remove('bf-on'))})();

/* Suche im Menü (Index: /suche.json, wird beim Öffnen geladen) */
(()=>{const top=document.querySelector('#sh-sheet .sh-top');if(!top)return;
const w=document.createElement('div');w.className='sq';w.setAttribute('role','search');
w.innerHTML='<label class="vh" for="sq-in">Ratgeber durchsuchen</label><input id="sq-in" type="search" placeholder="Suchen, z. B. Kühlschrank" autocomplete="off" enterkeyhint="search"><ul id="sq-out" aria-live="polite"></ul>';
top.insertAdjacentElement('afterend',w);
const inp=w.querySelector('input'),out=w.querySelector('ul');let idx=null;
const norm=s=>s.toLowerCase().replace(/ä/g,'ae').replace(/ö/g,'oe').replace(/ü/g,'ue').replace(/ß/g,'ss');
const load=()=>idx?Promise.resolve(idx):fetch('/suche.json').then(r=>r.json()).then(j=>(idx=j.map(e=>Object.assign(e,{n:norm(e.t+' '+e.d+' '+e.k)}))));
inp.addEventListener('focus',load,{once:true});
inp.addEventListener('input',()=>{const q=norm(inp.value.trim());if(q.length<2){out.innerHTML='';return}
load().then(L=>{const ws=q.split(/\s+/);const r=L.filter(e=>ws.every(x=>e.n.includes(x))).sort((a,b)=>(norm(b.t).includes(ws[0])?1:0)-(norm(a.t).includes(ws[0])?1:0)).slice(0,8);
out.innerHTML=r.length?r.map(e=>'<li><a href="'+e.u+'"><b>'+e.t.replace(/</g,'&lt;')+'</b><small>'+e.d.slice(0,90).replace(/</g,'&lt;')+'…</small></a></li>').join(''):'<li class="none">Nichts gefunden. Probier ein anderes Wort.</li>'})});})();

/* ===== Seit 11.11.2026 ===== */
/* Seitenübergang: Seiten blenden weich ineinander, das angetippte Kachelbild wächst zum Titelbild der Zielseite
   (View Transitions; Browser ohne diese Technik wechseln wie bisher). Regeln dazu in site.css. */
(function(){
  if(!('onpagereveal' in window)||!window.CSS||!CSS.supports('view-transition-name','x'))return;
  var d=document,cur=null,HS=window.__VTHERO||'.hero';
  function hero(){return d.querySelector(HS)}
  function clear(){if(cur){cur.style.viewTransitionName='';cur=null}}
  function thumb(a){return a.querySelector('.ic.th,picture,img')}
  function mark(el){clear();var h=hero();if(h)h.style.viewTransitionName='none';el.style.viewTransitionName='vt-hero';cur=el}
  d.addEventListener('click',function(e){
    var a=e.target.closest&&e.target.closest('a[href]');
    if(!a||a.target||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey||a.origin!==location.origin||a.pathname===location.pathname)return;
    var h=hero();if(h&&h.contains(a))return;
    var t=thumb(a);if(t)mark(t);else clear();
  },true);
  addEventListener('pagereveal',function(e){
    var h=hero();if(h)h.style.viewTransitionName='';
    if(!e.viewTransition){clear();return}
    if(!h){var f=window.navigation&&navigation.activation&&navigation.activation.from;
      if(f){try{var p=new URL(f.url).pathname,L=d.querySelectorAll('a[href="'+p+'"],a[href="'+p.slice(1)+'"]');
        for(var i=0;i<L.length;i++){var t=thumb(L[i]);if(!t)continue;var r=t.getBoundingClientRect();
          if(r.width>0&&r.bottom>0&&r.top<innerHeight){mark(t);break}}}catch(x){}}}
    e.viewTransition.finished.then(clear,clear);
  });
})();

/* Vorladen: Der Browser holt eine Seite schon, wenn man den Finger auf den Link legt oder mit der Maus darüber bleibt (wo vorhanden). */
(function(){try{if(!(HTMLScriptElement.supports&&HTMLScriptElement.supports('speculationrules')))return;
  var s=document.createElement('script');s.type='speculationrules';
  s.textContent=JSON.stringify({prefetch:[{where:{and:[{href_matches:'/*'},{not:{href_matches:'/*.xml'}},{not:{href_matches:'/*.json'}}]},eagerness:'moderate'}]});
  document.head.appendChild(s)}catch(e){}})();

/* Rechner-Ergebnisse leuchten kurz in der Akzentfarbe auf, wenn sie sich durch eine Eingabe ändern. */
(function(){
  if(!('MutationObserver' in window)||!Element.prototype.animate||matchMedia('(prefers-reduced-motion: reduce)').matches)return;
  var sel=(window.__MOTION&&window.__MOTION.tick)||'.res b';
  addEventListener('load',function(){setTimeout(function(){
    var root=document.documentElement,V=(window.__MOTION&&window.__MOTION.tickVar)||'--sun';
    var mo=new MutationObserver(function(ms){var seen=[],now=performance.now();ms.forEach(function(m){
      var el=m.target.nodeType===1?m.target:m.target.parentElement;el=el&&el.closest(sel);
      if(!el||seen.indexOf(el)>=0||(el.__c||0)>now)return;seen.push(el);
      var c=getComputedStyle(root).getPropertyValue(V).trim();if(!c)return;
      if(el.__tk)el.__tk.cancel();el.__tk=el.animate([{color:c},{color:c,offset:.3},{}],{duration:800,easing:'ease-out'})})});
    [].forEach.call(document.querySelectorAll(sel),function(el){mo.observe(el,{childList:true,characterData:true,subtree:true})});
  },1500)});
})();

/* Mein Strompreis: Wer in einem Rechner seinen Preis einträgt, findet ihn in allen anderen Rechnern wieder.
   Gespeichert nur im Browser (localStorage "sp"), nichts wird übertragen. Gilt für Felder mit aria-label "Strompreis in …". */
(function(){
  var d=document,K='sp',busy=0,told=0,last=null;
  function F(){return [].slice.call(d.querySelectorAll('input.vin[aria-label^="Strompreis in"]'))}
  function num(v){v=parseFloat(String(v==null?'':v).replace(',','.'));return v>=5&&v<=150?Math.round(v*100)/100:null}
  function get(){try{return num(localStorage.getItem(K))}catch(e){return null}}
  function fm(v){return String(v).replace('.',',')}
  function say(m){if(window.__toast)window.__toast(m)}
  function apply(){var v=get(),f=F();if(!f.length)return;
    if(v!=null){busy=1;var ch=0;f.forEach(function(x){if(num(x.value)!==v){x.value=fm(v);x.dispatchEvent(new Event('input',{bubbles:true}));x.dispatchEvent(new Event('change',{bubbles:true}));ch=1}});busy=0;
      if(ch)say('Gerechnet wird mit deinem Strompreis: '+fm(v)+' ct')}
    last=num(f[0].value)}
  function watch(){if(busy)return;setTimeout(function(){var f=F();if(!f.length)return;var v=num(f[0].value);if(v==null||v===last)return;last=v;
    try{localStorage.setItem(K,v)}catch(e){return}
    if(!told){told=1;say('Gemerkt: '+fm(v)+' ct gilt jetzt in allen Rechnern')}},80)}
  addEventListener('load',function(){setTimeout(function(){apply();d.addEventListener('input',watch,true);d.addEventListener('change',watch,true);d.addEventListener('click',watch,true)},60)});
})();

/* KI-Kennzeichnung (seit 11.11.2026, Pflicht, Wunsch des Inhabers: dezent, aber klar). Läuft automatisch für alle Fotos aus assets/:
   - Foto in einer Link-Kachel (Galerie): keine Marke aufs Bild, sondern EINE Zeile über der Galerie (.ki-hinweis).
   - Foto in <figure> mit <figcaption>: Zusatz am Ende der Bildunterschrift (.ki-cap).
   - Alle anderen (Titelbild, Vorher/Nachher, Szenen): kleine Marke "Mit KI erstellt" in der Bildecke (.ki-marke).
   Nicht entfernen. Fotos immer als <img src="assets/..."> einbinden, nie als CSS-Hintergrund. */
(function(){
  var RX=/(^|\/)assets\/[^\/]+\.(jpe?g|webp|png)(\?|$)/i,list=[],T='Mit KI erstellt',G='Fotos: Beispielbilder, mit Hilfe von KI erstellt.',C='Beispielbild, mit Hilfe von KI erstellt.';
  function box(im){var a=im.parentElement;if(a&&a.tagName==='PICTURE')a=a.parentElement;return a}
  function put(m){var a=m.__a,im=m.__i,ar=a.getBoundingClientRect(),ir=im.getBoundingClientRect();
    if(!ir.width||!ar.width){m.hidden=true;return}m.hidden=false;
    m.style.right=(Math.max(0,ar.right-ir.right)-a.clientLeft+8)+'px';m.style.bottom=(Math.max(0,ar.bottom-ir.bottom)-a.clientTop+8)+'px'}
  function mark(im){if(im.__ki)return;var s=im.getAttribute('src')||'';if(!RX.test(s))return;im.__ki=1;
    var card=im.closest('a'),fig=im.closest('figure');
    if(card&&card.parentElement){var g=card.parentElement,p=g.previousElementSibling;
      if(!(p&&p.classList.contains('ki-hinweis'))){var h=document.createElement('p');h.className='ki-hinweis';h.textContent=G;g.parentNode.insertBefore(h,g)}return}
    var fc=fig&&fig.querySelector('figcaption');
    if(fc){if(!fc.querySelector('.ki-cap')){var c=document.createElement('span');c.className='ki-cap';c.textContent=(fc.textContent.trim()?' ':'')+C;fc.appendChild(c)}return}
    var a=box(im);if(!a||a.querySelector(':scope>.ki-marke'))return;
    if(getComputedStyle(a).position==='static')a.style.position='relative';
    var m=document.createElement('span');m.className='ki-marke';m.textContent=T;
    m.__a=a;m.__i=im;a.appendChild(m);list.push(m);put(m);
    if(window.ResizeObserver){var ro=new ResizeObserver(function(){put(m)});ro.observe(a);ro.observe(im)}
    im.addEventListener('load',function(){put(m)})}
  function all(){document.querySelectorAll('img').forEach(mark)}
  all();addEventListener('load',function(){all();list.forEach(put)});
  if(window.MutationObserver)new MutationObserver(all).observe(document.body,{childList:true,subtree:true});
})();

/* Vergleichsbalken (Design-Agent 13.11.2026): In .res[data-vs] bekommen die ersten beiden Ergebnisse je einen Balken,
   Länge im Verhältnis der beiden Zahlen. Nur wenn beide dieselbe Einheit haben; der größere Betrag ist sonnengelb.
   Rein optisch (aria-hidden), die Zahlen stehen daneben. */
(function(){
  var d=document,boxes=[].slice.call(d.querySelectorAll('.res[data-vs]'));if(!boxes.length)return;
  function parse(t){t=String(t||'').replace(/ /g,' ').trim();var m=t.match(/^[^\d-]*(-?[\d.]+(?:,\d+)?)\s*(.*)$/);if(!m)return null;
    var v=parseFloat(m[1].replace(/\./g,'').replace(',','.'));return isNaN(v)?null:{v:Math.abs(v),u:m[2].trim()}}
  boxes.forEach(function(box){
    var items=[].slice.call(box.children).filter(function(c){return c.querySelector('b')&&!c.classList.contains('hi')}).slice(0,2);
    if(items.length<2)return;
    var bars=items.map(function(it){var s=d.createElement('span');s.className='vs';s.setAttribute('aria-hidden','true');s.appendChild(d.createElement('i'));it.appendChild(s);return s});
    function upd(){var a=parse(items[0].querySelector('b').textContent),b=parse(items[1].querySelector('b').textContent);
      var ok=a&&b&&a.u===b.u&&(a.v>0||b.v>0);box.classList.toggle('vs-off',!ok);if(!ok)return;
      var mx=Math.max(a.v,b.v);[a,b].forEach(function(x,i){bars[i].firstChild.style.width=(x.v/mx*100).toFixed(1)+'%';bars[i].classList.toggle('lead',x.v===mx&&a.v!==b.v)})}
    var mo=new MutationObserver(upd);items.forEach(function(it){mo.observe(it.querySelector('b'),{childList:true,characterData:true,subtree:true})});
    if('IntersectionObserver' in window){var io=new IntersectionObserver(function(es){if(es[0].isIntersecting){io.disconnect();upd()}},{threshold:.3});io.observe(box)}else upd();
  });
})();
