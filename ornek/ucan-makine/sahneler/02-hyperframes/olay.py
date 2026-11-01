import json
SB,SS=2.9,3.0
def ease(p): return 2*p*p if p<.5 else 1-2*(1-p)**2
ol=[{"kare":0,"tur":"cizgi","guc":0.5},{"kare":round(SB*30),"tur":"sayac","guc":0.4}]
for v in range(1500,1901,100):
    lo,hi=0,1
    for _ in range(40):
        m=(lo+hi)/2
        if 1485+418*ease(m)<v: lo=m
        else: hi=m
    ol.append({"kare":round((SB+lo*SS)*30),"tur":"sayac","guc":round(0.45+0.1*(v-1500)/400,2)})
ol.append({"kare":round((SB+SS)*30),"tur":"sayac","guc":0.8})
ol+= [{"kare":190,"tur":"vurus","guc":0.8},{"kare":201,"tur":"cizgi","guc":0.6}]
json.dump(ol,open("olaylar.json","w"),ensure_ascii=False)
