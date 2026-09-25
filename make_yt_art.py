#!/usr/bin/env python3
"""YouTube channel art for @VectorPicks -> brand/. Needs Pillow."""
import os
from PIL import Image, ImageDraw, ImageFont
HERE=os.path.dirname(os.path.abspath(__file__)); F=os.path.join(HERE,"assets","fonts"); OUT=os.path.join(HERE,"brand")
os.makedirs(OUT,exist_ok=True)
NAVY=(8,24,52); NAVY2=(13,42,90); PANEL=(12,32,68); GREEN=(34,197,94); WHITE=(255,255,255); GREY=(170,185,210)
def anton(s): return ImageFont.truetype(os.path.join(F,"Anton-Regular.ttf"),s)
def mont(s,w=800):
    f=ImageFont.truetype(os.path.join(F,"Montserrat-VariableFont_wght.ttf"),s); f.set_variation_by_axes([w]); return f
def bg(w,h,step=None):
    im=Image.new("RGB",(w,h),NAVY); d=ImageDraw.Draw(im)
    for y in range(h):
        t=y/h; d.line([(0,y),(w,y)],fill=tuple(int(NAVY[i]+(NAVY2[i]-NAVY[i])*t) for i in range(3)))
    step=step or max(20,w//28); lw=max(2,w//700)
    ov=Image.new("RGBA",(w,h),(0,0,0,0)); od=ImageDraw.Draw(ov)
    for x in range(-h,w+h,step): od.line([(x,h),(x+int(h*0.7),0)],fill=(90,130,200,22),width=lw)
    im.paste(ov,(0,0),ov); return im
def text_at(d,cx,cy,s,f,fill):
    bb=d.textbbox((0,0),s,font=f); w,h=bb[2]-bb[0],bb[3]-bb[1]
    d.text((cx-w/2-bb[0],cy-h/2-bb[1]),s,font=f,fill=fill); return w,h

# ---------- profile 800x800 ----------
S=800; p=bg(S,S,step=34); d=ImageDraw.Draw(p)
c=S//2
d.ellipse([c-270,c-270,c+270,c+270],fill=PANEL,outline=GREEN,width=14)   # r=270 < 0.35*800=280
f=anton(300)
bbV=d.textbbox((0,0),"V",font=f); bbP=d.textbbox((0,0),"P",font=f)
wV,wP=bbV[2]-bbV[0],bbP[2]-bbP[0]; gap=6; tot=wV+wP+gap; h=bbV[3]-bbV[1]
x0=c-tot/2; y0=c-h/2+6
d.text((x0-bbV[0],y0-bbV[1]),"V",font=f,fill=WHITE)
d.text((x0+wV+gap-bbP[0],y0-bbP[1]),"P",font=f,fill=GREEN)
# green vector arrow underline
ay=int(y0+h+22); ax0=int(c-tot/2+10); ax1=int(c+tot/2-10)
d.line([(ax0,ay),(ax1-26,ay)],fill=GREEN,width=16)
d.polygon([(ax1+8,ay),(ax1-34,ay-26),(ax1-34,ay+26)],fill=GREEN)
p.save(os.path.join(OUT,"youtube-profile.png"),optimize=True)

# ---------- banner 2560x1440 ----------
W,H=2560,1440; b=bg(W,H,step=60); d=ImageDraw.Draw(b)
sx0,sy0=(W-1546)//2,(H-423)//2; sx1,sy1=sx0+1546,sy0+423
# decoration outside safe area: green bars + faint big chevrons
d.rectangle([0,0,W,18],fill=GREEN); d.rectangle([0,H-18,int(W*0.35),H],fill=GREEN)
ov=Image.new("RGBA",(W,H),(0,0,0,0)); od=ImageDraw.Draw(ov)
for i,xx in enumerate([20,150,270]):
    od.line([(xx,H//2-300),(xx+200,H//2),(xx,H//2+300)],fill=(34,197,94,40+i*25),width=40,joint="curve")
for i,xx in enumerate([W-20,W-150,W-270]):
    od.line([(xx,H//2-300),(xx-200,H//2),(xx,H//2+300)],fill=(34,197,94,40+i*25),width=40,joint="curve")
b.paste(ov,(0,0),ov); d=ImageDraw.Draw(b)
cx=W//2
text_at(d,cx,sy0+120,"AI NFL WEEKLY SELECTIONS",anton(140),WHITE)
text_at(d,cx,sy0+255,"with Vector, your AI analyst",mont(56,800),GREEN)
line="New picks Tue · Thu · Sun   |   VectorPicks.com"
lf=mont(40,700); bb=d.textbbox((0,0),line,font=lf); lw=bb[2]-bb[0]
pw,ph=lw+80,78; px0=cx-pw//2; py0=sy0+320
d.rounded_rectangle([px0,py0,px0+pw,py0+ph],radius=18,fill=PANEL,outline=GREEN,width=4)
text_at(d,cx,py0+ph//2,line,lf,WHITE)
b.save(os.path.join(OUT,"youtube-banner.png"),optimize=True)
SAFE=(sx0,sy0,sx1,sy1)

# ---------- previews ----------
def circ(im,size):
    im=im.resize((size,size),Image.LANCZOS); m=Image.new("L",(size*4,size*4),0)
    ImageDraw.Draw(m).ellipse([0,0,size*4-1,size*4-1],fill=255); m=m.resize((size,size),Image.LANCZOS)
    o=Image.new("RGBA",(size,size),(0,0,0,0)); o.paste(im,(0,0),m); return o
pv=Image.new("RGB",(1200,900),(24,24,24)); pd=ImageDraw.Draw(pv)
pv.paste(circ(p,800),(40,50),circ(p,800))
c176=circ(p,176); pv.paste(c176,(920,150),c176)
c48=circ(p,48); pv.paste(c48,(984,420),c48)
pd.text((40,10),"800px circle",font=mont(26,700),fill=WHITE)
pd.text((920,110),"176px",font=mont(26,700),fill=WHITE); pd.text((960,380),"48px",font=mont(26,700),fill=WHITE)
pv.save(os.path.join(OUT,"profile-circle-preview.png"),optimize=True)
b.crop(SAFE).save(os.path.join(OUT,"banner-mobile-preview.png"),optimize=True)
# debug overlay (not required): safe-area box
dbg=b.copy(); ImageDraw.Draw(dbg).rectangle(SAFE,outline=(255,0,0),width=4); dbg.resize((1280,720)).save("/tmp/banner-safe-debug.png")
print("ok", p.size, b.size, SAFE)
