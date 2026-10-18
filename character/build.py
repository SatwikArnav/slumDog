import bpy, math, json, os, random
import time
print("BUILD START",time.time(),flush=True)
from mathutils import Vector, Quaternion, Matrix
ROOT=os.path.dirname(os.path.abspath(__file__)); A=ROOT+'/assets';random.seed(12)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def objdata(path):
 vs=[];uv=[];fs=[];ft=[];groups=[];group=''
 for l in open(path):
  a=l.split()
  if not a:continue
  if a[0]=='v':vs.append(Vector(tuple(map(float,a[1:4]))))
  elif a[0]=='vt':uv.append(tuple(map(float,a[1:3])))
  elif a[0]=='g':group=a[1]
  elif a[0]=='f':
   ids=[x.split('/') for x in a[1:]];fs.append([int(x[0])-1 for x in ids]);ft.append([int(x[1])-1 if len(x)>1 and x[1] else 0 for x in ids]);groups.append(group)
 return vs,uv,fs,ft,groups
base,uv,faces,fuv,groups=objdata(A+'/base.obj');v=[x.copy() for x in base]
MORPHS={'caucasian-male-young':.72,'caucasian-male-old':.28,'universal-male-young-maxmuscle-averageweight':.72,'universal-male-old-maxmuscle-averageweight':.28,'chin-width-incr':.22,'chin-bones-incr':.18,'l-cheek-bones-incr':.18,'r-cheek-bones-incr':.18,'l-cheek-volume-decr':.15,'r-cheek-volume-decr':.15,'l-eye-height2-decr':.12,'r-eye-height2-decr':.12,'eyebrows-trans-down':.10}
for n,amount in MORPHS.items():
 for l in open(A+'/'+n+'.target'):
  a=l.split()
  if len(a)==4 and not a[0].startswith('#'):v[int(a[0])]+=Vector(tuple(map(float,a[1:])))*amount
bodyinds={i for f,g in zip(faces,groups) if g=='body' for i in f};bottom=min(v[i].y for i in bodyinds);top=max(v[i].y for i in bodyinds);scale=1.87/(top-bottom)
def cv(p):return Vector((p.x*scale,-p.z*scale,(p.y-bottom)*scale))
V=[cv(x) for x in v]
sk=json.load(open(A+'/default.mhskel'));weights=json.load(open(A+'/default_weights.mhw'))['weights']
def jt(n):return sum((V[i] for i in sk['joints'][n]),Vector())/len(sk['joints'][n])
def alias(n):
 if n is None:return None
 for pre in ['upperarm','lowerarm','upperleg','lowerleg']:
  if n.startswith(pre+'02'):return n.replace('02','01')
 return n
# Preserve the anatomical face/finger hierarchy, merge only twist halves into full limb segments.
rigdata=bpy.data.armatures.new('Anatomical skeleton');rig=bpy.data.objects.new('ROOK • skin rig',rigdata);bpy.context.collection.objects.link(rig);bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for n,b in sk['bones'].items():
 if alias(n)!=n:continue
 eb=rigdata.edit_bones.new(n);eb.head=jt(b['head']);eb.tail=jt(b['tail'])
 if n.startswith(('upperarm01','upperleg01')):eb.tail=jt(sk['bones'][n.replace('01','02')]['tail'])
 if n.startswith(('lowerarm01','lowerleg01')):eb.tail=jt(sk['bones'][n.replace('01','02')]['tail'])
 if (eb.tail-eb.head).length<.0001:eb.tail=eb.head+Vector((0,0,.005))
 plane=sk['planes'].get(b.get('rotation_plane'))
 if plane:
  p=[jt(x) for x in plane];normal=(p[1]-p[0]).cross(p[2]-p[0]);
  if normal.length>.00001:eb.align_roll(normal)
for n,b in sk['bones'].items():
 if alias(n)!=n:continue
 if b['parent']:rigdata.edit_bones[n].parent=rigdata.edit_bones[alias(b['parent'])]
# Control layer
for s in ['L','R']:
 for src,ctrl in [('wrist.'+s,'CTRL_hand.'+s),('foot.'+s,'CTRL_foot.'+s)]:
  bone=rigdata.edit_bones[src];e=rigdata.edit_bones.new(ctrl);e.head=bone.head;e.tail=bone.tail;e.roll=bone.roll;e.use_deform=False
 for n,pos in [('CTRL_elbow.'+s,rigdata.edit_bones['lowerarm01.'+s].head+Vector((.35 if s=='L' else -.35,.2,0))),('CTRL_knee.'+s,rigdata.edit_bones['lowerleg01.'+s].head+Vector((0,-.5,0)))]:
  e=rigdata.edit_bones.new(n);e.head=pos;e.tail=pos+Vector((0,0,.08));e.use_deform=False
