"""Original Indian street-dog asset. blender -b --python game/build_dog.py"""
from pathlib import Path
import bpy
import math
import json
import sys
from mathutils import Vector, Matrix, noise
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
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=position)
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


def loft(name, rings, parts=None, subdivision=2):
    """Smooth anatomical sections along Y: (y, centre_z, half_width, half_height)."""
    vertices,faces = [],[]
    count = 20
    for y,z,w,h in rings:
        for i in range(count):
            angle = math.tau*i/count
            vertices.append((w*math.sin(angle),y,z+h*math.cos(angle)))
    for j in range(len(rings)-1):
        for i in range(count):
            a,b = j*count+i,j*count+(i+1)%count
            faces.append((a,b,b+count,a+count))
    faces.extend([tuple(reversed(range(count))),tuple(range((len(rings)-1)*count,len(rings)*count))])
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices,[],faces)
    o = bpy.data.objects.new(name,mesh)
    scene.collection.objects.link(o)
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    # Recalculate normals before remeshing: section winding depends on direction.
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    sub = o.modifiers.new('Anatomical curves','SUBSURF')
    sub.levels = subdivision
    bpy.ops.object.modifier_apply(modifier=sub.name)
    if parts is not None:
        parts.append(o)
    o.select_set(False)
    return o


def tube(name, points, radii, parts):
    vertices,faces = [],[]
    for j,p in enumerate(points):
        p = Vector(p)
        tangent = Vector(points[min(j+1,len(points)-1)])-Vector(points[max(0,j-1)])
        across = tangent.cross(Vector((1,0,0))).normalized()
        for i in range(16):
            angle = i*math.tau/16
            vertices.append(p+radii[j]*(Vector((1,0,0))*math.cos(angle)+across*math.sin(angle)))
    for j in range(len(points)-1):
        for i in range(16):
            a,b = j*16+i,j*16+(i+1)%16
            faces.append((a,b,b+16,a+16))
    faces.extend([tuple(reversed(range(16))),tuple(range((len(points)-1)*16,len(points)*16))])
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices,[],faces)
    o = bpy.data.objects.new(name,mesh)
    scene.collection.objects.link(o)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    sub = o.modifiers.new('Tapered contours','SUBSURF')
    sub.levels = 2
    bpy.ops.object.modifier_apply(modifier=sub.name)
    parts.append(o)
    return o


loft('Ribcage, loin and croup',[
    (.36,.455,.018,.025),(.31,.46,.079,.080),(.23,.458,.095,.092),
    (.12,.454,.088,.093),(.015,.425,.107,.125),(-.10,.415,.116,.145),
    (-.20,.416,.106,.143),(-.28,.428,.071,.102),(-.31,.46,.025,.035)],skin_parts)
loft('Sloping muscular neck',[
    (-.22,.467,.070,.082),(-.27,.50,.090,.11),(-.32,.545,.079,.108),
    (-.38,.585,.065,.084),(-.43,.606,.058,.063)],skin_parts)
# Forehead, stop, nasal bridge and tapered upper muzzle are one continuous wedge.
loft('Canine skull and nasal bridge',[
    (-.355,.618,.025,.025),(-.39,.635,.069,.063),(-.435,.636,.079,.068),
    (-.48,.627,.073,.057),(-.515,.606,.057,.041),(-.55,.596,.050,.033),
    (-.61,.584,.039,.025),(-.659,.580,.030,.021),(-.672,.581,.018,.012)],skin_parts)
for side in (-1,1):
    ellipsoid('Masseter cheek',(side*.048,-.451,.587),(.029,.052,.038),skin_parts)
    brow = ellipsoid('Brow ridge',(side*.059,-.486,.650),(.022,.034,.014),skin_parts)
    brow.rotation_euler.y = side*.25

bones = {'root':((0,.28,.445),(0,-.23,.445),None),
         'neck':((0,-.23,.465),(0,-.365,.595),'root'),
         'head':((0,-.365,.595),(0,-.54,.612),'neck'),
         'jaw':((0,-.448,.572),(0,-.625,.553),'head')}
