"""Original Indian street-dog asset. blender -b --python game/build_dog.py"""
from pathlib import Path
import bpy
import math
import json
import sys
from mathutils import Vector, Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dog_navigation import collect_navigation

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'game/assets'
OUT.mkdir(exist_ok=True)


def navigation():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'environment/Shanti_Nagar_Level.blend'))
    buildings,obstacles = collect_navigation()
    metadata = json.loads((OUT/'scene.json').read_text())
    metadata['collision'] = buildings
    metadata['dog_obstacles'] = obstacles
    (OUT/'scene.json').write_text(json.dumps(metadata,separators=(',',':')))


navigation()
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
skin_parts = []


def ellipsoid(name,position,scale,parts=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=10,location=position)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if parts is not None:
        parts.append(o)
    return o


def segment(name,a,b,radius,parts):
    a,b = Vector(a),Vector(b)
    o = ellipsoid(name,(a+b)/2,(radius,radius,(b-a).length*.62),parts)
    o.rotation_euler = (b-a).to_track_quat('Z','Y').to_euler()
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    return o


ellipsoid('Lean ribcage',(0,-.015,.43),(.135,.30,.155),skin_parts)
ellipsoid('Deep chest',(0,-.20,.42),(.14,.14,.18),skin_parts)
ellipsoid('Tucked abdomen',(0,.23,.445),(.105,.15,.115),skin_parts)
neck = ellipsoid('Sloping neck',(0,-.29,.52),(.095,.105,.175),skin_parts)
neck.rotation_euler.x = .48
ellipsoid('Wedge skull',(0,-.43,.615),(.103,.125,.10),skin_parts)
ellipsoid('Long tapered muzzle',(0,-.558,.563),(.068,.12,.057),skin_parts)
ellipsoid('Cheeks',(0,-.465,.56),(.09,.085,.075),skin_parts)

bones = {'root':((0,.30,.43),(0,-.23,.43),None),
         'neck':((0,-.23,.45),(0,-.36,.57),'root'),
         'head':((0,-.36,.57),(0,-.54,.60),'neck'),
         'jaw':((0,-.445,.535),(0,-.61,.505),'head')}
feet = {}
for side,x in [('L',.115),('R',-.115)]:
    for end,y in [('F',-.22),('H',.26)]:
        name = end+side
        hip = (x,y,.46)
        elbow = (x,y+.055 if end=='F' else y-.12,.26 if end=='F' else .29)
        ankle = (x,-.275 if end=='F' else .32,.065 if end=='F' else .12)
        toe = (x,-.355 if end=='F' else .205,.035)
        segment(name+' upper',hip,elbow,.045 if end=='F' else .063,skin_parts)
        segment(name+' lower',elbow,ankle,.025 if end=='F' else .032,skin_parts)
        segment(name+' pastern',ankle,toe,.024,skin_parts)
        ellipsoid(name+' paw',(x,toe[1]-.015,.034),(.043,.063,.032),skin_parts)
        bones[name+'_upper'] = (hip,elbow,'root')
        bones[name+'_lower'] = (elbow,ankle,name+'_upper')
        bones[name+'_paw'] = (ankle,toe,name+'_lower')
        feet[name] = ankle
tail = [(0,.35,.47),(0,.49,.55),(0,.58,.67),(0,.54,.77),(0,.43,.785),(0,.37,.745)]
for i,(a,b) in enumerate(zip(tail,tail[1:])):
    segment('Curved tail',a,b,.031-i*.004,skin_parts)
    bones['tail'+str(i)] = (a,b,'root' if i==0 else 'tail'+str(i-1))

bpy.ops.object.select_all(action='DESELECT')
for o in skin_parts:
    o.select_set(True)
bpy.context.view_layer.objects.active = skin_parts[0]
bpy.ops.object.join()
skin = bpy.context.object
skin.name = 'Indie | continuous short-coat skin'
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
remesh = skin.modifiers.new('Joined anatomical surface','REMESH')
remesh.mode = 'VOXEL'
remesh.voxel_size = .012
bpy.ops.object.modifier_apply(modifier=remesh.name)
smooth = skin.modifiers.new('Soft anatomy','SMOOTH')
smooth.factor,smooth.iterations = .7,3
bpy.ops.object.modifier_apply(modifier=smooth.name)
decimate = skin.modifiers.new('Game surface','DECIMATE')
decimate.ratio = .55
bpy.ops.object.modifier_apply(modifier=decimate.name)

rig_data = bpy.data.armatures.new('Street dog skeleton')
rig = bpy.data.objects.new('Indie | rig',rig_data)
scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for name,(head,tip,parent) in bones.items():
    bone = rig_data.edit_bones.new(name)
    bone.head,bone.tail = head,tip
    if parent:
        bone.parent = rig_data.edit_bones[parent]
