/* „Frag den Ratgeber“: beantwortet Fragen in ganzen Sätzen aus den geprüften Antworten der Website (frag.json, schreibt frag_index.py).
   Es wird nichts erzeugt oder erfunden: Jede Antwort steht wörtlich auf einer unserer Seiten, der Link führt dorthin. Alles läuft im Browser, keine Frage wird übertragen.
   window.sdFrag.frag(text) -> Promise<{antworten:[{q,a,u,t,s}], seiten:[{u,t,s}]}>;  window.sdFrag.kasten(el) baut den Fragekasten in el. */
(function(){
'use strict';
var d=document,sc=d.querySelector('script[src*="site.js"]'),BASE=sc?sc.src.replace(/site\.js.*$/,''):'/',idx=null,df={},N=0;
var st=d.createElement('style');st.textContent='.fragk-sec{padding:clamp(40px,7vw,72px) 20px}.fragk{max-width:720px;margin:0 auto}.fragk h2{margin:0 0 8px}.fragk-s{margin:0 0 20px;color:var(--mut,#555);max-width:56ch}.fragk-f{display:flex;gap:8px}.fragk-f input{flex:1;min-width:0;min-height:54px;padding:0 20px;border-radius:999px;border:1.5px solid var(--line,#c7c7cc);background:var(--pan,#fff);color:inherit;font:inherit;font-size:1rem}.fragk-f button{flex:none;min-height:54px;padding:0 24px;border-radius:999px;border:0;background:var(--ink,#111);color:var(--bg,#fff);font:inherit;font-weight:650;cursor:pointer}.fragk-c{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 0}.fragk-c button,.fragk-w{font:inherit;font-size:.92rem;font-weight:600;text-align:left;min-height:44px;padding:9px 16px;border-radius:22px;border:1.5px solid var(--line,#c7c7cc);background:transparent;color:inherit;cursor:pointer}.fragk-c button:hover,.fragk-w:hover{border-color:currentColor}.fragk-o:empty{display:none}.fragk-o{margin:22px 0 0}.fragk-a{padding:22px 24px;border-radius:22px;background:var(--pan,#fff);border:1px solid var(--line,#c7c7cc)}.fragk-a b{display:block;font-size:1.12rem;line-height:1.3;margin:0 0 8px}.fragk-a p{margin:0 0 12px}.fragk-a a{font-weight:650}.fragk-m{margin:18px 0 8px;font-size:.9rem;font-weight:650;color:var(--mut,#555)}.fragk-w{display:block;width:100%;margin:0 0 8px}.fragk-n{margin:0 0 10px}.fragk-l{margin:0;padding-left:1.2em}.fragk-l li{margin:6px 0}.fragk input:focus-visible,.fragk button:focus-visible{outline:2px solid currentColor;outline-offset:2px}.sq li.sq-ant a{background:var(--pan,#fff);border:1px solid var(--line,#c7c7cc);border-radius:16px;padding:14px 16px;margin:0 0 8px}.sq li.sq-ant small{display:block;font-weight:650;opacity:1;color:var(--mut,#555);margin:0 0 4px}.sq li.sq-ant span{display:-webkit-box;-webkit-line-clamp:5;-webkit-box-orient:vertical;overflow:hidden;margin:4px 0 6px}.sq li.sq-ant em{font-style:normal;font-weight:650;text-decoration:underline;text-underline-offset:3px}@media(max-width:480px){.fragk-f button{padding:0 18px}.fragk-a{padding:18px}}';d.head.appendChild(st);
var STOP='aber alle allem allen aller alles als also am an auch auf aus bei bin bis bist da damit dann das dass dein deine deinem deinen deiner dem den denn der des die dies diese dieser doch dort du durch ein eine einem einen einer eines er es etwas euch fuer gegen gibt hab habe haben hat hier ich ihr im in ist ja jede jedem jeden jeder kann kannst kein keine man mein meine meinem meinen meiner mich mir mit muss musst nach nicht noch nun nur ob oder ohne sehr sein seine sich sie sind so soll sollte um und uns unter vom von vor wann warum was weil welche welchem welchen welcher welches wenn wer werden wie wieder will wir wird wo wohl zu zum zur ueber eigentlich bitte mal denn gerade genau ungefaehr viel viele wieviel geht gehen macht machen mache brauche brauch braucht brauchen fuers ins aufs ans beim einem meinen meinem unser unsere denn eigentlich sollte soll darf duerfen lange oft passt passen lassen laesst lass gut beste besten bester am'.split(' '),ST={};
STOP.forEach(function(w){ST[w]=1});
function norm(s){return String(s).toLowerCase().replace(/ä/g,'ae').replace(/ö/g,'oe').replace(/ü/g,'ue').replace(/ß/g,'ss').replace(/[^a-z0-9]+/g,' ').trim()}
/* gleiche Bedeutung, andere Wortform: hoch/Höhe, kostet/Preis/teuer … */
var GL=[['hoch','hoehe','hoeh'],['gross','groesse','groess'],['lang','laenge','laeng'],['kost','kostet','preis','teuer','teur','kosten'],['verbrauch','verbraucht','verbrauche'],['lad','laedt','ladung','aufladen'],['dauer','dauert'],['streich','gestrichen','anstrich','streicht'],['haeng','haengt','aufhaeng','haengst'],['spar','spart','gespart','ersparnis'],['bild','bilder','poster','rahmen'],['hell','heller','helligkeit'],['kalt','warm','waerm','waermer','temperatur','grad','kaelt'],['solaranlag','photovoltaik','fotovoltaik','pv','solaranlage','solaranlagen','solar'],['guenstig','billig','billigst','guenstigst','guenstiger','billiger','billigsten','guenstigsten'],['tarif','stromvertrag','stromtarif','vertrag','stromanbieter','anbieter'],['wechsel','kuendig','kuendige','kuendigen','kuendigst','kuendigung','wechseln','wechsle'],['bedarf','reicht','liter','menge'],['pflanz','pflanze','pflanzen','zimmerpflanze','zimmerpflanzen'],['gluehbirn','gluehbirne','leuchtmittel','birne','gluehlampe']],GM={};
GL.forEach(function(g){g.forEach(function(w){GM[w]=g[0]})});
function stamm(w){if(GM[w])return GM[w];if(w.length>=5){var k=w.replace(/(ern|en|er|es|em|e|n|s)$/,'');if(k.length>=4)w=k}return GM[w]||w}
function woerter(s){var o=[];norm(s).split(' ').forEach(function(w){if(w.length>1&&!ST[w]){w=stamm(w);if(o.indexOf(w)<0)o.push(w)}});return o}
/* trifft ein Fragewort ein Wort der Antwort? Gleich, gleicher Anfang oder Teil eines zusammengesetzten Worts (Kühlschrank in Kühlschranktür) */
function passt(a,b){if(a===b)return 1;if(a.length>=4&&b.length>=4){if(b.indexOf(a)===0)return .85;if(a.indexOf(b)===0)return .55;if(b.indexOf(a)>0)return b.slice(-a.length)===a?.95:.6;if(a.indexOf(b)>0)return .3}return 0}
function best(w,L){var m=0;for(var i=0;i<L.length&&m<1;i++){var p=passt(w,L[i]);if(p>m)m=p}return m}
function laden(){if(idx)return Promise.resolve(idx);return fetch(BASE+'frag.json').then(function(r){return r.json()}).then(function(j){
  j.forEach(function(e){e.wq=woerter(e.q);e.wt=woerter(e.t+' '+e.u.replace(/\.html$/,''));e.wa=woerter(e.a);var seen={};e.wq.concat(e.wt,e.wa).forEach(function(w){if(!seen[w]){seen[w]=1;df[w]=(df[w]||0)+1}})});N=j.length;idx=j;return j})}
function kennt(w){var n=0;for(var k in df)if(passt(w,k)>=.85)n+=df[k];return n}
function gewicht(w){return Math.log(1+N/(1+kennt(w)))}
function frag(text){return laden().then(function(L){var W=woerter(text),out={antworten:[],seiten:[]};if(!W.length)return out;
  var G=W.map(gewicht),sum=G.reduce(function(a,b){return a+b},0)||1,seiten={},lose={},top=-1;
  W.forEach(function(w,i){if(kennt(w)&&(top<0||G[i]>G[top]))top=i});if(top<0)return out;
  L.forEach(function(e){var s=0,tr=0,kern=0;W.forEach(function(w,i){var q=best(w,e.wq),t=best(w,e.wt),a=best(w,e.wa),tt=e.k?t*.9:t*.7,m=Math.max(q,tt,a*.45);if(m>0)tr+=G[i];if(Math.max(q,t)>=.5)kern+=G[i];s+=G[i]*Math.max(q,tt,a*.4,(q+tt*.5+a*.3)/1.8)});
    var deck=tr/sum;if(deck>=.3&&(!lose[e.u]||lose[e.u].s<s/sum*deck))lose[e.u]={u:e.u,t:e.t,s:s/sum*deck};if(deck<.5||kern/sum<.5)return;   /* das seltenste Wort der Frage muss in Frage oder Seitentitel vorkommen */var rueck=0;e.wq.forEach(function(w){for(var i=0;i<W.length;i++)if(passt(w,W[i])>=.85||passt(W[i],w)===1){rueck++;break}});rueck=e.k?1:rueck/(e.wq.length||1);s=s/sum*deck*(.6+.4*rueck);if(e.k)s*=.97;
    out.antworten.push({q:e.q,a:e.a,u:e.u,t:e.t,s:s});if(!seiten[e.u]||seiten[e.u].s<s)seiten[e.u]={u:e.u,t:e.t,s:s}});
  out.antworten.sort(function(a,b){return b.s-a.s});out.antworten=out.antworten.slice(0,5);
  for(var u in lose)if(!seiten[u])seiten[u]={u:u,t:lose[u].t,s:lose[u].s*.5};
  out.seiten=Object.keys(seiten).map(function(k){return seiten[k]}).sort(function(a,b){return b.s-a.s}).slice(0,6);return out})}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function url(u){return BASE.replace(/\/$/,'')+u}

/* Fragekasten für Ratgeberseiten */
function kasten(el,opt){opt=opt||{};el.classList.add('fragk');
 el.innerHTML='<h2 id="fragk-h">Noch eine Frage?</h2><p class="fragk-s">Stell sie in deinen Worten. Die Antwort kommt Wort für Wort aus unseren geprüften Ratgebern. Deine Frage bleibt auf deinem Gerät.</p><form class="fragk-f" role="search" aria-labelledby="fragk-h"><input type="search" enterkeyhint="search" autocomplete="off" aria-label="Deine Frage" placeholder="'+esc(opt.beispiel||'Zum Beispiel: Was kostet eine Stunde Trockner?')+'"><button type="submit">Fragen</button></form><div class="fragk-c" role="group" aria-label="Häufige Fragen"></div><div class="fragk-o" aria-live="polite"></div>';
 var inp=el.querySelector('input'),out=el.querySelector('.fragk-o'),chips=el.querySelector('.fragk-c'),hier=location.pathname.replace(/index\.html$/,'');
 function zeig(text){frag(text).then(function(r){var a=r.antworten[0];
   if(!a||a.s<.4){out.innerHTML='<p class="fragk-n">Dazu haben wir noch keine geprüfte Antwort. Versuch es mit anderen Worten oder schau in die Übersicht.</p>'+liste(r.seiten.filter(function(x){return x.s>=.25}).slice(0,3));return}
   var mehr=r.antworten.slice(1).filter(function(x){return x.s>a.s*.6&&x.q!==a.q}).slice(0,2);
   out.innerHTML='<div class="fragk-a"><b>'+esc(a.q)+'</b><p>'+esc(a.a)+'</p><a href="'+esc(url(a.u))+'">Mehr dazu: '+esc(a.t)+'</a></div>'+(mehr.length?'<p class="fragk-m">Passt auch:</p>'+mehr.map(function(x){return '<button type="button" class="fragk-w">'+esc(x.q)+'</button>'}).join(''):'')})}
 function liste(S){return S.length?'<ul class="fragk-l">'+S.map(function(s){return '<li><a href="'+esc(url(s.u))+'">'+esc(s.t)+'</a></li>'}).join('')+'</ul>':''}
 el.querySelector('form').addEventListener('submit',function(ev){ev.preventDefault();if(inp.value.trim())zeig(inp.value)});
 el.addEventListener('click',function(ev){var b=ev.target.closest('.fragk-c button,.fragk-w');if(!b)return;inp.value=b.textContent;zeig(b.textContent)});
 /* Vorschläge: Fragen von ANDEREN Seiten, die zu dieser Seite passen */
 laden().then(function(){var h1=d.querySelector('h1'),t=(h1?h1.textContent:'')+' '+d.title;frag(t).then(function(r){var seen={},L=[];
   idx.forEach(function(e){if(e.u===hier||e.k)return;var s=0;woerter(t).forEach(function(w){s+=Math.max(best(w,e.wq),best(w,e.wt)*.7)});if(s>0)L.push([s,e])});
   L.sort(function(a,b){return b[0]-a[0]});var pick=[];L.forEach(function(x){if(pick.length<4&&!seen[x[1].u]){seen[x[1].u]=1;pick.push(x[1])}});
   if(pick.length<2)idx.forEach(function(e){if(pick.length<4&&!e.k&&e.u!==hier&&!seen[e.u]){seen[e.u]=1;pick.push(e)}});
   chips.innerHTML=pick.map(function(e){return '<button type="button">'+esc(e.q)+'</button>'}).join('')})})}
window.sdFrag={frag:frag,kasten:kasten,laden:laden,url:url};
d.dispatchEvent(new Event('sdfrag'));
})();