for label,side in [('L',1),('R',-1)]:
    bones['ear'+label] = ((side*.054,-.414,.670),(side*.085,-.403,.79),'head')
feet = {}
for side,x in [('L',.091),('R',-.091)]:
    for end,y in [('F',-.22),('H',.26)]:
        name = end+side
        hip = (x,y,.465)
        elbow = (x,-.18 if end=='F' else .135,.295 if end=='F' else .315)
        ankle = (x,-.245 if end=='F' else .305,.070 if end=='F' else .145)
        toe = (x,-.285 if end=='F' else .265,.028)
        # Shoulders merge into the chest; thighs taper into defined stifles/hocks.
        tube(name+' muscle and tendon',[hip,tuple(Vector(hip)*.55+Vector(elbow)*.45),elbow,
                                       tuple(Vector(elbow)*.45+Vector(ankle)*.55),ankle,toe],
             [.048 if end=='F' else .061,.041 if end=='F' else .052,
              .027 if end=='F' else .032,.019,.017,.022],skin_parts)
        ellipsoid(name+' paw',(x,toe[1]-.018,.027),(.031,.046,.024),skin_parts)
        bones[name+'_upper'] = (hip,elbow,'root')
        bones[name+'_lower'] = (elbow,ankle,name+'_upper')
        bones[name+'_paw'] = (ankle,toe,name+'_lower')
        feet[name] = ankle
tail = [(0,.32,.49),(0,.42,.535),(0,.515,.62),(0,.54,.715),(0,.50,.77),(0,.445,.765)]
tube('Continuous tapered sickle tail',tail,[.028,.023,.018,.013,.008,.002],skin_parts)
for i,(a,b) in enumerate(zip(tail,tail[1:])):
    bones['tail'+str(i)] = (a,b,'root' if i==0 else 'tail'+str(i-1))


def anatomy(point):
    x,y,z = point
    # The adult Indie muzzle is roughly half the head length; shortening the
    # nasal section and pinnae avoids the previous jackal-like proportions.
    if y < -.51:
        y = -.51+(y+.51)*.76
    if y < -.33 and z > .68:
        z = .68+(z-.68)*.74
    return Vector((x,y,z))


for o in skin_parts:
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    for v in o.data.vertices:
        v.co = anatomy(v.co)
bones = {n:(anatomy(a),anatomy(b),parent) for n,(a,b,parent) in bones.items()}
feet = {n:anatomy(p) for n,p in feet.items()}
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
remesh.voxel_size = .0045
bpy.ops.object.modifier_apply(modifier=remesh.name)
smooth = skin.modifiers.new('Soft anatomy','SMOOTH')
smooth.factor,smooth.iterations = .7,3
bpy.ops.object.modifier_apply(modifier=smooth.name)
decimate = skin.modifiers.new('Game surface','DECIMATE')
decimate.ratio = .42
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
    pole.head = anatomy((ankle[0],.1 if name.startswith('F') else -.35,.28))
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
    if v.co.y > .38 and v.co.z > .51:
        names = [n for n in bones if n.startswith('tail')]
    elif v.co.y < -.37 and v.co.z > .52:
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
    # Warm dusty fawn with a subtle sable saddle and naturally broken cream markings.
    grain = noise.noise_vector(v.co*24)[0]
    edge = .009*grain
    bib = y < -.19 and z < .465+edge and abs(x)<.091+edge
    sock_height = .075 if x>0 else .095
    white = z < sock_height+edge or bib or (y < -.51 and z < .584+edge)
    blaze = abs(x)<.010+edge*.3 and -.57<y<-.465 and z>.622
    flank = x<-.06 and ((y-.21)/.085)**2+((z-.395)/.07)**2 < .7+grain*.2
    white = white or blaze or flank
    dorsal = max(0,min(1,(z-.425)/.12))*max(0,min(1,(y+.32)*8))
    base = (.60,.53,.41) if white else tuple(a*(1-.60*dorsal) for a in (.42,.235,.11))
    # Face mask follows the muzzle/eye socket, rather than a cartoon black nose dot.
    mask = max(0,min(1,(-y-.52)/.14))*.52 if z>.566 else 0
    variation = .88+.12*noise.noise_vector(v.co*19)[1]
    c.color = (*[channel*variation*(1-mask) for channel in base],1)
