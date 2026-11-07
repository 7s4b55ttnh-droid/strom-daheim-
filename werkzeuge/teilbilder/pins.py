"""Pinterest-Pins 1000x1500 bauen. Aufruf: python3 pins.py <ausgabeordner> <json-datei>
JSON: [{"site":"stil|strom","bild":"assets/x.jpg","titel":"...","name":"datei"}]"""
import sys,json,html as H,subprocess,os
R={'strom':('/home/claude/strom-daheim-','strom-daheim.de','Strom-Daheim','#ffb81c','#0b0b0b','#f5f5f7'),
   'stil':('/home/claude/stil-daheim','stil-daheim.de','Stil-Daheim','#cfae6a','#f3efe6','#1e1a14')}
out=sys.argv[1];items=json.load(open(sys.argv[2]));jobs=[]
for it in items:
    root,dom,brand,acc,bg,fg=R[it['site']]
    t=H.escape(it['titel']);fs=92 if len(it['titel'])<28 else 80 if len(it['titel'])<40 else 68
    doc=f'''<!doctype html><html><head><meta charset="utf-8"><style>*{{margin:0;box-sizing:border-box}}
body{{width:1000px;height:1500px;background:{bg};font-family:-apple-system,'Inter','Helvetica Neue',Arial,sans-serif;color:{fg};overflow:hidden}}
.ph{{height:960px;background:url(file://{root}/{it['bild']}) center/cover}}
.tx{{height:540px;padding:56px 64px;display:flex;flex-direction:column;justify-content:space-between;border-top:12px solid {acc}}}
h1{{font-size:{fs}px;line-height:1.05;font-weight:850;letter-spacing:-.01em}}
.ft{{display:flex;justify-content:space-between;align-items:center;font-size:32px;font-weight:700}}.ft span:last-child{{color:{acc if it['site']=='strom' else '#8a6a2c'}}}
</style></head><body><div class="ph"></div><div class="tx"><h1>{t}</h1><div class="ft"><span>{brand}</span><span>{dom}</span></div></div></body></html>'''
    p=f'/tmp/teilbilder/pin_{it["name"]}.html';open(p,'w').write(doc);jobs.append([p,f'{out}/{it["name"]}.jpg'])
json.dump(jobs,open('/tmp/teilbilder/pins.json','w'))
js='''const {chromium}=require('playwright');const fs=require('fs');(async()=>{const b=await chromium.launch({args:['--allow-file-access-from-files']});const p=await b.newPage({viewport:{width:1000,height:1500}});
for(const [s,d] of JSON.parse(fs.readFileSync('/tmp/teilbilder/pins.json'))){await p.goto('file://'+s);await p.waitForTimeout(200);await p.screenshot({path:d.replace('.jpg','.png')})}await b.close()})();'''
open('/tmp/teilbilder/pins.js','w').write(js);subprocess.run(['node','/tmp/teilbilder/pins.js'],check=True)
from PIL import Image
for _,d in jobs:
    pp=d.replace('.jpg','.png');Image.open(pp).convert('RGB').save(d,quality=86,optimize=True,progressive=True);os.remove(pp)
print(len(jobs))