bpy.ops.object.mode_set(mode='OBJECT');rig.show_in_front=True
VW=[{} for _ in V]
for bn,entries in weights.items():
 bn=alias(bn)
 for i,w in entries:
  if i<len(V):VW[i][bn]=VW[i].get(bn,0)+w

def shader(name,color,rough=.5,metal=0,tex=None):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if tex and os.path.exists(tex):
  t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(tex,check_existing=True);t.image.pack();m.node_tree.links.new(t.outputs['Color'],p.inputs['Base Color'])
 return m
skintex=next((A+'/'+n for n in ['skin.png','middleage_lightskinned_male_diffuse.png'] if os.path.exists(A+'/'+n)),None)
skin=shader('Weathered skin • albedo + pores',(.36,.21,.135),.48,tex=skintex)
p=skin.node_tree.nodes.get('Principled BSDF');p.inputs['Subsurface Weight'].default_value=.065
noise=skin.node_tree.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=550;noise.inputs['Detail'].default_value=2;bump=skin.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.0006;skin.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);skin.node_tree.links.new(bump.outputs[0],p.inputs['Normal'])
cloth=shader('Charcoal cotton',(.035,.041,.043),.83);denim=shader('Faded black denim',(.035,.041,.045),.88);leather=shader('Worn boot leather',(.038,.021,.012),.54)
def mesh(name,verts,fs,uvs,fts,mat,ws=None,sub=1):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],fs);me.update();ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);me.materials.append(mat)
 if uvs:
  layer=me.uv_layers.new(name='UVMap')
  for poly,ids in zip(me.polygons,fts):
   for li,ti in zip(poly.loop_indices,ids):layer.data[li].uv=uvs[ti]
 for p in me.polygons:p.use_smooth=True
 if ws:
  names={n for w in ws for n in w};gs={n:ob.vertex_groups.new(name=n) for n in names if n in rigdata.bones}
  for i,w in enumerate(ws):
   tot=sum(max(x,0) for n,x in w.items() if n in gs)
   if tot:
    for n,x in w.items():
     if n in gs and x>1e-6:gs[n].add([i],x/tot,'REPLACE')
  a=ob.modifiers.new('Skin • normalized anatomical weights','ARMATURE');a.object=rig;a.use_deform_preserve_volume=True
 if sub:
  m=ob.modifiers.new('Surface subdivision','SUBSURF');m.levels=sub;m.render_levels=sub
 return ob
# Keep original indices for mapping; helper faces never become visible geometry.
bodyfaces=[f for f,g in zip(faces,groups) if g=='body'];bodyuv=[f for f,g in zip(fuv,groups) if g=='body']
body=mesh('Human • continuous skin',V,bodyfaces,uv,bodyuv,skin,VW,2)
print('BODY BUILT',time.time(),flush=True)

def proxy(name,mhclo,ma,sub=1):
 cfg={};rows=[];mode=False
 for l in open(A+'/'+mhclo):
  a=l.split()
  if not a or a[0].startswith('#'):continue
  if a[0]=='verts':mode=True;continue
  if mode and a[0][0].isdigit() and len(a) in [1,9]:rows.append(a)
  elif mode:mode=False
  if not mode:cfg[a[0]]=a[1:]
 fn=cfg['obj_file'][0];pv,pu,pf,pt,pg=objdata(A+'/'+fn);factors=[]
 for ax in ['x','y','z']:
  z=cfg.get(ax+'_scale');factors.append(abs(v[int(z[0])]['xyz'.index(ax)]-v[int(z[1])]['xyz'.index(ax)])/float(z[2]) if z else 1)
 new=[];ww=[]
 for row in rows:
  if len(row)==1:i=int(row[0]);new.append(V[i]);ww.append(VW[i]);continue
  ids=list(map(int,row[:3]));ts=list(map(float,row[3:6]));off=Vector(tuple(float(row[6+j])*factors[j] for j in range(3)));pos=sum((v[i]*t for i,t in zip(ids,ts)),Vector())+off;new.append(cv(pos));w={}
  for i,t in zip(ids,ts):
   for bn,val in VW[i].items():w[bn]=w.get(bn,0)+val*t
  ww.append(w)
 assert len(new)==len(pv),(name,len(new),len(pv))
 return mesh(name,new,pf,pu,pt,ma,ww,sub)
