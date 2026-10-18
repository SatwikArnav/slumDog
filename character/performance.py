# Executed in build.py's scene context.
from mathutils.bvhtree import BVHTree
# Add short beard shading and individual fine stubble on the actual facial surface.
def smoothstep(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def beardmask(p):
 x,y,z=p;ax=abs(x)
 jaw=(1-smoothstep(1.673+ax*.47,1.691+ax*.47,z))*smoothstep(1.59,1.612,z)*(1-smoothstep(-.076,-.045,y))
 lips=(1-smoothstep(.026,.041,ax))*smoothstep(1.645,1.650,z)*(1-smoothstep(1.672,1.677,z))
 moustache=(1-smoothstep(.027,.04,ax))*smoothstep(1.674,1.678,z)*(1-smoothstep(1.687,1.694,z))*(1-smoothstep(-.143,-.122,y))
 sideburn=smoothstep(.063,.075,ax)*(1-smoothstep(.092,.104,ax))*smoothstep(1.683,1.702,z)*(1-smoothstep(1.754,1.769,z))*(1-smoothstep(-.045,-.015,y))
 return max(0,min(1,max(jaw*(1-lips),moustache,sideburn)))*(1-smoothstep(.081,.094,ax))
att=body.data.attributes.new('Stubble mask','FLOAT','POINT')
for vertex,entry in zip(body.data.vertices,att.data):entry.value=beardmask(vertex.co)
nt=skin.node_tree;pr=nt.nodes.get('Principled BSDF');attr=nt.nodes.new('ShaderNodeAttribute');attr.attribute_name='Stubble mask';mul=nt.nodes.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=.58;nt.links.new(attr.outputs['Fac'],mul.inputs[0]);mix=nt.nodes.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[2].default_value=(.027,.019,.014,1);tex=next((x for x in nt.nodes if x.type=='TEX_IMAGE'),None)
if tex:nt.links.new(tex.outputs['Color'],mix.inputs[1])
else:mix.inputs[1].default_value=(.36,.21,.135,1)
nt.links.new(mul.outputs[0],mix.inputs[0]);nt.links.new(mix.outputs[0],pr.inputs['Base Color'])
# Hair colour graded towards dark brown.
hmat=hair.data.materials[0];hpr=hmat.node_tree.nodes.get('Principled BSDF');ht=next(n for n in hmat.node_tree.nodes if n.type=='TEX_IMAGE');hm=hmat.node_tree.nodes.new('ShaderNodeMixRGB');hm.blend_type='MULTIPLY';hm.inputs[0].default_value=1;hm.inputs[2].default_value=(.42,.37,.32,1);hmat.node_tree.links.new(ht.outputs['Color'],hm.inputs[1]);hmat.node_tree.links.new(hm.outputs[0],hpr.inputs['Base Color'])
stubblemat=shader('Short dark beard hair',(.035,.024,.017),.8)
cu=bpy.data.curves.new('Individual stubble','CURVE');cu.dimensions='3D';cu.resolution_u=1;cu.bevel_depth=.00011;cu.bevel_resolution=0
for face in body.data.polygons:
 if not any(beardmask(body.data.vertices[i].co)>.12 for i in face.vertices):continue
 pts=[body.data.vertices[i].co for i in face.vertices]
 for k in range(1,len(pts)-1):
  a,b,c=pts[0],pts[k],pts[k+1];area=(b-a).cross(c-a).length*.5
  for _ in range(int(area*950000)+1):
   q=random.random();r=random.random()
   if q+r>1:q=1-q;r=1-r
   point=a+(b-a)*q+(c-a)*r;m=beardmask(point)
   if random.random()>m:continue
   n=face.normal;root=point+n*.0002;tip=root+n*random.uniform(.0011,.0027)+Vector((0,0,-.0006));sp=cu.splines.new('POLY');sp.points.add(1);sp.points[0].co=(*root,1);sp.points[1].co=(*tip,1)
st=bpy.data.objects.new('Beard • fine surface stubble',cu);bpy.context.collection.objects.link(st);cu.materials.append(stubblemat)
bpy.ops.object.select_all(action='DESELECT');st.select_set(True);bpy.context.view_layer.objects.active=st;bpy.ops.object.convert(target='MESH');st=bpy.context.object;g=st.vertex_groups.new(name='head');g.add(list(range(len(st.data.vertices))),1,'REPLACE');am=st.modifiers.new('Follow head','ARMATURE');am.object=rig
# A small healed brow scar, projected onto the actual facial surface.
bvh=BVHTree.FromPolygons([v.co for v in body.data.vertices],[list(f.vertices) for f in body.data.polygons],all_triangles=False)
scar_points=[]
for i in range(7):
 t=i/6;x=-.059+.006*t;z=1.784-.041*t;hit,n,idx,dist=bvh.ray_cast(Vector((x,-.5,z)),Vector((0,1,0)))
 if hit is not None:scar_points.append(hit+n*.00035)
if len(scar_points)>2:
 sc=bpy.data.curves.new('Healed brow scar','CURVE');sc.dimensions='3D';sc.bevel_depth=.00055;sc.bevel_resolution=2;sp=sc.splines.new('BEZIER');sp.bezier_points.add(len(scar_points)-1)
 for p,co in zip(sp.bezier_points,scar_points):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
 ob=bpy.data.objects.new('Healed brow scar',sc);bpy.context.collection.objects.link(ob);sc.materials.append(shader('Scar tissue',(.42,.24,.17),.65));bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH');ob=bpy.context.object;g=ob.vertex_groups.new(name='head');g.add(list(range(len(ob.data.vertices))),1,'REPLACE');am=ob.modifiers.new('Follow head','ARMATURE');am.object=rig
# Anatomical hand frame. All fingers remain independently editable.
wrist_rest=rigdata.bones['wrist.R'].head_local.copy();long=(rigdata.bones['finger3-1.R'].head_local-wrist_rest).normalized();across=(rigdata.bones['finger2-1.R'].head_local-rigdata.bones['finger5-1.R'].head_local).normalized();normal=across.cross(long).normalized();across=long.cross(normal).normalized();oldframe=Matrix((across,long,normal)).transposed()
def fingerpose(side,finger,joint,flex,spread=0):
 n=f'finger{finger}-{joint}.{side}';pb=rig.pose.bones[n];rest=rigdata.bones[n];d=(rest.tail_local-rest.head_local).normalized();handlong=(rigdata.bones['finger3-1.'+side].head_local-rigdata.bones['wrist.'+side].head_local).normalized();handacross=(rigdata.bones['finger2-1.'+side].head_local-rigdata.bones['finger5-1.'+side].head_local).normalized();handnormal=handacross.cross(handlong).normalized();axis=d.cross(handnormal).normalized();inv=rest.matrix_local.to_quaternion().inverted();pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion(inv@handnormal,spread)@Quaternion(inv@axis,flex)
for side in ['L','R']:
 for finger in range(1,6):
  angles=([.15,.26,.19] if finger in [2,3] and side=='R' else [.25,.55,.40])
  if finger==1:angles=[.12,.20,.16]
  if side=='R' and finger in [4,5]:angles=[.50,.90,.65]
  for joint,a in enumerate(angles,1):fingerpose(side,finger,joint,a)
# Bring the thumb across the palm rather than pointing up against the cheek.
tb=rigdata.bones['finger1-1.R'];fromdir=(tb.tail_local-tb.head_local).normalized();todir=(rigdata.bones['finger3-1.R'].head_local-tb.head_local).normalized();turn=Quaternion().slerp(fromdir.rotation_difference(todir),.68);q=tb.matrix_local.to_quaternion();rig.pose.bones['finger1-1.R'].rotation_quaternion=q.inverted()@turn@q
fingerpose('R',1,2,.45);fingerpose('R',1,3,.35)
# Find a gentle adduction angle that clamps the cigarette between index and middle fingers.
best=(1e9,0)
for i in range(61):
 a=(i-30)*.01;fingerpose('R',2,1,.15,a);fingerpose('R',3,1,.15,-a);bpy.context.view_layer.update()
 p=rig.pose.bones['finger2-1.R'];q=rig.pose.bones['finger3-1.R'];P=p.head.lerp(p.tail,.85);Q=q.head.lerp(q.tail,.65);gap=(P-Q).length
 cost=(gap-.020)**2+.000002*a*a
 if cost<best[0]:best=(cost,a)
fingerpose('R',2,1,.15,best[1]);fingerpose('R',3,1,.15,-best[1]);bpy.context.view_layer.update()
p=rig.pose.bones['finger2-1.R'];q=rig.pose.bones['finger3-1.R'];P=p.head.lerp(p.tail,.85);Q=q.head.lerp(q.tail,.65);grip=(P+Q)*.5
wrist=rig.pose.bones['wrist.R'];unpose=rigdata.bones['wrist.R'].matrix_local@wrist.matrix.inverted();grip_rest=unpose@grip;axis_rest=-normal
butt_rest=grip_rest-axis_rest*.020;tip_rest=grip_rest+axis_rest*.063
paper=shader('Cigarette • off-white paper',(.76,.73,.65),.86);cork=shader('Cigarette • cork filter',(.47,.235,.072),.9);ash=shader('Cigarette • charred ash',(.11,.10,.095),.95);ember=shader('Cigarette • ember',(.24,.014,.002),.7);ep=ember.node_tree.nodes.get('Principled BSDF');ep.inputs['Emission Color'].default_value=(1,.045,.001,1);ep.inputs['Emission Strength'].default_value=.4
# Shared procedural irregularity prevents a uniform glowing bead.
n=ash.node_tree.nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=420;bu=ash.node_tree.nodes.new('ShaderNodeBump');bu.inputs['Strength'].default_value=.8;bu.inputs['Distance'].default_value=.0008;ash.node_tree.links.new(n.outputs['Fac'],bu.inputs['Height']);ash.node_tree.links.new(bu.outputs[0],ash.node_tree.nodes.get('Principled BSDF').inputs['Normal'])
def cylinder_between(name,a,b,r,ma,bone='wrist.R'):
 d=b-a;bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=r,depth=d.length,location=(a+b)*.5);o=bpy.context.object;o.name=name;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(ma)
 for f in o.data.polygons:f.use_smooth=True
 g=o.vertex_groups.new(name=bone);g.add(list(range(len(o.data.vertices))),1,'REPLACE');am=o.modifiers.new('Grip attachment • wrist skin transform','ARMATURE');am.object=rig
 return o
