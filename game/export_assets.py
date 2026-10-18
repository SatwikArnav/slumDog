"""Run with: blender -b --python game/export_assets.py (does not save .blend files)."""
import json
import math
import sys
from pathlib import Path
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_walk import make_walk, sockets

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'game' / 'assets'
OUT.mkdir(exist_ok=True)


def simplify_materials():
    # Preserve diffuse textures and colours; volume/noise networks are Blender-only.
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        old = mat.node_tree.nodes.get('Principled BSDF')
        color = tuple(old.inputs['Base Color'].default_value) if old else tuple(mat.diffuse_color)
        images = [n.image for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image
                  and (n.image.packed_file or Path(bpy.path.abspath(n.image.filepath)).is_file())
                  and not any(s in n.image.name.lower() for s in ('normal', '_nor', 'rough', 'metal', 'moisture'))]
        mat.node_tree.nodes.clear()
        bsdf = mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.inputs['Base Color'].default_value = color
        bsdf.inputs['Roughness'].default_value = .8
        output = mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
        mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
        if images:
            tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
            tex.image = images[0]
            mat.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
            if any(s in mat.name.lower() for s in ('hair', 'eye', 'brow')):
                mat.node_tree.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])


def export(name, animated=False):
    simplify_materials()
    bpy.ops.export_scene.gltf(
        filepath=str(OUT / name), export_format='GLB', export_yup=True,
        export_animations=animated, export_animation_mode='SCENE',
        export_anim_scene_split_object=False,
        export_force_sampling=True, export_bake_animation=True,
        export_morph=False, export_cameras=False, export_lights=False,
        export_apply=not animated, export_frame_range=True,
    )


bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'environment' / 'Shanti_Nagar_Level.blend'))
scene = bpy.context.scene
scene.frame_set(1)
collision = []
for obj in list(scene.objects):
    if obj.name.startswith('COL_'):
        points = [obj.matrix_world @ __import__('mathutils').Vector(c) for c in obj.bound_box]
        collision.append([min(p.x for p in points), min(-p.y for p in points),
                          max(p.x for p in points), max(-p.y for p in points)])
    character = any(c.name == 'Character' for c in obj.users_collection)
    if character or obj.hide_render or obj.type not in {'MESH', 'CURVE'}:
        bpy.data.objects.remove(obj, do_unlink=True)
        continue
    obj.animation_data_clear()
    if obj.type == 'CURVE':
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.ops.object.convert(target='MESH')
export('environment.glb')
metadata = {'collision': collision, 'spawn': [-.7, 0, 3.2],
            'smoking_seconds': 215 / 24, 'stride_length': 1.2}

bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'character' / 'Rook_Rebuilt.blend'))
scene = bpy.context.scene
scene.frame_set(1)
for obj in list(scene.objects):
    if (obj.type not in {'MESH', 'ARMATURE'} or obj.hide_render or
        obj.name.startswith(('Plane', 'WGT_', 'Smoke', 'Beard'))):
        bpy.data.objects.remove(obj, do_unlink=True)
        continue
    for mod in list(obj.modifiers):
        if mod.type == 'SUBSURF':
            obj.modifiers.remove(mod)
rig = next(o for o in scene.objects if o.type == 'ARMATURE')
metadata['smoke_sockets'] = sockets(rig)
export('character.glb', animated=True)
make_walk(rig)
metadata['walk_sockets'] = sockets(rig)
export('walk.glb', animated=True)
(OUT / 'scene.json').write_text(json.dumps(metadata, separators=(',', ':')))
print('GAME_ASSETS_EXPORTED', OUT, flush=True)
