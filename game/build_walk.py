"""Create a looping, in-place IK walk without modifying the source blend file."""
import math
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


def make_walk(rig):
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    base = {p.name: p.matrix.copy() for p in rig.pose.bones}
    basis = {p.name: p.matrix_basis.copy() for p in rig.pose.bones}
    body = next(o for o in scene.objects if o.name.startswith('Human'))
    outfit = next(o for o in scene.objects if o.name.startswith('Field jacket'))
    leg_groups = {g.index for g in outfit.vertex_groups
                  if g.name.startswith(('upperleg','lowerleg','pelvis'))}
    trouser_vertices = {v.index for v in outfit.data.vertices
                        if sum(g.weight for g in v.groups if g.group in leg_groups) > .1}
    hands = set()
    for side in ('L','R'):
        wrist = rig.data.bones['wrist.'+side].head_local
        direction = (rig.data.bones['finger3-1.'+side].head_local-wrist).normalized()
        groups = {g.index for g in body.vertex_groups if g.name.endswith('.'+side)
                  and g.name.startswith(('wrist','finger','metacarpal'))}
        hands.update(v.index for v in body.data.vertices
                     if (v.co-wrist).dot(direction) > .015
                     and sum(g.weight for g in v.groups if g.group in groups) > .5)
    rig.animation_data_clear()
    rig.animation_data_create()
    rig.animation_data.action = bpy.data.actions.new('Walk | heel contact, toe-off and relaxed arms')
    # Wrist IK and fixed elbow poles fight a relaxed arm swing. Bake FK arms for
    # this clip; the smoking clip has already been exported with its original IK.
    for side in ('L','R'):
        for name in ('lowerarm01.','wrist.'):
            for constraint in rig.pose.bones[name+side].constraints:
                constraint.influence = 0
    scene.frame_start, scene.frame_end, scene.render.fps = 1, 49, 48
    report = {'max_ankle_error':0., 'min_foot_separation':10.,
              'min_hand_leg_clearance':10.,'checked_hand_vertices':len(hands),'frames':[]}
    for frame in range(1, 50):
        scene.frame_set(frame)
        phase = (frame-1)/48
        angle = phase*math.tau
        for p in rig.pose.bones:
            p.matrix_basis = basis[p.name].copy()
        # Pelvis shifts toward the support foot, with a small twice-per-stride rise.
        pelvis = rig.pose.bones['root']
        pelvis.matrix = Matrix.Translation(Vector((.012*math.sin(angle), 0,
                                                   -.065+.010*math.cos(2*(angle-.6*math.pi))))) @ base[pelvis.name]
        pelvis.keyframe_insert('location', frame=frame)
        chest = rig.pose.bones['spine02']
        chest.rotation_mode = 'XYZ'
        chest.rotation_euler.y += .012*math.sin(angle)
        chest.rotation_euler.z += .018*math.sin(angle)
        chest.keyframe_insert('rotation_euler', frame=frame)
        for side, offset in [('L', 0), ('R', .5)]:
            t = (phase+offset) % 1
            half = 1.1*.62/2
            if t < .62:
                y, lift = -half+1.1*t, 0
                if t < .09:
                    tilt = -.10*(1-t/.09)
                    pivot = Vector((0,.045,-.06))
                else:
                    u = max(0,min(1,(t-.48)/.14))
                    tilt = .22*u*u*(3-2*u)
                    pivot = Vector((0,-.16,-.06))
            else:
                u = (t-.62)/.38
                # Match stance velocity at lift-off and heel contact. A zero-
                # velocity sine swing caused a visible hitch at every step.
                velocity = 1.1*.38
                delta = -2*half
                y = half+velocity*u+(3*delta-3*velocity)*u*u+(-2*delta+2*velocity)*u**3
                lift = .065*math.sin(math.pi*u)**1.5
                smooth = u*u*(3-2*u)
                tilt = .22*(1-smooth)-.10*smooth
                pivot = Vector((0,-.16*(1-smooth)+.045*smooth,-.06))
            foot = rig.pose.bones['CTRL_foot.'+side]
            contact = base[foot.name].translation+pivot
            lateral = -.10 if side == 'L' else .10
            foot.matrix = (Matrix.Translation(Vector((lateral,y,lift))) @
                           Matrix.Translation(contact) @ Matrix.Rotation(tilt,4,'X') @
                           Matrix.Translation(-contact) @ base[foot.name])
            for prop in ('location', 'rotation_quaternion', 'rotation_euler'):
                foot.keyframe_insert(prop, frame=frame)
            knee = rig.pose.bones['CTRL_knee.'+side]
            knee.matrix = Matrix.Translation(Vector((-.05 if side == 'L' else .05,-.08,0))) @ base[knee.name]
            knee.keyframe_insert('location',frame=frame)
        bpy.context.view_layer.update()
        torso = rig.pose.bones['spine01'].matrix @ base['spine01'].inverted()
        for side, offset in [('L',0),('R',.5)]:
            t = (phase+offset) % 1
            upper = rig.pose.bones['upperarm01.'+side]
            lower = rig.pose.bones['lowerarm01.'+side]
            wrist = rig.pose.bones['wrist.'+side]
            shoulder = base[upper.name].translation
            # Swing about the shoulder, not a translated wrist locked to an
            # outward pole. Retain lateral clearance for the whole palm/fingers;
            # pulling the shoulder too far inward sends the hands into the thighs.
            rotation = Matrix.Rotation(.20*math.cos(math.tau*t),4,'X') @ Matrix.Rotation(.05 if side=='L' else -.05,4,'Y')
            upper.matrix = torso @ Matrix.Translation(shoulder) @ rotation @ Matrix.Translation(-shoulder) @ base[upper.name]
            bpy.context.view_layer.update()
            upper_delta = upper.matrix @ base[upper.name].inverted()
            elbow = base[lower.name].translation
            forearm = (Matrix.Rotation(-.12 if side=='L' else .12,4,'Y') @
                       Matrix.Rotation(-.08-.025*(1-math.cos(math.tau*t)),4,'X'))
            lower.matrix = upper_delta @ Matrix.Translation(elbow) @ forearm @ Matrix.Translation(-elbow) @ base[lower.name]
            bpy.context.view_layer.update()
            wrist.matrix = lower.matrix @ base[lower.name].inverted() @ base[wrist.name]
            for bone in (upper,lower,wrist):
                bone.rotation_mode = 'QUATERNION'
                for prop in ('location','rotation_quaternion','scale'):
                    bone.keyframe_insert(prop,frame=frame)
        bpy.context.view_layer.update()
        for side in ('L','R'):
            error = (rig.pose.bones['foot.'+side].head-rig.pose.bones['CTRL_foot.'+side].head).length
            report['max_ankle_error'] = max(report['max_ankle_error'],error)
        separation = abs(rig.pose.bones['foot.L'].head.x-rig.pose.bones['foot.R'].head.x)
        report['min_foot_separation'] = min(report['min_foot_separation'],separation)
        deps = bpy.context.evaluated_depsgraph_get()
        clothing = outfit.evaluated_get(deps).data
        # Check actual deformed hands against clothed hips/thighs, not just the
        # wrist joint. Sleeve cuffs are deliberately excluded from this test.
        points = [v.co.copy() for v in clothing.vertices]
        faces = [tuple(p.vertices) for p in clothing.polygons
                 if all(i in trouser_vertices for i in p.vertices)]
        trousers = BVHTree.FromPolygons(points,faces,all_triangles=False)
        skin = body.evaluated_get(deps).data
        distances = []
        for i in hands:
            point = skin.vertices[i].co
            nearest,normal,_,distance = trousers.find_nearest(point)
            distances.append(distance if (point-nearest).dot(normal) >= 0 else -distance)
        clearance = min(distances)
        report['min_hand_leg_clearance'] = min(report['min_hand_leg_clearance'],clearance)
        report['frames'].append({name:list(rig.pose.bones[name].head) for name in
                                 ['foot.L','foot.R','lowerleg01.L','lowerleg01.R','wrist.L','wrist.R']})
    for curve in rig.animation_data.action.fcurves:
        for point in curve.keyframe_points:
            point.interpolation = 'LINEAR'
    scene.frame_set(1)
    return report


def sockets(rig):
    """Sample mouth and actual deformed cigarette in exported, Y-up coordinates."""
    scene = bpy.context.scene
    ember = next(o for o in scene.objects if o.name.startswith('Cigarette | ember'))
    head_rest = rig.data.bones['head'].matrix_local.inverted() @ Vector(rig['mouth_contact'])
    result = []
    for frame in range(scene.frame_start, scene.frame_end+1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        mouth = rig.matrix_world @ rig.pose.bones['head'].matrix @ head_rest
        evaluated = ember.evaluated_get(bpy.context.evaluated_depsgraph_get())
        point = evaluated.matrix_world @ (sum((v.co for v in evaluated.data.vertices), Vector()) /
                                           len(evaluated.data.vertices))
        result.append([[p.x, p.z, -p.y] for p in (mouth, point)])
    scene.frame_set(1)
    return result