cylinder_between('Cigarette | filter',butt_rest,grip_rest+axis_rest*.006,.0037,cork)
cylinder_between('Cigarette | paper',grip_rest+axis_rest*.006,tip_rest-axis_rest*.006,.0036,paper)
cylinder_between('Cigarette | ember',tip_rest-axis_rest*.006,tip_rest-axis_rest*.003,.00365,ember)
cylinder_between('Cigarette | ash',tip_rest-axis_rest*.003,tip_rest,.0038,ash)
# Continuous action: an arc through an intermediate wrist position, then a held contact.
ctrl=rig.pose.bones['CTRL_hand.R'];idlepos=ctrl.head.copy();idlerot=ctrl.matrix.to_quaternion();idle_pole=rig.pose.bones['CTRL_elbow.R'].head.copy()
targetlong=Vector((.90,0,.435)).normalized();targetnormal=Vector((0,1,0));targetacross=targetlong.cross(targetnormal).normalized();newframe=Matrix((targetacross,targetlong,targetnormal)).transposed();delta=(newframe@oldframe.inverted()).to_quaternion();smokerot=delta@rigdata.bones['wrist.R'].matrix_local.to_quaternion()
lip=Vector((-.012,-.170,1.661));smokepos=lip-delta@(butt_rest-wrist_rest)
# Store references for automated contact check and later inspection.
rig['cigarette_butt_rest']=list(butt_rest);rig['mouth_contact']=list(lip);rig['grip_gap_m']=(P-Q).length
midpos=Vector((-.36,-.24,1.28));midrot=idlerot.slerp(smokerot,.52)
poses=[(1,idlepos,idlerot,idle_pole),(25,idlepos,idlerot,idle_pole),(43,midpos,midrot,Vector((-.58,-.20,1.22))),(68,smokepos,smokerot,Vector((-.55,-.32,1.22))),(91,smokepos,smokerot,Vector((-.55,-.32,1.22))),(108,smokepos,smokerot,Vector((-.55,-.32,1.22))),(132,midpos,midrot,Vector((-.58,-.20,1.22))),(158,idlepos,idlerot,idle_pole),(216,idlepos,idlerot,idle_pole)]
for f,pos,rot,pole in poses:
 control('CTRL_hand.R',pos,rot);ctrl.keyframe_insert('location',frame=f,group='Right hand • smoking');ctrl.keyframe_insert('rotation_quaternion',frame=f,group='Right hand • smoking');control('CTRL_elbow.R',pole);pb=rig.pose.bones['CTRL_elbow.R'];pb.keyframe_insert('location',frame=f,group='Right elbow arc')
