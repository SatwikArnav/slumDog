from PIL import Image,ImageDraw,ImageFont,features
from pathlib import Path
import random
random.seed(12)
root=Path(__file__).parent/'assets'
font=root/'Devanagari.ttf'
latin='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def make(name,lines,bg,fg,size=(1536,512)):
 im=Image.new('RGB',size,bg);d=ImageDraw.Draw(im)
 d.rectangle((14,14,size[0]-15,size[1]-15),outline=fg,width=8)
 for text,y,sz in lines:
  f=ImageFont.truetype(str(font) if any(ord(c)>127 for c in text) else latin,sz)
  box=d.textbbox((0,0),text,font=f);x=(size[0]-(box[2]-box[0]))/2
  d.text((x,y),text,font=f,fill=fg,stroke_width=1)
 for i in range(1600):
  x=random.randrange(size[0]);y=random.randrange(size[1]);r=random.choice([1,1,2,3,5]);col=tuple(int(c*.65) for c in bg)
  d.line((x,y,x+r*3,y+random.randrange(1,5)),fill=col,width=1)
 im.save(root/(name+'.png'))
make('tea_sign',[('शंकर चाय भंडार',28,155),('SPECIAL CHAI  •  NASHTA',302,64)],(31,75,59),(237,215,149))
make('kirana_sign',[('श्री गणेश किराणा',30,152),('GENERAL STORES  •  DAILY NEEDS',306,52)],(133,36,29),(246,220,158))
make('tailor_sign',[('रहीम टेलर्स',38,162),('RAHIM TAILORS  •  ALTERATIONS',309,49)],(38,67,93),(230,223,194))
make('repair_sign',[('साई सायकल रिपेअर',35,144),('CYCLE REPAIR  •  PUNCTURE',310,55)],(196,157,66),(40,40,31))
make('lane_sign',[('शांती नगर',31,143),('SHANTI NAGAR   •   GULLY 03',305,50)],(31,70,109),(234,235,220))
make('menu',[('चाय  ₹१०',30,125),('SPECIAL CHAI  15',210,72),('BUN MASKA   20',340,66)],(20,34,29),(226,224,189),(768,576))
make('poster',[('खोली भाड्याने',28,85),('ROOM TO LET',175,75),('संपर्क : ९८२०० १२३४५',316,48)],(213,197,148),(62,48,32),(768,512))
# A soft, broken moisture and rust decal; transparent perimeter avoids rectangular marks.
im=Image.new('RGBA',(512,1024),(0,0,0,0));pix=im.load()
import math
for x in range(512):
 for y in range(1024):
  edge=max(0,1-abs(x-256)/256)**1.5
  wav=(math.sin(x*.055)+math.sin(x*.14+1)*.4+1.7)/3.1
  bottom=max(0,(y/1024-.2)/.8)
  alpha=int(85*edge*wav*bottom*(.7+random.random()*.3))
  pix[x,y]=(47,43,28,alpha)
im.save(root/'moisture.png')
print('Signs generated; text shaping:',features.check('raqm'))
