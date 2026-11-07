import re,sys,json,os,html as H
site=sys.argv[1]  # strom|stil
root={'strom':'/home/claude/strom-daheim-','stil':'/home/claude/stil-daheim'}[site]
skip={'404.html','impressum.html','datenschutz.html'}
C={'strom':dict(brand='Strom-Daheim',dom='strom-daheim.de',acc='#ffb81c',bg='radial-gradient(120% 120% at 85% 10%,#2a2000 0%,#0b0b0b 55%,#000 100%)',font="-apple-system,'Inter','Helvetica Neue',Arial,sans-serif",logo='<svg viewBox="0 0 64 64" width="44" height="44"><path d="M35 10 19 36h11l-3 18 18-27H34z" fill="#ffb81c"/></svg>'),
   'stil':dict(brand='Stil-Daheim',dom='stil-daheim.de',acc='#cfae6a',bg='radial-gradient(120% 120% at 85% 10%,#3a2e14 0%,#16130c 55%,#0b0a07 100%)',font="'Archivo','Helvetica Neue',Arial,sans-serif",logo='<svg viewBox="0 0 24 24" width="40" height="40" fill="none" stroke="#cfae6a" stroke-width="1.6"><path d="M8 3h8l3 8H5zM12 11v9M8 21h8"/></svg>')}[site]
ILLCSS='''.ill{width:420px;height:auto;overflow:visible}.ill *{fill:none;stroke:rgba(245,245,247,.6);stroke-width:2.4;stroke-linecap:round;stroke-linejoin:round}
.ill .t{stroke:rgba(245,245,247,.35);stroke-width:1.8}.ill .a{stroke:ACC;fill:rgba(255,184,28,.10)}.ill .g{stroke:ACC;stroke-width:2.8}
.ill .sw{stroke:rgba(255,255,255,.35);stroke-width:1.5}.ill .o{fill:rgba(255,255,255,.55);stroke:none}.ill .b{fill:ACC;stroke:none}.ill .l{stroke:rgba(255,255,255,.6)}
.ill .s{fill:rgba(207,174,106,.18);stroke:ACC}.ill .m{fill:rgba(207,174,106,.22);stroke:ACC}.ill .st{fill:ACC;stroke:none}.ill .sw[fill]{fill:attr(fill)}'''.replace('ACC',C['acc'])
out=[]
for f in sorted(os.listdir(root)):
    if not f.endswith('.html') or f in skip: continue
    h=open(os.path.join(root,f)).read()
    m=re.search(r'<h1[^>]*>(.*?)</h1>',h,re.S)
    if not m: continue
    title=re.sub(r'<[^>]+>','',m.group(1)).replace('&shy;','').replace('&nbsp;',' ')
    title=H.unescape(re.sub(r'\s+',' ',title)).strip()
    hero=h[h.find('<main'):h.find('<main')+6000] if '<main' in h else h
    img=re.search(r'<img[^>]+src="(/?assets/[^"]+\.jpg)"',hero)
    ill=re.search(r'<svg class="ill".*?</svg>',hero,re.S)
    big='bfbig' in hero
    out.append(dict(f=f,title=title,img=img.group(1).lstrip('/') if img else None,ill=ill.group(0) if ill else None,bf=big))
os.makedirs(root+'/assets/og',exist_ok=True)
pages=[]
for p in out:
    if p['img']: vis='<div class="ph" style="background-image:url(file://%s/%s)"></div>'%(root,p['img'])
    elif p['bf']: vis='<div class="bfb"><span>BLACK</span><span>FRIDAY</span></div>'
    elif p['ill']: vis='<div class="il">%s</div>'%p['ill'].replace('class="ill"','class="ill" style="width:430px"')
    else: vis=''
    fs=74 if len(p['title'])<34 else 62 if len(p['title'])<52 else 52
    doc='''<!doctype html><html><head><meta charset="utf-8"><style>
*{margin:0;box-sizing:border-box}body{width:1200px;height:630px;overflow:hidden;background:%(bg)s;font-family:%(font)s;color:#fff;position:relative}
.ph{position:absolute;inset:0;background-size:cover;background-position:center}
.ph::after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(0,0,0,.86) 0%%,rgba(0,0,0,.62) 48%%,rgba(0,0,0,.12) 100%%)}
.il{position:absolute;right:56px;top:50%%;transform:translateY(-50%%)}
.bfb{position:absolute;right:60px;top:50%%;transform:translateY(-50%%);display:flex;flex-direction:column;align-items:flex-end;font-weight:900;font-size:118px;line-height:.86}
.bfb span:first-child{color:transparent;-webkit-text-stroke:3px %(acc)s}.bfb span:last-child{color:%(acc)s}
.tx{position:absolute;left:64px;top:64px;bottom:64px;width:%(w)spx;display:flex;flex-direction:column;justify-content:space-between}
.br{display:flex;align-items:center;gap:12px;font-size:30px;font-weight:700}
h1{font-size:%(fs)spx;line-height:1.04;letter-spacing:-.01em;font-weight:800}
.u{font-size:26px;color:%(acc)s;font-weight:600}
.bar{position:absolute;left:0;right:0;bottom:0;height:10px;background:%(acc)s}
%(illcss)s</style></head><body>%(vis)s<div class="tx"><div class="br">%(logo)s<span>%(brand)s</span></div><h1>%(t)s</h1><div class="u">%(dom)s</div></div><div class="bar"></div></body></html>'''%dict(C,vis=vis,t=H.escape(p['title']),fs=fs,w=(540 if p['bf'] else 640) if (p['ill'] or p['bf']) and not p['img'] else 760,illcss=ILLCSS)
    path='/tmp/teilbilder/%s_%s'%(site,p['f'])
    open(path,'w').write(doc);pages.append([path,root+'/assets/og/'+p['f'].replace('.html','.jpg')])
json.dump(pages,open('/tmp/teilbilder/%s.json'%site,'w'))
print(site,len(pages))
