"""Baut aus den PVGIS-Rohdaten (typisches Jahr + langjährige Monatsmittel) die Datendatei einer Region.
Aufruf: python3 kodieren.py <tmy.json> <mr.json> <ziel.json> <plz2> <name>
Schritte: 1) Stundenwerte lesen. 2) Jeden Monat so skalieren, dass direkte und diffuse Strahlung
den Mittelwerten 2005 bis 2023 entsprechen (direkt nie über dem Wert bei klarem Himmel). 3) In Bytes packen."""
import json, math, base64, sys
MD=[31,28,31,30,31,30,31,31,30,31,30,31]
def sun_cz(doy,utc,lat,lon):
    g=2*math.pi/365*(doy-1+(utc-12)/24)
    eq=229.18*(0.000075+0.001868*math.cos(g)-0.032077*math.sin(g)-0.014615*math.cos(2*g)-0.040849*math.sin(2*g))
    dec=0.006918-0.399912*math.cos(g)+0.070257*math.sin(g)-0.006758*math.cos(2*g)+0.000907*math.sin(2*g)-0.002697*math.cos(3*g)+0.00148*math.sin(3*g)
    ha=math.radians((utc*60+eq+4*lon)/4-180);la=math.radians(lat)
    return math.sin(la)*math.sin(dec)+math.cos(la)*math.cos(dec)*math.cos(ha), 1361*(1+0.033*math.cos(2*math.pi*doy/365))
def build(tmy,mr,plz,name):
    d=json.load(open(tmy));loc=d['inputs']['location'];H=d['outputs']['tmy_hourly'];assert len(H)==8760
    lat,lon,off=loc['latitude'],loc['longitude'],loc.get('irradiance_time_offset',0.0)
    G=[max(0.0,x['G(h)']) for x in H];D=[max(0.0,min(x['Gd(h)'],x['G(h)'])) for x in H];T=[x['T2m'] for x in H]
    M=json.load(open(mr))['outputs']['monthly'];Ht=[0]*12;Dt=[0]*12;N=[0]*12
    for r in M: Ht[r['month']-1]+=r['H(h)_m'];Dt[r['month']-1]+=r['H(h)_m']*r['Kd'];N[r['month']-1]+=1
    yrs=sorted(set(r['year'] for r in M))
    h=0;info=[]
    for m in range(12):
        a=h;b=h+MD[m]*24;h=b
        ht=Ht[m]/N[m]*1000;dt=Dt[m]/N[m]*1000;bt=ht-dt
        ds=sum(D[a:b]);sD=dt/ds
        B=[G[i]-D[i] for i in range(a,b)];cap=[]
        for i in range(a,b):
            cz,i0=sun_cz(i//24+1,i%24+off,lat,lon);cap.append(max(0.0,0.80*i0*cz))
        Bn=B[:]
        for it in range(12):
            free=[k for k in range(len(Bn)) if Bn[k]<cap[k]-1e-6 and B[k]>0]
            cur=sum(Bn);need=bt-cur
            if abs(need)<0.5 or not free: break
            fs=sum(Bn[k] for k in free)
            if fs<=0: break
            f=1+need/fs
            for k in free: Bn[k]=min(max(Bn[k]*f,0),cap[k])
        for k,i in enumerate(range(a,b)):
            D[i]=D[i]*sD;G[i]=Bn[k]+D[i]
        info.append((round(sum(G[a:b])/1000,1),round(ht/1000,1),round(sum(D[a:b])/1000,1),round(dt/1000,1)))
    gb=bytearray(8760);fb=bytearray(8760);tb=bytearray(8760)
    for i in range(8760):
        if G[i]<0.5: continue
        v=min(255,max(1,round(math.sqrt(G[i])*7.5)));gb[i]=v
        fb[i]=min(255,max(0,round(D[i]/G[i]*255)))
        tb[i]=min(255,max(1,round((T[i]+30)*2)))
    sg=sum(x['G(h)'] for x in H);wind=round(sum(x['G(h)']*x['WS10m'] for x in H)/sg,2)
    out={'v':1,'plz':plz,'name':name,'lat':round(lat,3),'lon':round(lon,3),'hoehe':round(loc.get('elevation',0)),'off':round(off,4),'w':wind,
         'ghi':round(sum(G)/1000),'jahre':'%d–%d'%(yrs[0],yrs[-1]),'quelle':'PVGIS-SARAH3, © Europäische Union',
         'g':base64.b64encode(bytes(gb)).decode(),'f':base64.b64encode(bytes(fb)).decode(),'t':base64.b64encode(bytes(tb)).decode()}
    return out,info
if __name__=='__main__':
    out,info=build(sys.argv[1],sys.argv[2],sys.argv[4],sys.argv[5])
    json.dump(out,open(sys.argv[3],'w'),ensure_ascii=False,separators=(',',':'))
    print(out['ghi'],[i[0]-i[1] for i in info],[round(i[2]-i[3],1) for i in info])
