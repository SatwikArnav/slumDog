# Added incremental structure, irregular rooflines, and activity-specific props.
ACTIVE=COL['Architecture']
# A T-junction at the far end hides the horizon while the route turns sideways.
box('Far junction house',(0.3,32.1,2.6),(11,3.3,5.2),plasters[3])
box('Far house lower colour band',(.3,30.42,.7),(11,.04,1.4),plasters[1])
for xx in [-3.4,-.8,2,4.2]:
 box('Far window recess',(xx,30.42,3.8),(.95,.06,1.1),dark)
 for j in range(6):box('Far window grille',(xx-.4+j*.16,30.35,3.8),(.018,.04,1.1),steel)
 box('Far window sill',(xx,30.30,3.2),(1.1,.3,.13),cement)
box('Far doorway',(1.4,30.39,1.15),(1.1,.09,2.2),wood)
corrugated('Far house patched roof',.3,32.1,5.33,11.5,3.8,iron,.035)
ACTIVE=COL['Roofs and terraces']
for idx,(s,fr,y,w,d,h) in enumerate(buildings):
 if idx in [2,5,9]:
  # A lightweight addition on only part of a terrace gives a layered skyline.
  xx=fr+s*(d-.8);yy=y+.3;box('Rooftop room',(xx,yy,h+.8),(1.55,2.0,1.6),plasters[(idx+1)%6]);corrugated('Rooftop room tin roof',xx,yy,h+1.65,1.9,2.35,iron,s*.1)
 if idx in [1,4,8,11] and h>4:
  # Projecting upper gallery, offset entry and thin steel railing.
  box('Projecting balcony',(fr-s*.43,y,2.75),(.9,w*.68,.14),cement)
  for k in range(int(w*.68/.22)+1):rod('Balcony baluster',(fr-s*.85,y-w*.34+k*.22,2.82),(fr-s*.85,y-w*.34+k*.22,3.65),.014,steel)
  rod('Balcony top rail',(fr-s*.85,y-w*.34,3.65),(fr-s*.85,y+w*.34,3.65),.024,steel)
 if idx in [0,3,7]:
  # Small TV antennas, asymmetrical but anchored to roof structure.
  rod('Roof TV aerial mast',(fr+s*.65,y+.6,h),(fr+s*.65,y+.6,h+1.55),.018,steel)
  for j in range(5):rod('TV aerial element',(fr+s*.65-.35,y+.2+j*.2,h+1.42),(fr+s*.65+.35,y+.2+j*.2,h+1.42),.009,steel)
# A bicycle built from a real frame arrangement rather than a silhouette placeholder.
def bicycle(x,y,angle=0):
 global ACTIVE
 ACTIVE=COL['Domestic props'];parts=[]
 def P(yy,zz,xx=0):return (x+xx,y+yy,zz)
 for yy in [-.54,.54]:
  for radius,thick,ma in [(.34,.029,steel),(.302,.009,silver)]:
   parts.append(curve('Bicycle tyre' if ma==steel else 'Bicycle rim',[P(yy+math.cos(i*math.tau/48)*radius,.36+math.sin(i*math.tau/48)*radius) for i in range(49)],thick,ma))
  for i in range(12):parts.append(rod('Bicycle spoke',P(yy,.36),P(yy+math.cos(i*math.tau/12)*.30,.36+math.sin(i*math.tau/12)*.30),.0025,silver))
 a=P(-.54,.36);b=P(-.12,.82);c=P(.02,.34);d=P(.38,.88);e=P(.54,.36)
 for v,w in [(a,b),(b,c),(c,a),(b,d),(d,c),(d,e)]:parts.append(rod('Bicycle steel frame',v,w,.019,rust))
 rod('Saddle post',b,P(-.15,.98),.018,silver);box('Bicycle saddle',P(-.21,1.0),(.18,.28,.065),steel)
 rod('Handlebar stem',d,P(.37,1.06),.018,silver);rod('Handlebars',P(.37,1.06,-.25),P(.37,1.06,.25),.018,steel)
 rod('Bike crank',P(.02,.34,-.1),P(.02,.34,.15),.013,silver);rod('Bike pedal arm',P(.02,.34,.15),P(.17,.19,.15),.012,silver);box('Bike pedal',P(.17,.19,.15),(.13,.08,.035),steel)
 rod('Bicycle stand',P(-.08,.35),P(-.18,.04,-.16),.008,steel)
bicycle(-1.67,9.3);bicycle(10.7,18.8)
ACTIVE=COL['Domestic props']
# Feed sacks stacked inside workshop recesses.
sack=weather('Coarse woven storage sacks',(.53,.43,.27),None,8)
for x,y,z in [(4.2,20.2,.24),(4.6,20.2,.24),(4.4,20.2,.63)]:
 o=box('Tied storage sack',(x,y,z),(.39,.55,.37),sack,.04)
# A small display of folded cloth and sewing work in the tailor's open front.
for s,fr,y,w,d,h in buildings:
 if s==-1 and 8<y<13:
  box('Tailor work table',(fr+s*.5,y,.82),(.9,1.45,.07),wood)
  for k in range(6):box('Folded fabric',(fr+s*.45,y-.4+k*.13,.91),(.49,.12,.10),random.choice([green,blue,plasters[4],ceramic]))
  box('Sewing machine base',(fr+s*.42,y+.28,.92),(.34,.46,.05),steel);box('Sewing machine column',(fr+s*.52,y+.4,1.05),(.11,.13,.25),steel);box('Sewing machine arm',(fr+s*.52,y+.26,1.17),(.12,.36,.10),steel)
  break
# Doorside footwear gives the housing a maintained, inhabited threshold.
for s,fr,y,w,d,h in buildings[::3]:
 for k in range(2):
  o=box('Sandals at doorstep',(fr-s*.48,y-.55+k*.17,.14),(.24,.10,.035),rust);o.rotation_euler.z=.2