for face in skin.data.polygons:
    face.use_smooth = True
armature = skin.modifiers.new('Skin','ARMATURE')
armature.object = rig


def attached(o,bone,mat):
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    for v in o.data.vertices:
        v.co = anatomy(v.co)
    o.data.materials.append(mat)
    o.vertex_groups.new(name=bone).add(list(range(len(o.data.vertices))),1,'REPLACE')
    o.modifiers.new('Follow bone','ARMATURE').object = rig
    for face in o.data.polygons:
        face.use_smooth = True


black = material('Wet black nose and lips',(.012,.009,.007),.23)
eye_mat = material('Amber brown iris',(.095,.044,.012),.17)
pupil_mat = material('Deep brown pupil',(.004,.003,.002),.12)
inner = material('Ear concha',(.12,.054,.030))
tan = material('Fawn ears',(.36,.185,.078))
cream = material('Cream chin',(.53,.45,.33))
pink = material('Tongue',(.34,.075,.085),.5)
ivory = material('Small ivory teeth',(.62,.56,.43),.4)
# A broad triangular nose, paired nostrils, philtrum and restrained lip line.
nose = ellipsoid('Nose leather',(0,-.671,.582),(.032,.019,.021))
for v in nose.data.vertices:
    v.co.x *= .85+.15*(v.co.z/.021)
attached(nose,'head',black)
for side in (-1,1):
    attached(ellipsoid('Nostril',(side*.019,-.686,.586),(.009,.004,.006)),'head',pupil_mat)
    # Eyes sit in slanted sockets, with a narrow eyelid rather than exposed spheres.
    socket = ellipsoid('Dark eyelid',(side*.067,-.490,.636),(.012,.022,.011))
    socket.rotation_euler.z = side*.45
    attached(socket,'head',black)
    attached(ellipsoid('Amber iris',(side*.074,-.498,.637),(.007,.011,.007)),'head',eye_mat)
    attached(ellipsoid('Pupil',(side*.077,-.503,.638),(.004,.006,.005)),'head',pupil_mat)
    # Cupped pinnae: curved rim, recessed concha, thin back, and a rounded tip.
    rows = [(0,.045,.023),(.025,.048,.031),(.070,.037,.024),(.112,.021,.012),(.139,.002,.001)]
    vertices,faces = [],[]
    for height,width,depth in rows:
        for i in range(9):
            u = -1+2*i/8
            vertices.append((side*(.054+.25*height+u*width),
                             -.414+.11*height-depth*(1-u*u),.670+height-.008*u))
    for j in range(len(rows)-1):
        for i in range(8):
            a = j*9+i
            faces.append((a,a+1,a+10,a+9))
    mesh = bpy.data.meshes.new('Cupped ear')
    mesh.from_pydata(vertices,[],faces)
    ear = bpy.data.objects.new('Thin curved pinna',mesh)
    scene.collection.objects.link(ear)
    bpy.context.view_layer.objects.active = ear
    sub = ear.modifiers.new('Soft pinna','SUBSURF')
    sub.levels = 2
    bpy.ops.object.modifier_apply(modifier=sub.name)
    solid = ear.modifiers.new('Ear thickness','SOLIDIFY')
    solid.thickness = .004
    bpy.ops.object.modifier_apply(modifier=solid.name)
    attached(ear,'earL' if side==1 else 'earR',tan)
    ear.data.materials.append(inner)
    for face in ear.data.polygons:
        centre = face.center
        if .69<centre.z<.77 and abs(abs(centre.x)-.075)<.018:
            face.material_index = 1