for name,ankle in feet.items():
    control = rig_data.edit_bones.new('CTRL_'+name)
    control.head,control.tail = ankle,bones[name+'_paw'][1]
    control.use_deform = False
    pole = rig_data.edit_bones.new('POLE_'+name)
    pole.head = (ankle[0],.1 if name.startswith('F') else -.35,.28)
    pole.tail = pole.head+Vector((0,0,.08))
    pole.use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')
for name in feet:
    ik = rig.pose.bones[name+'_lower'].constraints.new('IK')
    ik.target,ik.subtarget,ik.chain_count = rig,'CTRL_'+name,2
    ik.pole_target,ik.pole_subtarget = rig,'POLE_'+name
    ik.pole_angle = math.pi/2
    ik.use_stretch = False
    rotation = rig.pose.bones[name+'_paw'].constraints.new('COPY_ROTATION')
    rotation.target,rotation.subtarget = rig,'CTRL_'+name
    rotation.owner_space = rotation.target_space = 'WORLD'
    best = (float('inf'),0)
    for step in range(48):
        ik.pole_angle = -math.pi+step*math.tau/48
        bpy.context.view_layer.update()
        error = (rig.pose.bones[name+'_lower'].head-Vector(bones[name+'_lower'][0])).length_squared
        if error < best[0]:
            best = error,ik.pole_angle
    ik.pole_angle = best[1]


def distance(point,a,b):
    a,b = Vector(a),Vector(b)
    t = max(0,min(1,(point-a).dot(b-a)/(b-a).length_squared))
    return (point-a-(b-a)*t).length


groups = {name:skin.vertex_groups.new(name=name) for name in bones}
for v in skin.data.vertices:
    if v.co.y > .40 and v.co.z > .49:
        names = [n for n in bones if n.startswith('tail')]
    elif v.co.y < -.38 and v.co.z > .42:
        names = ['head','neck']
    else:
        names = [n for n in bones if n!='jaw']
    weights = []
    for n in names:
        radius = .17 if n=='root' else .08 if n in ('head','neck') else .045 if n.endswith('upper') else .025
        d = distance(v.co,*bones[n][:2])/radius
        weights.append((n,1/max(.06,d)**5))
    weights = sorted(weights,key=lambda p:p[1],reverse=True)[:4]
    total = sum(w for _,w in weights)
    for n,w in weights:
        groups[n].add([v.index],w/total,'REPLACE')


def material(name,color,roughness=.8,vertex=False):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color,1)
    shader.inputs['Roughness'].default_value = roughness
    if vertex:
        attr = mat.node_tree.nodes.new('ShaderNodeVertexColor')
        attr.layer_name = 'Coat'
        mat.node_tree.links.new(attr.outputs['Color'],shader.inputs['Base Color'])
    return mat


coat = material('Short fawn coat with white bib',(1,1,1),vertex=True)
skin.data.materials.append(coat)
colors = skin.data.color_attributes.new(name='Coat',type='FLOAT_COLOR',domain='POINT')
for v,c in zip(skin.data.vertices,colors.data):
    x,y,z = v.co
    white = (z < .08 or (y < -.13 and z < .44 and abs(x)<.10) or (y < -.49 and z < .565))
    base = (.70,.66,.56) if white else (.48,.25,.085)
    grain = .96+.04*math.sin(x*97+y*81+z*121)
    c.color = (*[channel*grain for channel in base],1)
for face in skin.data.polygons:
    face.use_smooth = True
armature = skin.modifiers.new('Skin','ARMATURE')
armature.object = rig


def attached(o,bone,mat):
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    o.data.materials.append(mat)
    o.vertex_groups.new(name=bone).add(list(range(len(o.data.vertices))),1,'REPLACE')
    o.modifiers.new('Follow bone','ARMATURE').object = rig
    for face in o.data.polygons:
        face.use_smooth = True


