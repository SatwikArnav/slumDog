# Executed from build.py after the complete scene has been assembled.
import json
scene=bpy.context.scene
# Add a master without changing any rest-space or keyed transforms.
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');e=rigdata.edit_bones.new('CTRL_master');e.head=(0,0,0);e.tail=(0,0,.2);e.use_deform=False
for b in rigdata.edit_bones:
 if b.name!='CTRL_master' and (b.name.startswith('CTRL_') or b.parent is None):b.parent=e
bpy.ops.object.mode_set(mode='OBJECT')
controls=rigdata.collections.new('Controls');fingers=rigdata.collections.new('Fingers');deform=rigdata.collections.new('Deformation');face=rigdata.collections.new('Face')
faceprefix=('oris','oculi','levator','risorius','temporalis','orbicularis','tongue','special','jaw','eye.')
for b in rigdata.bones:
 if b.name.startswith('CTRL_'):controls.assign(b);b.color.palette='THEME04' if b.name.endswith('.L') else 'THEME03' if b.name.endswith('.R') else 'THEME09'
 elif b.name.startswith(('finger','metacarpal')):fingers.assign(b)
 elif b.name.startswith(faceprefix):face.assign(b)
 else:deform.assign(b)
fingers.is_visible=False;deform.is_visible=False;face.is_visible=False
widgets=bpy.data.collections.new('Rig widgets');scene.collection.children.link(widgets);widgets.hide_render=True
for kind,size in [('hand',.045),('foot',.065),('pole',.028),('master',.43)]:
 if kind=='master':vs=[(size*math.cos(i*math.tau/48),0,size*math.sin(i*math.tau/48)) for i in range(48)];es=[(i,(i+1)%48) for i in range(48)]
 else:
  vs=[(x*size,y*size,z*size) for x,y,z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]];es=[(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
 me=bpy.data.meshes.new(kind+' control');me.from_pydata(vs,es,[]);o=bpy.data.objects.new('WGT_'+kind,me);widgets.objects.link(o);o.hide_render=True;o.hide_set(True)
 for pb in rig.pose.bones:
  if (kind=='master' and pb.name=='CTRL_master') or (kind in ['hand','foot'] and pb.name.startswith('CTRL_'+kind)) or (kind=='pole' and pb.name.startswith(('CTRL_elbow','CTRL_knee'))):pb.custom_shape=o;pb.use_custom_shape_bone_size=False
# Carry art-directed smoke with the character's master control.
for smoke_obj in [mouthsmoke,tipsmoke]:
 c=smoke_obj.constraints.new('CHILD_OF');c.name='Follow character master';c.target=rig;c.subtarget='CTRL_master';c.inverse_matrix=(rig.matrix_world@rigdata.bones['CTRL_master'].matrix_local).inverted()
# Validate visible mesh weights and held contact with evaluated constraints.
report={'bones':len(rigdata.bones),'skin_vertices':len(body.data.vertices),'contact_errors_m':{},'weight_issues':[]}
for ob in [body,outfit,boots,eyes,hair,brows]:
 names={g.index:g.name for g in ob.vertex_groups};used={i for f in ob.data.polygons for i in f.vertices};bad=0
 for i in used:
  total=sum(g.weight for g in ob.data.vertices[i].groups if names[g.group] in rigdata.bones)
  if abs(total-1)>.002:bad+=1
 if bad:report['weight_issues'].append([ob.name,bad])
for f in [68,80,91,108]:
 scene.frame_set(f);bpy.context.view_layer.update();wr=rig.pose.bones['wrist.R'];actual=wr.matrix@rigdata.bones['wrist.R'].matrix_local.inverted()@Vector(rig['cigarette_butt_rest']);error=(actual-Vector(rig['mouth_contact'])).length;report['contact_errors_m'][str(f)]=error
assert max(report['contact_errors_m'].values())<.001,report
assert not report['weight_issues'],report
json.dump(report,open(ROOT+'/rig_validation.json','w'),indent=2);print('RIG VALIDATION',report,flush=True)
readme=bpy.data.texts.new('START HERE • instructions and credits');readme.write(open(ROOT+'/README.md').read())
# Default camera frames the complete smoking performance from the waist up.
cam.location=(-2.8,-6.5,2.05);cam.rotation_euler=(Vector((0,-.05,1.34))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.34
scene.render.resolution_x=640;scene.render.resolution_y=800;scene.render.resolution_percentage=100;scene.eevee.taa_render_samples=32;scene.render.image_settings.file_format='PNG';scene.render.filepath='//frames/'
scene.frame_set(1)
# Comfortable initial viewport and useful timeline limits.
for area_ in bpy.context.screen.areas:
 if area_.type=='VIEW_3D':area_.spaces.active.region_3d.view_location=(0,0,1.05);area_.spaces.active.region_3d.view_distance=3.2;area_.spaces.active.shading.type='MATERIAL'
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
for title,frame in [('Idle',1),('Raise',26),('Draw • lip contact',68),('Lower hand',109),('Exhale',118),('Return to idle',158),('End',216)]:scene.timeline_markers.new(title,frame=frame)
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/Rook_Rebuilt.blend',compress=True)
# Full body and contact portrait, using the final geometry.
cam.location=(-3.2,-6.7,2.2);cam.rotation_euler=(Vector((0,0,1.0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=2.22;scene.frame_set(80);scene.render.resolution_x=700;scene.render.resolution_y=1000;scene.render.filepath=ROOT+'/Rook_FullBody.png';bpy.ops.render.render(write_still=True)
cam.location=(-1.4,-3.8,1.92);cam.rotation_euler=(Vector((-.03,-.08,1.61))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.70;scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.filepath=ROOT+'/Rook_Portrait.png';bpy.ops.render.render(write_still=True)
if os.environ.get('ROOK_RENDER_ANIMATION')=='1':
 cam.location=(-2.8,-6.5,2.05);cam.rotation_euler=(Vector((0,-.05,1.34))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.34
 scene.render.resolution_x=640;scene.render.resolution_y=800;scene.render.resolution_percentage=75;scene.eevee.taa_render_samples=8;scene.eevee.volumetric_samples=32;scene.eevee.volumetric_tile_size='4';scene.eevee.volumetric_start=5;scene.eevee.volumetric_end=9;scene.eevee.volumetric_sample_distribution=0
 os.makedirs(ROOT+'/frames',exist_ok=True)
 for f in range(1,217,2):scene.frame_set(f);scene.render.filepath=ROOT+'/frames/%04d.png'%f;bpy.ops.render.render(write_still=True)