jaw = loft('Tapered lower jaw',[
    (-.44,.555,.043,.019),(-.48,.548,.046,.017),(-.54,.548,.039,.013),
    (-.61,.553,.028,.009),(-.651,.560,.020,.006)])
attached(jaw,'jaw',cream)
attached(ellipsoid('Lower lip',(0,-.565,.563),(.037,.084,.003)),'jaw',black)
attached(ellipsoid('Mouth cavity',(0,-.541,.567),(.035,.072,.004)),'head',black)
attached(ellipsoid('Tongue',(0,-.575,.566),(.021,.042,.004)),'jaw',pink)
for side in (-1,1):
    for y,z,radius,length in [(-.608,.567,.004,.012),(-.502,.565,.004,.008)]:
        bpy.ops.mesh.primitive_cone_add(vertices=12,radius1=.001,radius2=radius,depth=length,
                                        location=(side*.028,y,z-length/2))
        attached(bpy.context.object,'head',ivory)
    # Separate small toe lobes/claws make the feet read as paws, not white shoes.
    for end in ('F','H'):
        bone = end+('L' if side==1 else 'R')+'_paw'
        x,y,z = bones[bone][1]
        for offset in (-.017,0,.017):
            attached(ellipsoid('Toe',(x+offset,y-.040,.023),(.011,.018,.015)),bone,cream)
            attached(ellipsoid('Small claw',(x+offset,y-.054,.019),(.0035,.008,.004)),bone,black)

# Bake fine, directional short-coat colour into a portable texture; raylib
# cannot interpret Blender procedural shader nodes.
bpy.ops.object.select_all(action='DESELECT')
skin.select_set(True)
bpy.context.view_layer.objects.active = skin
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(island_margin=.015)
bpy.ops.object.mode_set(mode='OBJECT')
nodes,links = coat.node_tree.nodes,coat.node_tree.links
shader = nodes.get('Principled BSDF')
attr = next(n for n in nodes if n.type=='VERTEX_COLOR')
coord = nodes.new('ShaderNodeTexCoord')
scale = nodes.new('ShaderNodeVectorMath')
scale.operation = 'MULTIPLY'
scale.inputs[1].default_value = (480,65,480)
links.new(coord.outputs['Generated'],scale.inputs[0])
fibres = nodes.new('ShaderNodeTexNoise')
fibres.inputs['Scale'].default_value = 1
fibres.inputs['Detail'].default_value = 2
links.new(scale.outputs[0],fibres.inputs['Vector'])
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].color = (.48,.48,.48,1)
ramp.color_ramp.elements[1].color = (1.12,1.12,1.12,1)
links.new(fibres.outputs['Fac'],ramp.inputs[0])
mix = nodes.new('ShaderNodeMixRGB')
mix.blend_type = 'MULTIPLY'
mix.inputs[0].default_value = 1
links.new(attr.outputs['Color'],mix.inputs[1])
links.new(ramp.outputs[0],mix.inputs[2])
emission = nodes.new('ShaderNodeEmission')
ao = nodes.new('ShaderNodeAmbientOcclusion')
ao.inputs['Distance'].default_value = .12
ao.samples = 16
shade = nodes.new('ShaderNodeMixRGB')
shade.blend_type = 'MULTIPLY'
shade.inputs[0].default_value = .72
links.new(mix.outputs[0],shade.inputs[1])
links.new(ao.outputs['Color'],shade.inputs[2])
links.new(shade.outputs[0],emission.inputs[0])
output = nodes.get('Material Output')
links.new(emission.outputs[0],output.inputs['Surface'])
texture = bpy.data.images.new('Indie short sable coat',width=2048,height=2048)
target = nodes.new('ShaderNodeTexImage')
target.image = texture
nodes.active = target
scene.render.engine = 'CYCLES'
scene.cycles.samples = 1
scene.render.bake.margin = 12
bpy.ops.object.bake(type='EMIT')
texture.pack()
links.new(shader.outputs[0],output.inputs['Surface'])
links.new(target.outputs['Color'],shader.inputs['Base Color'])
# Tangent-space hair relief survives export as a normal map. Colour-only grain
# disappears in motion and leaves the silhouette looking like polished clay.
bump = nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = .32
bump.inputs['Distance'].default_value = .002
links.new(fibres.outputs['Fac'],bump.inputs['Height'])
links.new(bump.outputs['Normal'],shader.inputs['Normal'])
normal_image = bpy.data.images.new('Short coat micro normals',width=2048,height=2048)
normal_image.colorspace_settings.name = 'Non-Color'
normal_target = nodes.new('ShaderNodeTexImage')
normal_target.image = normal_image
nodes.active = normal_target
bpy.ops.object.bake(type='NORMAL')
normal_image.pack()
normal_map = nodes.new('ShaderNodeNormalMap')
links.new(normal_target.outputs['Color'],normal_map.inputs['Color'])
links.new(normal_map.outputs['Normal'],shader.inputs['Normal'])
# Baked colours already include the vertex markings.
skin.data.color_attributes.remove(colors)

