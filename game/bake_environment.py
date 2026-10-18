"""Bake Blender-only surface networks into UV atlases for the static level."""
from collections import defaultdict
import json
from pathlib import Path
import tempfile
import bpy


def procedural(material):
    if not material or not material.use_nodes:
        return False
    return any(n.type in {'TEX_NOISE','TEX_BRICK','MIX_RGB','NEW_GEOMETRY'} or
               (n.type == 'TEX_IMAGE' and n.projection == 'BOX')
               for n in material.node_tree.nodes)


def prepare_environment(out):
    scene = bpy.context.scene
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    print('COLLECTING_SURFACES',flush=True)
    groups = defaultdict(list)
    originals = [o for o in scene.objects if o.type == 'MESH']
    # Evaluate transforms/modifiers before merging; keep original UVs on signs,
    # chairs and other image-textured assets. Limit batches to 16-bit indices.
    for obj in originals:
        evaluated = obj.evaluated_get(deps)
        mesh = evaluated.to_mesh()
        uv = mesh.uv_layers.active
        by_material = defaultdict(list)
        for face in mesh.polygons:
            mat = mesh.materials[face.material_index] if mesh.materials else None
            if mat:
                mat = mat.original
                points = [tuple(evaluated.matrix_world @ mesh.vertices[i].co) for i in face.vertices]
                coords = [tuple(uv.data[i].uv) for i in face.loop_indices] if uv else [(0.,0.)]*len(points)
                normal_matrix = evaluated.matrix_world.to_3x3().inverted().transposed()
                normals = [tuple((normal_matrix @ mesh.corner_normals[i].vector).normalized()) for i in face.loop_indices]
                by_material[mat].append((points,coords,face.use_smooth,normals))
        for mat, faces in by_material.items():
            if not groups[mat] or groups[mat][-1]['count']+sum(len(f[0]) for f in faces) > 50000:
                groups[mat].append({'count':0,'faces':[]})
            batch = groups[mat][-1]
            batch['faces'].extend(faces)
            batch['count'] += sum(len(f[0]) for f in faces)
        evaluated.to_mesh_clear()
    for obj in originals:
        bpy.data.objects.remove(obj, do_unlink=True)
    print('MERGING_SURFACES',len(groups),flush=True)
    baked = []
    targets = []
    for source, batches in groups.items():
        for index, batch in enumerate(batches):
            vertices, polygons, coords, smooth, normals = [], [], [], [], []
            for points, face_uv, shading, face_normals in batch['faces']:
                start = len(vertices)
                vertices.extend(points)
                polygons.append(tuple(range(start,start+len(points))))
                coords.extend(face_uv)
                smooth.append(shading)
                normals.extend(face_normals)
            mesh = bpy.data.meshes.new(source.name+' surface')
            mesh.from_pydata(vertices,[],polygons)
            mesh.update()
            uv = mesh.uv_layers.new(name='Surface UV')
            for loop, coordinate in zip(uv.data,coords):
                loop.uv = coordinate
            for face, shading in zip(mesh.polygons,smooth):
                face.use_smooth = shading
            mesh.normals_split_custom_set(normals)
            material = source.copy() if procedural(source) else source
            mesh.materials.append(material)
            obj = bpy.data.objects.new(source.name+f' batch {index}',mesh)
            scene.collection.objects.link(obj)
            if procedural(source):
                targets.append((obj,material,source.name))
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 1
    scene.cycles.use_denoising = False
    for obj, mat, name in targets:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=1.1519, island_margin=.006)
        bpy.ops.object.mode_set(mode='OBJECT')
        size = 3072 if name.startswith(('Plaster','Lane concrete','Unfinished brick')) else 1024
        image = bpy.data.images.new('Baked '+mat.name,width=size,height=size,alpha=False)
        image.file_format = 'PNG'
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        bsdf = nodes.get('Principled BSDF')
        color = bsdf.inputs['Base Color']
        output = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL')
        # Original base-colour network + local occlusion, not a guessed texture.
        ao = nodes.new('ShaderNodeAmbientOcclusion')
        ao.inputs['Distance'].default_value = .8
        ao.samples = 8
        if color.is_linked:
            links.new(color.links[0].from_socket,ao.inputs['Color'])
        else:
            ao.inputs['Color'].default_value = color.default_value
        emission = nodes.new('ShaderNodeEmission')
        blend = nodes.new('ShaderNodeMixRGB')
        blend.inputs[0].default_value = .3
        if color.is_linked:
            links.new(color.links[0].from_socket,blend.inputs[1])
        else:
            blend.inputs[1].default_value = color.default_value
        links.new(ao.outputs['Color'],blend.inputs[2])
        links.new(blend.outputs[0],emission.inputs['Color'])
        links.new(emission.outputs[0],output.inputs['Surface'])
        target = nodes.new('ShaderNodeTexImage')
        target.image = image
        nodes.active = target
        print('BAKING_SURFACE',name,size,flush=True)
        bpy.ops.object.bake(type='EMIT',margin=8,use_clear=True)
        # Opaque atlases use JPEG; retain PNG alpha on source signs/decals.
        with tempfile.TemporaryDirectory(prefix='slumdog-surface-') as directory:
            image.filepath_raw = str(Path(directory,'surface.jpg'))
            image.file_format = 'JPEG'
            image.save()
            image.pack()
        # Export a conventional UV texture, preserving the baked result exactly.
        nodes.clear()
        shader = nodes.new('ShaderNodeBsdfPrincipled')
        shader.inputs['Roughness'].default_value = .85
        tex = nodes.new('ShaderNodeTexImage')
        tex.image = image
        output = nodes.new('ShaderNodeOutputMaterial')
        links.new(tex.outputs['Color'],shader.inputs['Base Color'])
        links.new(shader.outputs[0],output.inputs['Surface'])
        mat['baked_original_surface'] = True
        baked.append({'material':name,'image':image.name,'size':size})
    Path(out,'surface_bakes.json').write_text(json.dumps(baked,indent=2))
    print('BAKED_SURFACES_COMPLETE',len(baked),flush=True)
