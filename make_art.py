#!/usr/bin/env python3
"""Generate brand art into assets/: podcast cover (3000x3000 + 600px web copy), favicon, og-image. Needs Pillow."""
import os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); A = os.path.join(HERE, "assets")
F = os.path.join(A, "fonts")
NAVY=(8,24,52); NAVY2=(13,42,90); GREEN=(34,197,94); WHITE=(255,255,255); GREY=(170,185,210); LINE=(31,61,116)
def anton(s): return ImageFont.truetype(os.path.join(F,"Anton-Regular.ttf"), s)
def mont(s,w=800):
    f=ImageFont.truetype(os.path.join(F,"Montserrat-VariableFont_wght.ttf"), s); f.set_variation_by_axes([w]); return f
def bg(w,h):
    im=Image.new("RGB",(w,h),NAVY); d=ImageDraw.Draw(im)
    for y in range(h):
        t=y/h; d.line([(0,y),(w,y)],fill=tuple(int(NAVY[i]+(NAVY2[i]-NAVY[i])*t) for i in range(3)))
    step=max(20,w//28); lw=max(2,w//700)
    ov=Image.new("RGBA",(w,h),(0,0,0,0)); od=ImageDraw.Draw(ov)
    for x in range(-h,w+h,step): od.line([(x,h),(x+int(h*0.7),0)],fill=(90,130,200,22),width=lw)
    im.paste(ov,(0,0),ov); return im
def ctext(d,y,s,f,fill,W):
    bb=d.textbbox((0,0),s,font=f); d.text(((W-(bb[2]-bb[0]))/2-bb[0],y-bb[1]),s,font=f,fill=fill); return bb[3]-bb[1]
def cover(S=3000):
    im=bg(S,S); d=ImageDraw.Draw(im); u=S/1000
    d.rectangle([0,0,S,int(22*u)],fill=GREEN)
    ctext(d,int(95*u),"VECTORPICKS.COM",mont(int(44*u),800),GREY,S)
    ctext(d,int(185*u),"AI NFL",anton(int(250*u)),WHITE,S)
    ctext(d,int(455*u),"WEEKLY SELECTIONS",anton(int(118*u)),GREEN,S)
    # pill
    pf=mont(int(40*u),800); t="with VECTOR · your AI analyst"; bb=d.textbbox((0,0),t,font=pf)
    pw,ph=(bb[2]-bb[0])+int(90*u),int(110*u); x0=(S-pw)//2; y0=int(640*u)
    d.rounded_rectangle([x0,y0,x0+pw,y0+ph],radius=int(24*u),outline=GREEN,width=int(7*u),fill=(12,32,68))
    ctext(d,y0+(ph-(bb[3]-bb[1]))//2,t,pf,WHITE,S)
    ctext(d,int(830*u),"POWER RATINGS · OUR SPREAD · THE CARD",mont(int(30*u),800),GREY,S)
    ctext(d,int(900*u),"Entertainment only · 21+",mont(int(24*u),600),(120,138,170),S)
    d.rectangle([0,S-int(12*u),int(S*0.35),S],fill=GREEN)
    return im
c=cover(3000); c.save(os.path.join(A,"podcast-cover-3000.png"),optimize=True)
c.resize((600,600),Image.LANCZOS).save(os.path.join(A,"podcast-cover-600.png"),optimize=True)
# favicon
fv=bg(256,256); d=ImageDraw.Draw(fv); d.rectangle([0,0,256,14],fill=GREEN); ctext(d,52,"VP",anton(150),GREEN,256)
fv.resize((64,64),Image.LANCZOS).save(os.path.join(A,"favicon.png"))
# og image 1200x630
og=bg(1200,630); d=ImageDraw.Draw(og); d.rectangle([0,0,1200,10],fill=GREEN)
ctext(d,90,"VECTORPICKS.COM",anton(130),WHITE,1200); ctext(d,270,"AI NFL WEEKLY SELECTIONS",anton(70),GREEN,1200)
ctext(d,400,"Our own power ratings & spreads · graded at the posted line",mont(30,700),GREY,1200)
ctext(d,520,"Entertainment only · 21+ · 1-800-GAMBLER",mont(24,600),(120,138,170),1200)
og.save(os.path.join(A,"og-image.png"),optimize=True)
print("art ok", c.size)