eye=shader('Eyes • brown iris',(.45,.37,.27),.22,tex=A+'/brown_eye.png');et=next(n for n in eye.node_tree.nodes if n.type=='TEX_IMAGE');eye.node_tree.links.new(et.outputs['Alpha'],eye.node_tree.nodes.get('Principled BSDF').inputs['Alpha']);eye.blend_method='HASHED';eye.shadow_method='NONE';eyes=proxy('Eyes','high-poly.mhclo',eye,1)
# Fitted garment geometry carries interpolated skin weights from its anatomical binding.
def textured_asset(name,file,texture,normal=None,cutout=False,sub=1):
 ma=shader(name+' material',(1,1,1),.67,tex=A+'/'+texture)
 p=ma.node_tree.nodes.get('Principled BSDF')
 if normal and os.path.exists(A+'/'+normal):
  tn=ma.node_tree.nodes.new('ShaderNodeTexImage');tn.image=bpy.data.images.load(A+'/'+normal,check_existing=True);tn.image.colorspace_settings.name='Non-Color';tn.image.pack();nm=ma.node_tree.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.45;ma.node_tree.links.new(tn.outputs['Color'],nm.inputs['Color']);ma.node_tree.links.new(nm.outputs[0],p.inputs['Normal'])
 if cutout:
  tex=next(n for n in ma.node_tree.nodes if n.type=='TEX_IMAGE');ma.node_tree.links.new(tex.outputs['Alpha'],p.inputs['Alpha']);ma.blend_method='HASHED';ma.shadow_method='HASHED';p.inputs['Roughness'].default_value=.58
 return proxy(name,file,ma,sub)
outfit=textured_asset('Field jacket • shirt • jeans','male_casualsuit05.mhclo','male_casualsuit05_diffuse.png','male_casualsuit05_normal.png',sub=2)
boots=textured_asset('Leather work shoes','shoes04.mhclo','shoes04_diffuse.png','shoes04_normal.png',sub=1)
hair=textured_asset('Short textured hair','short02.mhclo','short02_diffuse.png','short02_normal.png',True,1)
brows=textured_asset('Eyebrows','eyebrow005.mhclo','eyebrow005.png',cutout=True,sub=1)
bm=brows.data.materials[0];bp=bm.node_tree.nodes.get('Principled BSDF');bt=next(n for n in bm.node_tree.nodes if n.type=='TEX_IMAGE');mix=bm.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(.20,.15,.1,1);bm.node_tree.links.new(bt.outputs['Color'],mix.inputs[1]);bm.node_tree.links.new(mix.outputs[0],bp.inputs['Base Color'])
# Delete only the body faces explicitly hidden by the garment authors.
import re,bmesh
hidden=set()
for f in ['male_casualsuit05.mhclo','shoes04.mhclo']:
 text=open(A+'/'+f).read().split('delete_verts')[-1]
 for a,b,c in re.findall(r'(\d+)\s*-\s*(\d+)|(\d+)',text):
  if c:hidden.add(int(c))
  else:hidden.update(range(int(a),int(b)+1))
maskgroup=body.vertex_groups.new(name='Covered by outfit • toggle mask to reveal full body');maskgroup.add([i for i in hidden if i<len(body.data.vertices)],1,'REPLACE');maskmod=body.modifiers.new('Clothing coverage • non-destructive','MASK');maskmod.vertex_group=maskgroup.name;maskmod.invert_vertex_group=True;bpy.context.view_layer.objects.active=body;bpy.ops.object.modifier_move_to_index(modifier=maskmod.name,index=0)
print('OUTFIT BUILT',time.time(),flush=True)
paused_mods=[m for o in bpy.context.scene.objects if o.type=='MESH' for m in o.modifiers if m.show_viewport]
for m in paused_mods:m.show_viewport=False
# Four limb IK controls, with explicit pole targets. Full limb bones retain the supplied smooth weights.
for side in ['R','L']:
 for limb,end,control,pole in [('arm','lowerarm01.','CTRL_hand.','CTRL_elbow.'),('leg','lowerleg01.','CTRL_foot.','CTRL_knee.')]:
  c=rig.pose.bones[end+side].constraints.new('IK');c.name=limb+' IK';c.target=rig;c.subtarget=control+side;c.chain_count=2;c.use_stretch=False;c.pole_target=rig;c.pole_subtarget=pole+side
 target=rig.pose.bones['wrist.'+side];c=target.constraints.new('COPY_ROTATION');c.target=rig;c.subtarget='CTRL_hand.'+side;c.owner_space='WORLD';c.target_space='WORLD'
 target=rig.pose.bones['foot.'+side];c=target.constraints.new('COPY_ROTATION');c.target=rig;c.subtarget='CTRL_foot.'+side;c.owner_space='WORLD';c.target_space='WORLD'
