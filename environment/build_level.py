import bpy,math,random,os,json,time
from mathutils import Vector, Matrix
ROOT=os.path.dirname(os.path.abspath(__file__));A=ROOT+'/assets';random.seed(32)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
COL={}
for n in ['Architecture','Roofs and terraces','Street infrastructure','Shopfronts and signs','Domestic props','Reusable CC0 props','Character','Lighting','Cameras','Collision']:
 c=bpy.data.collections.new(n);scene.collection.children.link(c);COL[n]=c
ACTIVE=COL['Architecture']
def link(o):ACTIVE.objects.link(o);return o
def mat(name,col,rough=.8,metal=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;return m
def img(path,noncolor=False):
 i=bpy.data.images.load(path,check_existing=True)
 if noncolor:i.colorspace_settings.name='Non-Color'
 i.pack();return i
def weather(name,col,photo=None,scale=.65):
 m=mat(name,col);n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');tc=n.new('ShaderNodeTexCoord');v=n.new('ShaderNodeVectorMath');v.operation='SCALE';v.inputs[3].default_value=scale;l.new(tc.outputs['Object'],v.inputs[0]);noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=4;noise.inputs['Detail'].default_value=5;l.new(v.outputs[0],noise.inputs['Vector'])
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=tuple(x*.78 for x in col)+(1,);ramp.color_ramp.elements[1].color=tuple(min(1,x*1.12) for x in col)+(1,);l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color'])
 if photo and os.path.exists(A+'/'+photo):
  t=n.new('ShaderNodeTexImage');t.image=img(A+'/'+photo);t.projection='BOX';t.projection_blend=.15;l.new(v.outputs[0],t.inputs['Vector']);mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;l.new(t.outputs[0],mix.inputs[1]);l.new(ramp.outputs[0],mix.inputs[2]);paint=n.new('ShaderNodeMixRGB');paint.inputs[0].default_value=.60;l.new(mix.outputs[0],paint.inputs[1]);l.new(ramp.outputs[0],paint.inputs[2]);l.new(paint.outputs[0],p.inputs['Base Color'])
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.45;bump.inputs['Distance'].default_value=.018;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal']);return m
plasters=[weather('Plaster • '+n,c,'plaster_diff.jpg') for n,c in [('ochre',(.72,.59,.36)),('faded turquoise',(.30,.55,.48)),('chalk',(.76,.72,.60)),('blue wash',(.38,.50,.60)),('rose wash',(.64,.42,.34)),('cement',(.45,.46,.41))]]
cement=weather('Old concrete',(.42,.40,.34),'plaster_diff.jpg',.7);ground=weather('Lane concrete • repairs and aggregate',(.27,.26,.23),None,1.4);brick=weather('Exposed fired clay',(.48,.21,.105),None,2);mortar=mat('Dusty mortar',(.36,.32,.25));iron=weather('Galvanized roofing with patina',(.63,.59,.49),'iron_diff.jpg',.5);iron.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value=.55
rust=weather('Rust brown steel',(.20,.105,.048),None,3);steel=mat('Old painted black metal',(.035,.046,.043),.47,.65);wood=weather('Worn timber',(.27,.15,.065),None,3);dark=mat('Interior shadow',(.023,.03,.026));glass=mat('Dusty dark window glass',(.045,.082,.092),.24,.25);blue=weather('Blue tarpaulin',(.025,.17,.40),None,2);green=weather('Faded green tarpaulin',(.15,.28,.18),None,3);red=mat('Painted red cylinder',(.32,.027,.018),.53,.35);ceramic=mat('Off-white ceramic',(.76,.73,.61),.27);silver=mat('Brushed steel utensils',(.48,.49,.45),.27,.85);water=mat('Dark shallow puddles',(.055,.065,.055),.11,.3);soil=mat('Potting soil',(.075,.045,.022));leaf=mat('Leaves',(.10,.22,.055),.63)
unit=bpy.data.meshes.new('Shared unit box');unit.from_pydata([(-.5,-.5,-.5),(.5,-.5,-.5),(.5,.5,-.5),(-.5,.5,-.5),(-.5,-.5,.5),(.5,-.5,.5),(.5,.5,.5),(-.5,.5,.5)],[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
# Each material shares a box mesh; object-space coordinates are set to world metres below.
boxmeshes={}
def box(n,loc,dims,ma,bevel=0):
 if ma.name not in boxmeshes:me=unit.copy();me.materials.append(ma);boxmeshes[ma.name]=me
 o=link(bpy.data.objects.new(n,boxmeshes[ma.name]));o.location=loc;o.scale=dims
 if bevel:
  mod=o.modifiers.new('Soft manufactured edges','BEVEL');mod.width=bevel;mod.segments=2
 return o
cylmeshes={}
def cyl(n,loc,r,depth,ma,verts=16,r2=None):
 key=(ma.name,verts,round(r2/r,3) if r2 is not None else 1)
 if key not in cylmeshes:
  ratio=key[2];vs=[(math.cos(i*math.tau/verts)*rad,math.sin(i*math.tau/verts)*rad,z) for z,rad in [(-.5,1),(.5,ratio)] for i in range(verts)];fs=[tuple(reversed(range(verts))),tuple(range(verts,verts*2))]+[(i,(i+1)%verts,(i+1)%verts+verts,i+verts) for i in range(verts)];me=bpy.data.meshes.new(n);me.from_pydata(vs,[],fs);me.materials.append(ma)
  for f in me.polygons:f.use_smooth=len(f.vertices)==4
  cylmeshes[key]=me
 o=link(bpy.data.objects.new(n,cylmeshes[key]));o.location=loc;o.scale=(r,r,depth);return o
def rod(n,a,b,r,ma):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)*.5,r,(b-a).length,ma,12);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def curve(n,points,r,ma):
 cu=bpy.data.curves.new(n,'CURVE');cu.dimensions='3D';cu.resolution_u=1;cu.bevel_depth=r;cu.bevel_resolution=1;s=cu.splines.new('POLY');s.points.add(len(points)-1)
 for p,co in zip(s.points,points):p.co=(*co,1)
 ob=link(bpy.data.objects.new(n,cu));cu.materials.append(ma);return ob
def panel(n,verts,ma):
 me=bpy.data.meshes.new(n);me.from_pydata(verts,[],[(0,1,2,3)]);me.materials.append(ma);uv=me.uv_layers.new()
 for i,p in enumerate([(0,0),(1,0),(1,1),(0,1)]):uv.data[i].uv=p
 return link(bpy.data.objects.new(n,me))
def imagematerial(name,file,alpha=False):
 m=mat(name,(1,1,1));n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');t=n.new('ShaderNodeTexImage');t.image=img(A+'/'+file);l.new(t.outputs['Color'],p.inputs['Base Color'])
 if alpha:l.new(t.outputs['Alpha'],p.inputs['Alpha']);m.blend_method='HASHED';m.use_nodes=True;m.use_screen_refraction=False;m.diffuse_color=(.2,.2,.1,.2);m.use_backface_culling=False;m.shadow_method='NONE'
 return m
signmats={n:imagematerial(n,n+'.png') for n in ['tea_sign','kirana_sign','tailor_sign','repair_sign','lane_sign','menu','poster']};moist=imagematerial('Water staining decal','moisture.png',True)
def frontpanel(n,s,x,y,z,w,h,ma):
 # Readable front UV orientation on both sides of the street.
 u=-s
 return panel(n,[(x,y-u*w/2,z-h/2),(x,y+u*w/2,z-h/2),(x,y+u*w/2,z+h/2),(x,y-u*w/2,z+h/2)],ma)
def sign(n,s,front,y,z,w,h,key):
 box(n+' board',(front,y,z),(.055,w,h),wood);return frontpanel(n,s,front-s*.033,y,z,w*.97,h*.91,signmats[key])
def corrugated(n,cx,cy,z,dx,dy,ma,slope=0):
 vs=[];ny=max(12,int(dy/.035))
 for x in [-dx/2,dx/2]:
  for j in range(ny+1):
   y=-dy/2+dy*j/ny;vs.append((cx+x,cy+y,z+x*slope+.025*math.cos(y*math.tau/.18)))
 fs=[(j,j+1,j+1+ny+1,j+ny+1) for j in range(ny)];me=bpy.data.meshes.new(n);me.from_pydata(vs,[],fs);me.materials.append(ma);return link(bpy.data.objects.new(n,me))
def brickpatch(s,front,y,z,w,h):
 box('Exposed mortar patch',(front-s*.009,y,z),(.025,w,h),mortar)
 for row in range(int(h/.085)):
  for col in range(int(w/.24)):
   yy=y-w/2+col*.24+(row%2)*.11
   if yy>y+w/2-.10:continue
   o=box('Uneven exposed brick',(front-s*.035,yy,z-h/2+row*.085+.04),(.07,.222,.066),brick);o.rotation_euler.x=random.uniform(-.015,.015)
def grille(s,front,y,z,w,h):
 box('Window recess',(front,y,z),(.045,w,h),dark);box('Dusty window',(front-s*.025,y,z),(.012,w*.91,h*.91),glass)
 for u in [-w/2,w/2]:box('Window steel frame',(front-s*.07,y+u,z),(.08,.065,h+.1),rust)
 for zz in [z-h/2,z+h/2]:box('Window steel frame',(front-s*.07,y,zz),(.08,w,.065),rust)
 for u in range(1,max(2,int(w/.17))):box('Security grille',(front-s*.12,y-w/2+u*.17,z),(.025,.018,h),steel)
 box('Window ledge',(front-s*.16,y,z-h/2-.08),(.38,w+.18,.12),cement)
def shutter(s,front,y,z,w,h,color):
 box('Shutter inset',(front,y,z),(.08,w+.1,h+.08),dark)
 for i in range(int(h/.075)):box('Rolling shutter slat',(front-s*.06,y,z-h/2+i*.075),(.065,w,.064),color)
 box('Shutter lock',(front-s*.12,y,z-h/2+.1),(.08,.16,.1),steel)
def plant(x,y,z=0):
 cyl('Clay plant pot',(x,y,z+.16),.16,.32,brick,20,.22);cyl('Soil',(x,y,z+.323),.19,.018,soil)
 for i in range(8):
  ang=i*2.4;tip=Vector((x+math.cos(ang)*random.uniform(.18,.34),y+math.sin(ang)*.22,z+random.uniform(.45,.75)));rod('Plant stem',(x,y,z+.32),tip,.006,leaf)
  for t in [.55,.85]:
   c=Vector((x,y,z+.32)).lerp(tip,t);d=Vector((math.cos(ang+1)*.14,math.sin(ang+1)*.14,.05));panel('Plant leaf',[c,c+d+Vector((.035,0,.025)),c+d*1.7,c+d-Vector((.035,0,.025))],leaf)
# World-space material coordinates preserve real texture size across differently sized modules.
anchor=link(bpy.data.objects.new('Material metre coordinates',None))
for m in list(bpy.data.materials):
 if m.use_nodes:
  for node in m.node_tree.nodes:
   if node.type=='TEX_COORD':node.object=anchor
ACTIVE=COL['Street infrastructure']
box('Concrete lane foundation',(0,12,-.15),(5.1,34,.3),ground)
box('Courtyard ground',(6.0,18,-.14),(11.5,8,.28),ground)
box('Entrance road',(0,-4,-.17),(27,6,.32),ground)
# Low plinths and open drain channels, crossed at doorways.
for s in [-1,1]:
 box('Dark drain bed',(s*2.02,12,-.075),(.26,30,.07),dark)
 for j in range(55):
  y=-1.5+j*.55;box('Broken pavement edging',(s*2.26,y,.025),(.28,.51,random.uniform(.06,.1)),cement)
  if j%5!=2:
   for k in range(5):box('Drain grate',(s*2.02,y-.2+k*.09,.015),(.25,.026,.025),steel)
 for j in range(12):
  y=random.uniform(-1,27);box('Concrete repair',(s*random.uniform(.4,1.6),y,.004),(random.uniform(.3,.8),random.uniform(.4,1.3),.012),random.choice([cement,ground]))
for i in range(18):
 x=random.uniform(-1.7,1.7);y=random.uniform(-2,27);r=random.uniform(.15,.65);v=[(x,y,.018)]+[(x+math.cos(k*math.tau/18)*r*random.uniform(.8,1.1),y+math.sin(k*math.tau/18)*r*.55*random.uniform(.8,1.1),.018) for k in range(18)];me=bpy.data.meshes.new('Puddle');me.from_pydata(v,[],[(0,k+1,(k+1)%18+1) for k in range(18)]);me.materials.append(water);link(bpy.data.objects.new('Shallow rainwater',me))
# Dense low-rise shells, varied incremental additions, and distinct frontage uses.
buildings=[]
for s in [-1,1]:
 y=-.2
 for i in range(7):
  width=[3.6,4.2,3.8,4.7,4.0,4.4,3.8][i];cy=y+width/2;front=s*(2.35+random.uniform(-.27,.38));depth=random.uniform(3.6,5.4);levels=([2,1,2,3,2,1,2][i] if s==-1 else [2,2,1,2,2,3,2][i]);height=2.72+(levels-1)*2.42;ma=plasters[(i+(2 if s<0 else 0))%len(plasters)]
  # Right-hand courtyard opening creates a branching route.
  if s==1 and i==4:y+=width;continue
  ACTIVE=COL['Architecture'];buildings.append((s,front,cy,width,depth,height))
  box('Rear wall',(front+s*depth,cy,height/2),(.22,width,height),ma)
  for edge in [-1,1]:box('Party wall',(front+s*depth/2,cy+edge*width/2,height/2),(depth,.20,height),ma)
  for floor in range(levels+1):
   zz=0 if floor==0 else 2.72+(floor-1)*2.42
   box('Concrete floor slab',(front+s*depth/2,cy,zz),(depth+.20,width+.20,.16),cement)
  # Ground front kept open between pillars; actual interior depth is visible.
  for edge in [-1,1]:box('Front pier',(front,cy+edge*(width/2-.16),1.35),(.27,.32,2.7),ma)
  box('Shop lintel',(front,cy,2.48),(.3,width,.5),ma)
  box('Shop back wall',(front+s*1.4,cy,1.22),(.09,width-.3,2.4),dark)
  shop=(s==1 and i in [1,2]) or (s==-1 and i in [0,2,4])
  if not shop:
   box('Ground facade infill',(front,cy,1.18),(.23,width-.5,2.3),ma);shutter(s,front-s*.14,cy-.4,1.13,1.05,2.13,random.choice([steel,green,plasters[3]]));grille(s,front-s*.13,cy+width*.27,1.65,.65,.75)
  for floor in range(1,levels):
   z0=2.72+(floor-1)*2.42
   box('Upper facade',(front-s*random.choice([0,.12,.22]),cy,z0+1.21),(.23,width,2.42),ma)
   for u in [-.25,.25]:grille(s,front-s*.19,cy+width*u,z0+1.3,random.uniform(.65,.9),1.05)
   box('Facade horizontal beam',(front-s*.18,cy,z0+.08),(.34,width+.12,.16),cement)
  for u in [-.37,.36]:frontpanel('Rain and drain staining',s,front-s*.133,cy+width*u,1.0,.6,1.8,moist)
  if i%3==2:brickpatch(s,front-s*.14,cy-width*.24,.65,.9,.65)
  ACTIVE=COL['Roofs and terraces']
  if i%3==1:
   box('Terrace parapet',(front-s*.1,cy,height+.35),(.18,width+.15,.7),ma)
   for u in [-1,1]:box('Terrace side parapet',(front+s*depth/2,cy+u*width/2,height+.35),(depth,.16,.7),ma)
   for j in range(2):
    tx=front+s*(depth-.8-j*.9);ty=cy+.5;cyl('Black rooftop water tank',(tx,ty,height+.65),.5,1.15,steel,32);cyl('Tank lid',(tx,ty,height+1.25),.52,.06,steel,32)
    for k in range(6):cyl('Water tank rib',(tx,ty,height+.18+k*.17),.515,.025,steel,32)
  else:
   corrugated('Overlapping corrugated roof',front+s*depth/2,cy,height+.12,depth+.65,width+.65,iron,s*.09)
   for u in [-.28,.24]:rod('Roof batten',(front-s*.35,cy+width*u,height+.10),(front+s*(depth+.3),cy+width*u,height+.10+s*(depth+.65)*s*.09),.025,rust)
   # Loose bricks hold down repaired sheets.
   for k in range(5):box('Roof sheet ballast',(front+s*random.uniform(.3,depth),cy+random.uniform(-width*.4,width*.4),height+.25),(.23,.11,.08),brick)
  if i in [0,1,3,5]:
   corrugated('Shopfront tin awning',front-s*.57,cy,2.53,1.35,width+.25,iron,-s*.18)
   for u in [-.4,.4]:rod('Awning brace',(front,cy+width*u,2.0),(front-s*1.15,cy+width*u,2.43),.018,rust)
  ACTIVE=COL['Street infrastructure'];rod('Exterior PVC downpipe',(front-s*.27,cy+width*.43,.18),(front-s*.27,cy+width*.43,height+.35),.035,cement)
  for zz in [.4,1.8,3.1,4.6]:box('Pipe wall clip',(front-s*.25,cy+width*.43,zz),(.10,.11,.035),steel)
  # Exterior meter cabinet and surface wiring.
  box('Electric meter box',(front-s*.2,cy+width*.35,1.8),(.22,.27,.38),steel);curve('Surface conduit',[(front-s*.24,cy+width*.35,1.8),(front-s*.24,cy+width*.35,3.05),(front-s*.24,cy-width*.4,3.05)],.012,steel)
  ACTIVE=COL['Shopfronts and signs']
  if shop:
   key='tea_sign' if s==1 and i==1 else 'kirana_sign' if s==-1 and i==0 else 'tailor_sign' if s==-1 and i==2 else 'repair_sign'
   sign('Hand-painted local shop board',s,front-s*.22,cy,2.19,width*.87,.49,key)
   box('Worn shop step',(front-s*.38,cy,.09),(.9,width-.4,.18),cement)
   if key!='tea_sign':
    for level in range(3):box('Shop shelving',(front+s*.75,cy,.55+level*.49),(.45,width-.7,.06),wood)
    for k in range(18):
     box('Shop stock',(front+s*.68,cy+random.uniform(-width*.35,width*.35),.71+(k%3)*.49),(.24,.17,.27),random.choice([red,ceramic,green,blue,wood]))
   if key=='tea_sign':tea=(s,front,cy,width)
  ACTIVE=COL['Domestic props']
  if not shop:
   plant(front-s*.52,cy+width*.37)
   for k in range(2):cyl('Household bucket',(front-s*.52,cy-width*.27+k*.32,.18),.13,.33,random.choice([blue,green,ceramic]),20,.16)
  # Clothes lines sit above the lane and follow plausible attachment points.
  if i in [1,3,5]:
   z=3.35;curve('Clothes line',[(front-s*.3,cy-1.1,z),(front-s*.47,cy,z-.18),(front-s*.3,cy+1.2,z)],.007,wood)
   for k in range(5):
    yy=cy-.9+k*.43;ma2=random.choice([blue,ceramic,green,plasters[4]]);o=panel('Drying laundry',[(front-s*.5,yy,3.24),(front-s*.53,yy+.34,3.22),(front-s*.60,yy+.35,2.56),(front-s*.56,yy+.02,2.58)],ma2)
  y+=width
print('BUILDINGS',len(buildings),flush=True)
# Recessed courtyard closes the right branch with working facades and an upper gallery.
ACTIVE=COL['Architecture']
for x in [5,8.5,12]:
 box('Courtyard workshop',(x,22.3,2.65),(3.4,3.2,5.3),random.choice(plasters));box('Workshop dark doorway',(x,20.66,1.15),(1.15,.025,2.2),dark);box('Workshop timber door',(x+.39,20.62,1.15),(.38,.08,2.2),wood)
 for xx in [-.85,.85]:
  box('Upper courtyard window',(x+xx,20.64,3.85),(.8,.07,1.0),glass)
  for t in range(5):box('Courtyard grille',(x+xx-.32+t*.16,20.57,3.85),(.018,.035,1.0),steel)
 corrugated('Courtyard workshop roof',x,22.3,5.4,3.7,3.8,iron,.05)
box('Upper gallery landing',(8.5,20.15,2.75),(10.5,.95,.15),cement)
for xx in [3.5+i*.5 for i in range(21)]:rod('Gallery baluster',(xx,19.69,2.8),(xx,19.69,3.7),.018,steel)
rod('Gallery rail',(3.3,19.69,3.7),(13.7,19.69,3.7),.027,steel)
# Stair flight rises beside the courtyard wall.
for j in range(16):box('Exterior stair tread',(12.8,16.0+j*.24,.085+j*.17),(1.05,.28,.16),cement)
rod('Stair handrail',(12.25,15.9,.95),(12.25,19.8,3.65),.024,steel)
for j in range(0,16,3):rod('Stair rail upright',(12.25,16+j*.24,j*.17),(12.25,16+j*.24,j*.17+.95),.018,steel)
# Background massing extends the settlement beyond the detailed slice.
for side in [-1,1]:
 for i in range(9):
  x=side*random.uniform(9,17);y=random.uniform(-1,32);h=random.uniform(4.2,8.5);box('Background settlement mass',(x,y,h/2),(random.uniform(3,5),random.uniform(3,5),h),random.choice(plasters))
ACTIVE=COL['Street infrastructure']
for y in [1.5,11,22.5]:
 rod('Utility pole',(-2.2,y,0),(-2.2,y,7.4),.065,wood);rod('Utility crossarm',(-2.8,y,6.9),(-1.6,y,6.9),.04,wood)
 for j in range(5):
  x0=-2.6+j*.2;pts=[(x0+.14*math.sin(t*math.pi),y+t*10,6.8-(.7+j*.07)*math.sin(t*math.pi)) for t in [k/24 for k in range(25)]];curve('Sagging overhead service cable',pts,.009 if j<3 else .015,steel)
for y,z in [(5.4,5.0),(14.2,5.7),(22,5.5)]:
 for j in range(4):curve('Cross-lane wires',[(-3,y+j*.15,z),(0,y+.3+j*.15,z-.55),(3,y+j*.15,z+.15)],.008,steel)
# Blue sheet canopy: irregular edge, tension points, and creased centre.
ACTIVE=COL['Roofs and terraces']
vs=[];nx=12;ny=16
for i in range(nx+1):
 for j in range(ny+1):
  x=-2.5+5*i/nx;y=10+3.1*j/ny;z=4.45-.45*math.sin(math.pi*i/nx)*math.sin(math.pi*j/ny)+.045*math.sin(j*2.7+i*.8);vs.append((x,y,z))
fs=[(i*(ny+1)+j,(i+1)*(ny+1)+j,(i+1)*(ny+1)+j+1,i*(ny+1)+j+1) for i in range(nx) for j in range(ny)];me=bpy.data.meshes.new('Tarp creases');me.from_pydata(vs,[],fs);me.materials.append(blue);link(bpy.data.objects.new('Tensioned blue tarp canopy',me))
for x in [-2.5,2.5]:curve('Canopy tie rope',[(x,10,4.45),(x*1.2,9.5,4.7)],.012,wood)
# Tea stall: counter, kettle, glasses, snacks, hanging packets and working light.
ACTIVE=COL['Domestic props'];s,front,cy,w=tea
box('Tea counter base',(front-.37,cy,.55),(.65,w*.68,1.1),plasters[1]);box('Tea counter stone top',(front-.40,cy,1.12),(.84,w*.73,.08),cement)
for k in range(8):cyl('Tea glass',(front-.48,cy-.7+k*.19,1.25),.037,.14,ceramic,16,.043)
cyl('Tea kettle body',(front-.25,cy+.6,1.37),.15,.34,silver,32,.11);cyl('Kettle lid',(front-.25,cy+.6,1.57),.125,.035,silver,32);cyl('Kettle lid knob',(front-.25,cy+.6,1.61),.027,.05,steel)
rod('Kettle spout',(front-.30,cy+.7,1.43),(front-.51,cy+.78,1.52),.035,silver)
curve('Kettle handle',[(front-.1,cy+.5,1.3),(front+.04,cy+.45,1.4),(front+.02,cy+.48,1.58),(front-.09,cy+.53,1.58)],.022,steel)
box('Tea stove',(front-.16,cy+.6,1.21),(.4,.43,.12),steel)
cyl('LPG cylinder',(front+.22,cy+.9,.40),.17,.75,red,24,.15);cyl('Cylinder valve',(front+.22,cy+.9,.82),.04,.08,steel)
curve('Gas hose',[(front+.22,cy+.9,.82),(front+.38,cy+.82,1.02),(front+.10,cy+.64,1.22)],.012,rust)
for k in range(9):
 o=box('Hanging snack packets',(front+.07,cy-w*.29+k*.26,2.03),(.07,.18,.26),random.choice([red,blue,green,ceramic]));o.rotation_euler.x=random.uniform(-.1,.1)
sign('Tea stall menu',s,front-.17,cy+w*.36,1.57,.59,.61,'menu')
for yy in [cy-1.55,cy+1.55]:
 box('Timber bench seat',(front-.95,yy,.48),(.48,1.0,.10),wood)
 for u in [-.35,.35]:box('Bench leg',(front-.95,yy+u,.23),(.33,.07,.46),steel)
# Reuse real scanned CC0 chair and water drum meshes.
ACTIVE=COL['Reusable CC0 props'];templates={}
for file in ['chair.blend','drum.blend']:
 with bpy.data.libraries.load(A+'/'+file,link=False) as (src,dst):dst.objects=[n for n in src.objects if n in ['plastic_monobloc_chair_01','Barrel_02']]
 for ob in dst.objects:
  if not ob or ob.type!='MESH':continue
  # Replace missing external map paths with downloaded JPG maps; fall back to appropriate material only when absent.
  for ma in ob.data.materials:
   if ma and ma.use_nodes:
    for node in ma.node_tree.nodes:
     if node.type=='TEX_IMAGE' and node.image:
      old=node.image.name
      if 'metal' in old:
       for out in node.outputs:
        for l in list(out.links):ma.node_tree.links.remove(l)
       ma.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value=0
       continue
      kind='diff' if 'diff' in old else 'nor_gl' if 'nor' in old else 'roughness' if ob.name=='Barrel_02' else 'rough';path=A+'/'+ob.name+'_'+kind+'.jpg'
      if os.path.isfile(path):node.image=img(path,kind!='diff')
      elif 'metal' in old:
       for out in node.outputs:
        for l in list(out.links):ma.node_tree.links.remove(l)
      else:node.image=None
  templates[file]=ob
positions={'chair.blend':[(1.15,8.3,0,.5),(4.6,18.2,0,-.6),(-1.45,2.1,0,-1.2)],'drum.blend':[(-1.65,14,0,0),(7.2,20,0,0),(1.7,23,0,0)]}
for file,ps in positions.items():
 ob=templates.get(file)
 if not ob:continue
 for i,(x,y,z,rz) in enumerate(ps):
  o=ob.copy();o.data=ob.data;ACTIVE.objects.link(o);o.location=(x,y,z);o.rotation_euler=(0,0,rz);o.scale=(1,1,1)
# Courtyard activity, storage, pots, a handcart, and sparse street litter.
ACTIVE=COL['Domestic props']
for i in range(14):
 x=random.uniform(4.4,8.5);y=random.uniform(19.2,20.3);h=random.uniform(.18,.36);cyl('Earthenware pot',(x,y,h/2),h*.48,h,brick,20,h*.36)
for i in range(8):box('Stored timber offcut',(11.7,20.1,.08+i*.09),(1.2,.25,.065),wood)
for x,y in [(-1.55,17.1),(3.9,19.5),(9.3,20),(-1.55,24)]:plant(x,y)
# Handcart with thin wheels: dark tyres and metal axle.
box('Handcart deck',(5.8,17.6,.60),(1.3,.8,.10),wood)
for x in [5.3,6.3]:
 o=cyl('Cart wheel',(x,17.6,.36),.32,.07,steel,32);o.rotation_euler.y=math.pi/2
rod('Cart axle',(5.2,17.6,.36),(6.4,17.6,.36),.04,steel)
for x in [5.35,6.25]:rod('Cart handle',(x,17.4,.6),(x,15.8,.95),.025,rust)
for i in range(16):
 x=random.choice([-1,1])*random.uniform(1.65,1.85);y=random.uniform(-1,25);o=box('Small paper scrap',(x,y,.03),(random.uniform(.06,.15),.10,.003),ceramic);o.rotation_euler.z=random.uniform(0,6)
# Wall-mounted notices and the lane name board.
ACTIVE=COL['Shopfronts and signs'];sign('Lane name plate',1,2.06,.5,3.0,1.15,.42,'lane_sign')
for s,fr,y,w,d,h in buildings:
 if random.random()<.45:frontpanel('Local paper notice',s,fr-s*.15,y+w*.3,1.3,.33,.47,signmats['poster'])
exec(compile(open(ROOT+'/street_details.py').read(),ROOT+'/street_details.py','exec'))
# Lighting fixtures, believable illumination under shop awnings.
ACTIVE=COL['Lighting']
for loc in [(front-.05,cy,2.17),(-2.1,1.8,2.18),(-2.15,10,2.18),(8,20.3,2.55)]:
 lampmat=mat('Warm tube phosphor '+str(loc),(1,.72,.39));p=lampmat.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(1,.63,.28,1);p.inputs['Emission Strength'].default_value=3;rod('Shop tube lamp',(loc[0],loc[1]-.34,loc[2]),(loc[0],loc[1]+.34,loc[2]),.022,lampmat)
 data=bpy.data.lights.new('Shop warm practical','AREA');data.energy=35;data.color=(1,.66,.36);data.shape='DISK';data.size=.8;o=link(bpy.data.objects.new('Shop warm practical',data));o.location=loc;o.rotation_euler=(0,math.pi/2 if loc[0]<0 else -math.pi/2,0)
world=bpy.data.worlds.new('Mumbai late afternoon sky');world.use_nodes=True;world.node_tree.nodes.get('Background').inputs[0].default_value=(.33,.43,.52,1);world.node_tree.nodes.get('Background').inputs[1].default_value=.55;scene.world=world
sun=bpy.data.lights.new('Late afternoon sun','SUN');sun.energy=2.8;sun.angle=math.radians(12);o=link(bpy.data.objects.new('Late afternoon sun',sun));o.rotation_euler=(math.radians(34),math.radians(-26),math.radians(-35))
sky=bpy.data.lights.new('Open sky fill','AREA');sky.energy=4700;sky.shape='DISK';sky.size=25;o=link(bpy.data.objects.new('Open sky fill',sky));o.location=(0,12,13)
# Append the actual rigged character and its materials/action, excluding the studio.
ACTIVE=COL['Character']
character_path=ROOT+'/character/Rook_Rebuilt.blend'
if not os.path.isfile(character_path):character_path=os.path.abspath(ROOT+'/../character/Rook_Rebuilt.blend')
if os.path.isfile(character_path):
 with bpy.data.libraries.load(character_path,link=False) as (src,dst):
  dst.objects=[n for n in src.objects if n.startswith(('ROOK','Human','Eyes','Field jacket','Leather work','Short textured','Eyebrows','Beard','Healed brow','Cigarette','Smoke'))]
 for ob in dst.objects:
  if ob:ACTIVE.objects.link(ob)
 rig=next(o for o in dst.objects if o and o.type=='ARMATURE');rig.pose.bones['CTRL_master'].matrix=Matrix.Translation(Vector((.82,5.45,0)))@Matrix.Rotation(-math.pi/2,4,'Z')@rig.data.bones['CTRL_master'].matrix_local;rig.show_in_front=False
 # Hidden studio widgets are not needed for scene playback; bones remain editable.
 for pb in rig.pose.bones:
  if pb.custom_shape:pb.custom_shape=None
# Camera animation: one continuous walking-height move through the street.
ACTIVE=COL['Cameras'];data=bpy.data.cameras.new('Street walkthrough');cam=link(bpy.data.objects.new('Street walkthrough',data));data.lens=25;data.clip_start=.07;data.clip_end=150;scene.camera=cam
for f,pos,target in [(1,(-.7,-3.2,1.65),(1.0,7.5,2.05)),(70,(-.75,3.6,1.67),(1.3,8.4,1.85)),(135,(-.4,10.4,1.72),(.5,17.7,2.0)),(192,(1.0,16.5,1.78),(7.0,20.5,2.15))]:
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.keyframe_insert('location',frame=f);cam.keyframe_insert('rotation_euler',frame=f)
for fc in cam.animation_data.action.fcurves:
 for k in fc.keyframe_points:k.interpolation='LINEAR'
# Named, simple collision volumes are supplied separately from visual detail.
ACTIVE=COL['Collision']
for s,fr,y,w,d,h in buildings:
 o=box('COL_building',(fr+s*d/2,y,h/2),(d,w,h),dark);o.display_type='WIRE';o.hide_render=True
COL['Collision'].hide_viewport=True
scene.render.engine='BLENDER_EEVEE';scene.eevee.use_gtao=True;scene.eevee.gtao_distance=2.4;scene.eevee.gtao_factor=1.25;scene.eevee.use_soft_shadows=True;scene.eevee.taa_render_samples=32;scene.eevee.use_ssr=True;scene.eevee.use_ssr_refraction=True;scene.eevee.volumetric_tile_size='8';scene.eevee.volumetric_samples=32;scene.eevee.volumetric_start=.1;scene.eevee.volumetric_end=35
scene.render.resolution_x=1280;scene.render.resolution_y=800;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.fps=24;scene.frame_start=1;scene.frame_end=216
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.5
exec(compile(open(ROOT+'/polish.py').read(),ROOT+'/polish.py','exec'))
for title,f in [('Entry',1),('Tea stall',70),('Under the tarp',135),('Workshop courtyard',192)]:scene.timeline_markers.new(title,frame=f)
scene['Environment']='Shanti Nagar • fictional Mumbai-inspired basti';scene['Scope']='Detailed 28m gully, tea stall and adjoining workshop courtyard, surrounding settlement massing';scene['Units']='metres';scene['Source credits']='Poly Haven CC0 materials, plastic monobloc chair by Kuutti Siitonen, Barrel 02 by Jorge Camacho; MakeHuman CC0 character from previous deliverable; original scene and local signage.'
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
for screen in bpy.data.screens:
 for ar in screen.areas:
  if ar.type=='VIEW_3D':ar.spaces.active.shading.type='MATERIAL';ar.spaces.active.region_3d.view_location=(0,10,2);ar.spaces.active.region_3d.view_distance=22
scene.frame_set(70);bpy.context.view_layer.update()
for im in bpy.data.images:
 if im.source=='FILE' and im.has_data and not im.packed_file:
  try:im.pack()
  except:pass
readme=bpy.data.texts.new('START HERE • environment and credits');readme.write(open(ROOT+'/README.md').read())
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/Shanti_Nagar_Level.blend',compress=True)
report={'objects':len(scene.objects),'buildings':len(buildings),'packed_images':sum(bool(i.packed_file) for i in bpy.data.images),'character_rig':rig.name if 'rig' in globals() else None};json.dump(report,open(ROOT+'/scene_report.json','w'),indent=2);print('SAVED',report,flush=True)
# Review frames first; animation is rendered only after visual inspection.
for f,n in [(1,'Entry'),(70,'Tea_Stall'),(192,'Courtyard')]:
 scene.frame_set(f);scene.render.filepath=ROOT+'/Shanti_Nagar_'+n+'.png';bpy.ops.render.render(write_still=True)
