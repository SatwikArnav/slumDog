"""Original fictional packaging, price cards and workshop signage atlas."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import random
ROOT=Path(__file__).parent/'assets'
labels=[('ANNA','BASMATI RICE','1 kg'),('SUGANDH','MASALA CHAI','250 g'),('SURYA','COOKING OIL','1 litre'),('NIRMAL','WASHING SOAP','100 g'),('TARA','GLUCOSE BISCUITS','Rs 10'),('MIRCHI','CHILLI POWDER','100 g'),('DAL','TOOR / MOONG','500 g'),('SAFEDI','DETERGENT','500 g'),('FRESH CHAI','CHAI 10 / SPECIAL 15','BUN MASKA 20'),('RAHIM TAILORS','ALTERATIONS / STITCHING','DELIVERY 3 DAYS'),('SAI CYCLE WORKS','PUNCTURE / BRAKE / CHAIN','AIR AVAILABLE'),('SHANTI ELECTRICAL','FANS / MIXERS / IRONS','REPAIRS UNDERTAKEN'),('2026','OCTOBER','1  2  3  4  5  6  7'),('PAY HERE','CASH / UPI','PLEASE ASK FOR RECEIPT'),('WORK ORDER','NAME: __________','DATE: ____  PAID: ____'),('FRAGILE','KEEP DRY','THIS SIDE UP')]
im=Image.new('RGB',(2048,2048));d=ImageDraw.Draw(im);rng=random.Random(7)
font='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
for i,(title,sub,small) in enumerate(labels):
 x,y=(i%4)*512,(i//4)*512
 bg=[(144,42,29),(33,86,63),(181,131,32),(48,84,114),(161,79,31),(102,47,42),(145,122,61),(42,102,106)][i%8] if i<8 else (220,207,168)
 ink=(246,229,184) if i<8 else (43,51,45)
 d.rectangle((x,y,x+511,y+511),fill=bg)
 d.rectangle((x+18,y+18,x+493,y+493),outline=ink,width=5)
 if i<8:
  d.ellipse((x+170,y+155,x+342,y+327),outline=ink,width=9)
  for k in range(5):d.line((x+200+k*24,y+220,x+210+k*24,y+270),fill=ink,width=8)
 for text,dy,maxsize in [(title,65,48),(sub,350,25),(small,415,24)]:
  size=maxsize
  while d.textlength(text,font=ImageFont.truetype(font,size))>460:size-=1
  f=ImageFont.truetype(font,size);w=d.textlength(text,font=f)
  d.text((x+(512-w)/2,y+dy),text,font=f,fill=ink)
 if i>=8:
  for k in range(5):d.line((x+48,y+160+k*29,x+464,y+160+k*29),fill=(141,135,111),width=2)
 for _ in range(160):
  a,b=x+rng.randrange(512),y+rng.randrange(512)
  d.line((a,b,a+rng.randrange(2,8),b),fill=tuple(int(v*.85) for v in bg),width=1)
im.save(ROOT/'shop_labels.png')