def control(n,position,rotation=None):
 pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';m=rigdata.bones[n].matrix_local
 pb.location=m.to_3x3().inverted()@(Vector(position)-m.translation)
 if rotation:pb.rotation_quaternion=m.to_quaternion().inverted()@rotation
 bpy.context.view_layer.update()
# Lower the hands into a natural relaxed stance. Orient palms inward and fingers down.
for side,sg in [('R',-1),('L',1)]:
 # hand's local anatomical long and across axes form a frame
 wrist=rigdata.bones['wrist.'+side].head_local
 long=(rigdata.bones['finger3-1.'+side].head_local-wrist).normalized()
 across=(rigdata.bones['finger2-1.'+side].head_local-rigdata.bones['finger5-1.'+side].head_local).normalized()
 normal=across.cross(long).normalized();across=long.cross(normal).normalized()
 old=Matrix((across,long,normal)).transposed()
 newlong=Vector((.08*sg,-.1,-1)).normalized();newnormal=Vector((-sg,0,0));newacross=newlong.cross(newnormal).normalized();newnormal=newacross.cross(newlong).normalized();new=Matrix((newacross,newlong,newnormal)).transposed();delta=(new@old.inverted()).to_quaternion()
 rot=delta@rigdata.bones['wrist.'+side].matrix_local.to_quaternion()
 control('CTRL_hand.'+side,(sg*.32,-.04,.99),rot)
 control('CTRL_elbow.'+side,(sg*.53,.12,1.26))
 # Calibrate the solver's pole convention against an outward, slightly rearward elbow.
 c=rig.pose.bones['lowerarm01.'+side].constraints.get('arm IK');best=(1e9,0);desired=Vector((sg*.34,.045,1.27))
 for i in range(72):
  c.pole_angle=-math.pi+i*math.tau/72;bpy.context.view_layer.update();err=(rig.pose.bones['lowerarm01.'+side].head-desired).length_squared
  if err<best[0]:best=(err,c.pole_angle)
 c.pole_angle=best[1]
 # Keep the legs close to their rest pose while respecting their knee target.
 c=rig.pose.bones['lowerleg01.'+side].constraints.get('leg IK');best=(1e9,0);desired=rigdata.bones['lowerleg01.'+side].head_local
 for i in range(72):
  c.pole_angle=-math.pi+i*math.tau/72;bpy.context.view_layer.update();err=(rig.pose.bones['lowerleg01.'+side].head-desired).length_squared
  if err<best[0]:best=(err,c.pole_angle)
 c.pole_angle=best[1]
bpy.context.view_layer.update()
print('IK CALIBRATED',time.time(),flush=True)
exec(compile(open(ROOT+'/performance.py').read(),ROOT+'/performance.py','exec'))
print('PERFORMANCE BUILT',time.time(),flush=True)
exec(compile(open(ROOT+'/smoke.py').read(),ROOT+'/smoke.py','exec'))
print('SMOKE BUILT',time.time(),flush=True)
for m in paused_mods:m.show_viewport=True
# Rest joint evidence for precise posing
info={n:{'head':list(b.head_local),'tail':list(b.tail_local),'matrix':[list(row) for row in b.matrix_local]} for n,b in rigdata.bones.items()}
json.dump(info,open(ROOT+'/joints.json','w'),indent=2)
def area(n,pos,color,power,size,target=(0,0,1.3)):
 bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.name=n;o.data.energy=power;o.data.color=color;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
floor=shader('Studio floor',(.018,.022,.027),.7);bpy.ops.mesh.primitive_plane_add(size=200);bpy.context.object.data.materials.append(floor);bpy.context.object.location.z=min(v.co.z for v in boots.data.vertices)-.001
area('Key softbox',(-2.7,-3.5,3.2),(1,.82,.65),300,2.7);area('Rim',(2,1.7,2.8),(.52,.69,1),450,2);area('Face bounce',(1.3,-3,2.0),(.8,.9,1),70,2)
bpy.ops.object.camera_add(location=(-3.2,-6.7,2.2));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,1.0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.22
s=bpy.context.scene;s.camera=cam;s.render.engine='BLENDER_EEVEE';s.eevee.taa_render_samples=32;s.eevee.use_gtao=True;s.eevee.gtao_distance=.2;s.eevee.gtao_factor=1.15;s.eevee.use_soft_shadows=True;s.world.color=(.06,.06,.06);s.render.resolution_x=700;s.render.resolution_y=900;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX';s.render.image_settings.file_format='PNG';s.render.filepath=ROOT+'/contact_check.png';s.render.fps=24
exec(compile(open(ROOT+'/finalize.py').read(),ROOT+'/finalize.py','exec'))