base = {p.name:p.matrix_basis.copy() for p in rig.pose.bones}
world_rest = {p.name:p.matrix.copy() for p in rig.pose.bones}
controls = {n:rig.pose.bones['CTRL_'+n].matrix.copy() for n in feet}
validation = {}
for mode,frames,fps in [('idle',97,32),('walk',49,48),('bark',25,32)]:
    ankle_error = 0.
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
        root.location.z = -.014+.003*math.cos(phase*math.tau*2) if mode=='walk' else .002*math.sin(phase*math.tau)
        if mode == 'walk':
            for name,offset in [('HL',0),('FL',.25),('HR',.5),('FR',.75)]:
                t = (phase+offset)%1
                if t < .62:
                    forward,lift = -.1178+.38*t,0
                else:
                    u = (t-.62)/.38
                    forward = .1178 + .1444*u - 1.14*u*u + .76*u*u*u
                    lift = .035*math.sin(math.pi*u)**1.5
                p = rig.pose.bones['CTRL_'+name]
                p.matrix = Matrix.Translation(Vector((0,forward,lift))) @ controls[name]
                p.keyframe_insert('location',frame=frame)
            rig.pose.bones['neck'].rotation_euler.x = .028*math.sin(phase*math.tau*2)
            rig.pose.bones['head'].rotation_euler.x = -.018*math.sin(phase*math.tau*2)
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
        for i,label in enumerate(('L','R')):
            rig.pose.bones['ear'+label].rotation_euler.x = .045*math.sin(phase*math.tau*(2 if mode=='walk' else 1)+i*.4)
        for p in rig.pose.bones:
            if not p.name.startswith(('CTRL_','POLE_')):
                for prop in ('location','rotation_euler'):
                    p.keyframe_insert(prop,frame=frame)
        bpy.context.view_layer.update()
        for name in feet:
            ankle_error = max(ankle_error,(rig.pose.bones[name+'_lower'].tail-
                                          rig.pose.bones['CTRL_'+name].head).length)
    validation[mode] = {'sampled_frames':frames,'maximum_ankle_target_error_m':ankle_error}
    assert ankle_error < .015, f'{mode}: paw misses ground trajectory by {ankle_error:.4f}m'
    scene.frame_set(1)
    for curve in rig.animation_data.action.fcurves:
        for point in curve.keyframe_points:
            point.interpolation = 'LINEAR'
    bpy.ops.export_scene.gltf(filepath=str(OUT/('dog.glb' if mode=='idle' else 'dog_'+mode+'.glb')),
                              export_format='GLB',export_animations=True,export_animation_mode='SCENE',
                              export_anim_scene_split_object=False,export_force_sampling=True,
                              export_bake_animation=True,export_morph=False)
print('INDIE_DOG_EXPORTED',len(skin.data.vertices),'skin vertices',flush=True)
(OUT/'dog_validation.json').write_text(json.dumps(validation,indent=2)+'\n')
