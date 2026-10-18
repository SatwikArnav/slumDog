import bpy,math
from mathutils import Vector
# Keep upper windows outside the façade face; projected balconies carry the extensions.
lin=[o for o in bpy.data.objects if o.name.startswith('Shop lintel')]
upper=[o for o in bpy.data.objects if o.name.startswith('Upper facade')]
for o in upper:
 nearest=min(lin,key=lambda p:abs(p.location.y-o.location.y)+10*(p.location.x*o.location.x<0))
 o.location.x=nearest.location.x
# Stronger weathering at ground level, lighter paint above the splash zone.
for ma in bpy.data.materials:
 if not ma.name.startswith('Plaster •') or not ma.use_nodes:continue
 nt=ma.node_tree;p=nt.nodes.get('Principled BSDF');n=next((n for n in nt.nodes if n.type=='MIX_RGB' and n.blend_type=='MIX'),None)
 if not n:continue
 geom=nt.nodes.new('ShaderNodeNewGeometry');sep=nt.nodes.new('ShaderNodeSeparateXYZ');ran=nt.nodes.new('ShaderNodeMapRange');ran.inputs['From Min'].default_value=0;ran.inputs['From Max'].default_value=1.7;ran.inputs['To Min'].default_value=.12;ran.inputs['To Max'].default_value=.52;ran.clamp=True;nt.links.new(geom.outputs['Position'],sep.inputs[0]);nt.links.new(sep.outputs['Z'],ran.inputs[0]);nt.links.new(ran.outputs[0],n.inputs[0])
# Real-sized brick courses on two incrementally extended upper storeys.
ma=bpy.data.materials.new('Unfinished brick upper storeys');ma.use_nodes=True;nt=ma.node_tree;p=nt.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.95
geo=nt.nodes.new('ShaderNodeNewGeometry');sep=nt.nodes.new('ShaderNodeSeparateXYZ');combine=nt.nodes.new('ShaderNodeCombineXYZ');nt.links.new(geo.outputs['Position'],sep.inputs[0]);nt.links.new(sep.outputs['Y'],combine.inputs['X']);nt.links.new(sep.outputs['Z'],combine.inputs['Y']);b=nt.nodes.new('ShaderNodeTexBrick');b.inputs['Color1'].default_value=(.39,.16,.065,1);b.inputs['Color2'].default_value=(.59,.29,.13,1);b.inputs['Mortar'].default_value=(.29,.27,.22,1);b.inputs['Scale'].default_value=2.25;b.inputs['Mortar Size'].default_value=.025;b.inputs['Brick Width'].default_value=.5;b.inputs['Row Height'].default_value=.23;nt.links.new(combine.outputs[0],b.inputs['Vector']);nt.links.new(b.outputs['Color'],p.inputs['Base Color']);bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.4;bump.inputs['Distance'].default_value=.012;nt.links.new(b.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs[0],p.inputs['Normal'])
for o in upper:
 if (o.location.x<0 and 8<o.location.y<12 and o.location.z<4.2) or (o.location.x>0 and 23<o.location.y<27 and o.location.z<4.2):
  s=1 if o.location.x>0 else -1;x=o.location.x-s*.119;y=o.location.y;w=o.scale.y;z=o.location.z;h=o.scale.z
  me=bpy.data.meshes.new('Exposed brick frontage');me.from_pydata([(x,y-w/2,z-h/2),(x,y+w/2,z-h/2),(x,y+w/2,z+h/2),(x,y-w/2,z+h/2)],[],[(0,1,2,3)]);me.materials.append(ma);ob=bpy.data.objects.new('Brick extension above painted home',me);bpy.data.collections['Architecture'].objects.link(ob)
# Daylight gradient instead of a flat grey background.
w=bpy.context.scene.world;nt=w.node_tree;sky=nt.nodes.new('ShaderNodeTexSky');sky.sky_type='NISHITA';sky.sun_elevation=math.radians(34);sky.sun_rotation=math.radians(-35);sky.air_density=1.2;sky.dust_density=2.0;sky.ozone_density=1.0;sky.sun_disc=False;bg=nt.nodes.get('Background');nt.links.new(sky.outputs[0],bg.inputs[0]);bg.inputs[1].default_value=.22
for l in bpy.data.lights:
 if l.type=='SUN':l.color=(1,.87,.70)
 if l.name=='Open sky fill':l.color=(.83,.90,1)
# Very subtle laundry motion; walls and props stay static and reusable.
for ob in bpy.data.objects:
 if ob.name.startswith('Drying laundry'):
  ob.rotation_euler.y=-.025;ob.keyframe_insert('rotation_euler',frame=1);ob.rotation_euler.y=.025;ob.keyframe_insert('rotation_euler',frame=108);ob.rotation_euler.y=-.025;ob.keyframe_insert('rotation_euler',frame=216)
# Ground supports all background buildings and the complete courtyard/stair footprint.
base_mat=bpy.data.materials['Lane concrete • repairs and aggregate']
verts=[(-22.5,-9.5,-.31),(22.5,-9.5,-.31),(22.5,35.5,-.31),(-22.5,35.5,-.31),(-22.5,-9.5,-.01),(22.5,-9.5,-.01),(22.5,35.5,-.01),(-22.5,35.5,-.01)]
me=bpy.data.meshes.new('Continuous neighbourhood foundation');me.from_pydata(verts,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);me.materials.append(base_mat);ob=bpy.data.objects.new('Continuous neighbourhood foundation',me);bpy.data.collections['Street infrastructure'].objects.link(ob)
for ob in bpy.data.objects:
 if ob.name=='Courtyard ground':ob.location.x=7;ob.scale.x=15
