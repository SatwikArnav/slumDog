import bpy,os
ROOT=os.path.dirname(os.path.abspath(__file__))
s=bpy.context.scene
s.render.resolution_x=960;s.render.resolution_y=600;s.render.resolution_percentage=67
s.eevee.taa_render_samples=4
s.eevee.volumetric_tile_size='8';s.eevee.volumetric_samples=24
s.eevee.use_ssr=False
for ob in s.objects:
 if ob.name.startswith('Smoke •'):ob.hide_render=True
os.makedirs(ROOT+'/frames',exist_ok=True)
for f in range(1,193,3):
 s.frame_set(f);s.render.filepath=ROOT+'/frames/%04d.png'%f;bpy.ops.render.render(write_still=True)