black = material('Wet black nose and lips',(.009,.007,.006),.28)
eye_mat = material('Warm brown eyes',(.025,.014,.006),.15)
inner = material('Warm inner ear',(.20,.085,.045))
tan = material('Fawn ears and jaw',(.48,.25,.085))
pink = material('Tongue',(.42,.12,.13),.5)
attached(ellipsoid('Black nose',(0,-.670,.563),(.045,.024,.027)),'head',black)
for side in (-1,1):
    attached(ellipsoid('Brown almond eye',(side*.086,-.49,.629),(.018,.023,.017)),'head',eye_mat)
    vertices = [(side*.032,-.43,.665),(side*.12,-.395,.66),(side*.115,-.44,.82),
                (side*.074,-.477,.676),(side*.073,-.414,.681)]
    mesh = bpy.data.meshes.new('Upright ear')
    mesh.from_pydata(vertices,[],[(0,1,2),(0,2,3),(1,4,2),(0,4,1),(0,3,4),(2,4,3)])
    ear = bpy.data.objects.new('Upright triangular ear',mesh)
    scene.collection.objects.link(ear)
    attached(ear,'head',tan)
    mesh = bpy.data.meshes.new('Ear inset')
    mesh.from_pydata([(side*.052,-.449,.681),(side*.094,-.451,.689),(side*.108,-.449,.778)],[],[(0,1,2)])
    ear = bpy.data.objects.new('Dark inner ear',mesh)
    scene.collection.objects.link(ear)
    attached(ear,'head',inner)
attached(ellipsoid('Lower jaw',(0,-.55,.504),(.059,.10,.025)),'jaw',tan)
attached(ellipsoid('Lower lip',(0,-.56,.524),(.06,.103,.009)),'jaw',black)
attached(ellipsoid('Tongue',(0,-.585,.532),(.031,.049,.006)),'jaw',pink)

base = {p.name:p.matrix_basis.copy() for p in rig.pose.bones}
world_rest = {p.name:p.matrix.copy() for p in rig.pose.bones}
controls = {n:rig.pose.bones['CTRL_'+n].matrix.copy() for n in feet}
for mode,frames,fps in [('idle',97,32),('walk',49,48),('bark',25,32)]:
    rig.animation_data_clear()
    rig.animation_data_create()
    rig.animation_data.action = bpy.data.actions.new('Indie '+mode)
    scene.frame_start,scene.frame_end,scene.render.fps = 1,frames,fps
    for frame in range(1,frames+1):
        scene.frame_set(frame)
        phase = (frame-1)/(frames-1)
        for p in rig.pose.bones:
            p.matrix_basis = base[p.name].copy()
            p.rotation_mode = 'XYZ'
        root = rig.pose.bones['root']
        root.location.z = -.025+.004*math.cos(phase*math.tau*2) if mode=='walk' else .002*math.sin(phase*math.tau)
        if mode == 'walk':
            for name,offset in [('HL',0),('FL',.25),('HR',.5),('FR',.75)]:
                t = (phase+offset)%1
                if t < .62:
                    forward,lift = -.1488+.48*t,0
                else:
                    u = (t-.62)/.38
                    forward = .1488-.2976*u*u*(3-2*u)
                    lift = .045*math.sin(math.pi*u)**1.5
                p = rig.pose.bones['CTRL_'+name]
                p.matrix = Matrix.Translation(Vector((0,forward,lift))) @ controls[name]
                p.keyframe_insert('location',frame=frame)
        elif mode == 'idle':
            rig.pose.bones['neck'].rotation_euler.x = -.20*math.sin(phase*math.pi)**4
            rig.pose.bones['head'].rotation_euler.x = -.28*math.sin(phase*math.pi)**4
        else:
            t = phase*.75
            pulse = sum(max(0,math.sin(math.pi*(t-a)/.16))**2 if a<t<a+.16 else 0 for a in (.06,.30))
            rig.pose.bones['neck'].rotation_euler.x = .09*pulse
            bpy.context.view_layer.update()
            head_delta = rig.pose.bones['head'].matrix @ world_rest['head'].inverted()
            hinge = world_rest['jaw'].translation
            rig.pose.bones['jaw'].matrix = (head_delta @ Matrix.Translation(hinge) @
                                           Matrix.Rotation(.55*pulse,4,'X') @
                                           Matrix.Translation(-hinge) @ world_rest['jaw'])
        rig.pose.bones['tail0'].rotation_euler.z = .12*math.sin(phase*math.tau)
        for p in rig.pose.bones:
            if not p.name.startswith(('CTRL_','POLE_')):
                for prop in ('location','rotation_euler'):
                    p.keyframe_insert(prop,frame=frame)
        bpy.context.view_layer.update()
    scene.frame_set(1)
    for curve in rig.animation_data.action.fcurves:
        for point in curve.keyframe_points:
            point.interpolation = 'LINEAR'
    bpy.ops.export_scene.gltf(filepath=str(OUT/('dog.glb' if mode=='idle' else 'dog_'+mode+'.glb')),
                              export_format='GLB',export_animations=True,export_animation_mode='SCENE',
                              export_anim_scene_split_object=False,export_force_sampling=True,
                              export_bake_animation=True,export_morph=False)
print('INDIE_DOG_EXPORTED',len(skin.data.vertices),'skin vertices',flush=True)
