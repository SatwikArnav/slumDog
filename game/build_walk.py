"""Create a looping, in-place IK walk without modifying the source blend file."""
import math
import bpy
from mathutils import Matrix, Vector


def make_walk(rig):
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    base = {p.name: p.matrix.copy() for p in rig.pose.bones}
    basis = {p.name: p.matrix_basis.copy() for p in rig.pose.bones}
    rig.animation_data_clear()
    rig.animation_data_create()
    rig.animation_data.action = bpy.data.actions.new('Walk | planted steps and counter-swing')
    scene.frame_start, scene.frame_end, scene.render.fps = 1, 33, 32
    for frame in range(1, 34):
        scene.frame_set(frame)
        phase = (frame-1)/32
        angle = phase*math.tau
        for p in rig.pose.bones:
            p.matrix_basis = basis[p.name].copy()
        # Pelvis shifts toward the support foot, with a small twice-per-stride rise.
        pelvis = rig.pose.bones['root']
        pelvis.matrix = Matrix.Translation(Vector((.018*math.sin(angle), 0,
                                                   -.075+.010*math.cos(2*angle)))) @ base[pelvis.name]
        pelvis.keyframe_insert('location', frame=frame)
        for side, offset in [('L', 0), ('R', .5)]:
            t = (phase+offset) % 1
            if t < .6:
                y, lift = -.36+1.2*t, 0
                tilt = .10*max(0, (t-.45)/.15)
            else:
                u = (t-.6)/.4
                smooth = u*u*(3-2*u)
                y, lift = .36-.72*smooth, .12*math.sin(math.pi*u)**1.3
                tilt = -.15*math.sin(math.pi*u)
            foot = rig.pose.bones['CTRL_foot.'+side]
            foot.matrix = (Matrix.Translation(Vector((0, y, lift))) @
                           base[foot.name] @ Matrix.Rotation(tilt, 4, 'X'))
            for prop in ('location', 'rotation_quaternion', 'rotation_euler'):
                foot.keyframe_insert(prop, frame=frame)
            # Hands oppose the leg swing; use existing two-bone IK chains.
            hand = rig.pose.bones['CTRL_hand.'+side]
            hand.matrix = Matrix.Translation(Vector((0, -.17*math.cos(math.tau*t),
                                                     .025+.025*math.sin(math.tau*t)))) @ base[hand.name]
            for prop in ('location', 'rotation_quaternion', 'rotation_euler'):
                hand.keyframe_insert(prop, frame=frame)
            elbow = rig.pose.bones['CTRL_elbow.'+side]
            elbow.matrix = Matrix.Translation(Vector((-.12 if side == 'L' else .12,
                                                      -.08*math.cos(math.tau*t), -.04))) @ base[elbow.name]
            elbow.keyframe_insert('location', frame=frame)
        chest = rig.pose.bones['spine02']
        chest.rotation_mode = 'XYZ'
        chest.rotation_euler.y += .025*math.sin(angle)
        chest.rotation_euler.z += .025*math.sin(angle)
        chest.keyframe_insert('rotation_euler', frame=frame)
        bpy.context.view_layer.update()
    for curve in rig.animation_data.action.fcurves:
        for point in curve.keyframe_points:
            point.interpolation = 'LINEAR'
    scene.frame_set(1)


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
