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
