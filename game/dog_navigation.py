"""Collect evaluated Blender building/prop bounds for street navigation."""
from mathutils import Vector
import bpy


def collect_navigation():
    bpy.data.collections['Collision'].hide_viewport = False
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    buildings,props = [],[]
    for o in bpy.context.scene.objects:
        if o.type!='MESH' or any(c.name=='Character' for c in o.users_collection):
            continue
        points = [o.matrix_world @ Vector(v) for v in o.bound_box]
        lo = [min(v[i] for v in points) for i in range(3)]
        hi = [max(v[i] for v in points) for i in range(3)]
        bounds = [lo[0],-hi[1],hi[0],-lo[1]]
        if o.name.startswith('COL_'):
            buildings.append(bounds)
        elif not o.hide_render and lo[2]<.23 and hi[2]>.27 and hi[0]-lo[0]<3 and hi[1]-lo[1]<3:
            props.append(bounds)
    return buildings,buildings+props
