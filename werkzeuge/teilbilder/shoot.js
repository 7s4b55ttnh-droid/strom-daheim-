const {chromium}=require('playwright');const fs=require('fs');
(async()=>{const b=await chromium.launch({args:['--allow-file-access-from-files']});const p=await b.newPage({viewport:{width:1200,height:630}});
for(const s of process.argv.slice(2)){for(const [src,dst] of JSON.parse(fs.readFileSync(s))){await p.goto('file://'+src);await p.waitForTimeout(150);await p.screenshot({path:dst.replace('.jpg','.png')});}}
await b.close()})();