# Very subtle breathing, preserving the exact mouth target during contact.
for f,a in [(1,0),(26,.004),(68,0),(108,0),(139,.004),(175,-.002),(216,0)]:
 pb=rig.pose.bones['spine02'];pb.rotation_mode='XYZ';pb.rotation_euler.x=a;pb.keyframe_insert('rotation_euler',frame=f,group='Breathing')
for f,e in [(1,.35),(58,.35),(68,2.8),(92,3.3),(108,.5),(216,.35)]:ep.inputs['Emission Strength'].default_value=e;ep.inputs['Emission Strength'].keyframe_insert('default_value',frame=f)
rig.animation_data.action.name='Smoking • idle, raise, draw, lower, exhale'
scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=216;scene.render.fps=24
for f,n in [(1,'IDLE'),(26,'LIFT'),(68,'CONTACT / DRAW'),(109,'LOWER'),(118,'EXHALE'),(182,'SETTLE')]:scene.timeline_markers.new(n,frame=f)
# Render checks are done at the physical contact frame.
scene.frame_set(80);bpy.context.view_layer.update();wrist=rig.pose.bones['wrist.R'];actual=wrist.matrix@rigdata.bones['wrist.R'].matrix_local.inverted()@butt_rest
print('CIGARETTE CONTACT ERROR m',tuple(actual-lip),'GRIP GAP',rig['grip_gap_m'],flush=True)
