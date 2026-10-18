# Analytic, animated participating-media fields. No particle balls or external caches.
def smoke_material(name,tip=False):
 m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;nt.nodes.clear();n=nt.nodes;L=nt.links
 out=n.new('ShaderNodeOutputMaterial');vol=n.new('ShaderNodeVolumePrincipled');vol.inputs['Color'].default_value=(.63,.66,.69,1);vol.inputs['Anisotropy'].default_value=.15;L.new(vol.outputs['Volume'],out.inputs['Volume'])
 tc=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');L.new(tc.outputs['Generated'],sep.inputs[0])
 def mathnode(op,a,b=None):
  o=n.new('ShaderNodeMath');o.operation=op
  for i,val in enumerate([a,b]):
   if val is None:continue
   if isinstance(val,(int,float)):o.inputs[i].default_value=val
   else:L.new(val,o.inputs[i])
  return o.outputs[0]
 def ramp(inp,stops):
  r=n.new('ShaderNodeValToRGB');r.color_ramp.elements.remove(r.color_ramp.elements[1]);e=r.color_ramp.elements[0];e.position=stops[0][0];e.color=(stops[0][1],)*3+(1,)
  for t,x in stops[1:]:e=r.color_ramp.elements.new(t);e.color=(x,x,x,1)
  r.color_ramp.interpolation='EASE';L.new(inp,r.inputs[0]);return r.outputs['Color']
 z=sep.outputs['Z'];x=mathnode('SUBTRACT',sep.outputs['X'],.5);y=mathnode('SUBTRACT',sep.outputs['Y'],.5)
 # A widening curved centreline, broken up by animated 3-D turbulence.
 phase=n.new('ShaderNodeValue');phase.name='Flow time'
 for f,val in [(1,0),(216,3.8)]:phase.outputs[0].default_value=val;phase.outputs[0].keyframe_insert('default_value',frame=f)
 bend=mathnode('MULTIPLY',mathnode('SINE',mathnode('ADD',mathnode('MULTIPLY',z,8 if tip else 5),phase.outputs[0])),.09 if tip else .045)
 x=mathnode('SUBTRACT',x,mathnode('MULTIPLY',bend,z));y=mathnode('SUBTRACT',y,mathnode('MULTIPLY',mathnode('MULTIPLY',z,z),.15))
 radius=mathnode('ADD',mathnode('MULTIPLY',z,.28 if tip else .34),.065 if tip else .035)
 radius2=mathnode('MULTIPLY',radius,radius);r2=mathnode('DIVIDE',mathnode('ADD',mathnode('MULTIPLY',x,x),mathnode('MULTIPLY',y,y)),radius2)
 radial=ramp(r2,[(0,1),(.18,.92),(.68,.28),(1,0)])
 tail=ramp(z,[(0,.65),(.04,1),(.55,.75),(1,0)])
 mapping=n.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(3,3,12);L.new(tc.outputs['Generated'],mapping.inputs[0]);add=n.new('ShaderNodeVectorMath');add.operation='ADD';L.new(mapping.outputs[0],add.inputs[0]);combine=n.new('ShaderNodeCombineXYZ');L.new(mathnode('MULTIPLY',phase.outputs[0],-2),combine.inputs['Z']);L.new(combine.outputs[0],add.inputs[1]);noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=2.1;noise.inputs['Detail'].default_value=4;noise.inputs['Roughness'].default_value=.7;L.new(add.outputs[0],noise.inputs['Vector']);turb=ramp(noise.outputs['Fac'],[(.22,0),(.43,.35),(.62,1),(.85,.7)])
 power=n.new('ShaderNodeValue');power.name='Smoke density'
 if tip:
  power.outputs[0].default_value=7
  front=1
 else:
  for f,d in [(1,0),(116,0),(123,4),(141,7),(158,5),(180,1.7),(199,0),(216,0)]:power.outputs[0].default_value=d;power.outputs[0].keyframe_insert('default_value',frame=f)
  lead=n.new('ShaderNodeValue');lead.name='Exhale front'
  for f,val in [(1,-.1),(116,-.1),(126,.2),(145,.62),(172,1.2),(216,1.2)]:lead.outputs[0].default_value=val;lead.outputs[0].keyframe_insert('default_value',frame=f)
  front=ramp(mathnode('SUBTRACT',z,lead.outputs[0]),[(0,1),(.08,0)])
 density=mathnode('MULTIPLY',mathnode('MULTIPLY',radial,tail),mathnode('MULTIPLY',turb,power.outputs[0]));density=mathnode('MULTIPLY',density,front);L.new(density,vol.inputs['Density'])
 return m

def volume_box(name,ma,dims,loc,rot=None):
 # Cube vertices run from local Z=0 to 1; the emitter is at the base centre.
 vs=[(x,y,z) for z in [0,1] for y in [-.5,.5] for x in [-.5,.5]];fs=[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)]
 o=mesh(name,vs,fs,[],[],ma,None,0);o.location=loc;o.scale=dims
 if rot:o.rotation_euler=rot
 return o
mouthsmoke=volume_box('Smoke • continuous exhale',smoke_material('Exhaled smoke • turbulent field'),(.24,.23,.55),lip+Vector((0,-.008,0)),(math.pi/2,0,0))
# local +Y points up and local +Z points away from the lips (-world Y).
for f,offset in [(1,0),(116,0),(145,.005),(175,.045),(199,.085),(216,.085)]:mouthsmoke.location=lip+Vector((0,-.008,offset));mouthsmoke.keyframe_insert('location',frame=f)
tipsmoke=volume_box('Smoke • ember wisp',smoke_material('Ember smoke • thin rising field',True),(.055,.055,.26),tip_rest)
for f in range(1,218,3):
 scene.frame_set(min(f,216));bpy.context.view_layer.update();w=rig.pose.bones['wrist.R'];tipsmoke.location=w.matrix@rigdata.bones['wrist.R'].matrix_local.inverted()@tip_rest;tipsmoke.keyframe_insert('location',frame=min(f,216))
# Purse the mouth very subtly during the exhale. Existing face bones remain available.
body.shape_key_add(name='Basis');key=body.shape_key_add(name='Exhale • lip purse')
for vtx,d in zip(body.data.vertices,key.data):
 p=vtx.co;mask=(1-smoothstep(.022,.042,abs(p.x)))*smoothstep(1.637,1.650,p.z)*(1-smoothstep(1.680,1.692,p.z))*(1-smoothstep(-.135,-.115,p.y))
 d.co.x-=p.x*.12*mask;d.co.y-=.0025*mask;d.co.z+=(-.0009 if p.z<1.661 else .0005)*mask
for f,val in [(1,0),(113,0),(126,1),(153,1),(184,0),(216,0)]:key.value=val;key.keyframe_insert('value',frame=f)
scene.eevee.volumetric_tile_size='2';scene.eevee.volumetric_samples=96;scene.eevee.volumetric_start=.01;scene.eevee.volumetric_end=12;scene.eevee.volumetric_sample_distribution=.5
scene.frame_set(80)
