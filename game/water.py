"""Planar puddle reflections, rendered from a camera mirrored in the water plane."""
import json
import struct
from pathlib import Path
import pyray as rl
from raylib import ffi

HEIGHT = .018


def reflect_point(point, height=HEIGHT):
    return (point[0], 2*height-point[1], point[2])


VERTEX = '''#version 330
in vec3 vertexPosition;
in vec2 vertexTexCoord;
uniform mat4 mvp;
uniform mat4 matModel;
uniform mat4 reflectionVP;
out vec3 world;
out vec4 reflectionClip;
out float edge;
void main() {
    world = vec3(matModel*vec4(vertexPosition,1.0));
    reflectionClip = reflectionVP*vec4(world,1.0);
    edge = vertexTexCoord.x;
    gl_Position = mvp*vec4(vertexPosition,1.0);
}
'''
FRAGMENT = '''#version 330
in vec3 world;
in vec4 reflectionClip;
in float edge;
uniform sampler2D texture0;
uniform vec3 viewPosition;
uniform float elapsed;
out vec4 finalColor;
void main() {
    vec2 uv = reflectionClip.xy/reflectionClip.w*0.5+0.5;
    vec2 waves = vec2(sin(world.x*19.0+world.z*8.0+elapsed*1.3),
                      cos(world.z*21.0-world.x*6.0+elapsed*1.1));
    vec3 N = normalize(vec3(waves.x*0.012,1.0,waves.y*0.012));
    vec3 V = normalize(viewPosition-world);
    float facing = max(dot(N,V),0.0);
    float fresnel = 0.05+0.95*pow(1.0-facing,5.0);
    vec3 reflected = pow(texture(texture0,clamp(uv+waves*0.0009,0.002,0.998)).rgb,vec3(2.2));
    // Shallow water transmits the grey lane beneath it rather than opaque black.
    vec3 water = mix(vec3(0.13,0.155,0.145),reflected,0.18+fresnel*0.82);
    vec3 sun = normalize(vec3(-0.4,0.85,0.3));
    float glint = pow(max(dot(N,normalize(V+sun)),0.0),220.0);
    water += vec3(1.0,0.89,0.72)*glint*0.45;
    finalColor = vec4(pow(water,vec3(1.0/2.2)),smoothstep(0.0,0.12,edge));
}
'''


class Water:
    def __init__(self, environment, asset_path):
        self.model = environment
        with Path(asset_path).open('rb') as f:
            f.read(12)
            length, _ = struct.unpack('<II',f.read(8))
            gltf = json.loads(f.read(length))
        # raylib's glTF loader reserves material 0 for its fallback material.
        if environment.materialCount != len(gltf['materials'])+1:
            raise RuntimeError('Unexpected raylib glTF material mapping')
        self.materials = {i+1 for i,m in enumerate(gltf['materials'])
                          if m.get('name','').startswith('Dark shallow puddles')}
        if not self.materials:
            raise RuntimeError('Puddle surface missing from environment')
        self.shader = rl.load_shader_from_memory(VERTEX,FRAGMENT)
        if not rl.is_shader_valid(self.shader):
            raise RuntimeError('Water shader failed to compile')
        self.locations = {n:rl.get_shader_location(self.shader,n)
                          for n in ['reflectionVP','viewPosition','elapsed']}
        self.original = {i:(ffi.new('Shader *',environment.materials[i].shader),
                            ffi.new('Texture *',environment.materials[i].maps[0].texture))
                         for i in self.materials}
        self.target = None
        self.size = None

    def resize(self):
        size = (max(1,rl.get_screen_width()//2),max(1,rl.get_screen_height()//2))
        if size == self.size:
            return
        if self.target is not None:
            rl.unload_render_texture(self.target)
        self.target = rl.load_render_texture(*size)
        if not rl.is_render_texture_valid(self.target):
            raise RuntimeError('Reflection framebuffer could not be allocated')
        rl.set_texture_filter(self.target.texture,rl.TEXTURE_FILTER_BILINEAR)
        self.size = size
        for i in self.materials:
            self.model.materials[i].shader = self.shader
            self.model.materials[i].maps[0].texture = self.target.texture

    def draw_environment(self, puddles=False):
        for i in range(self.model.meshCount):
            material = self.model.meshMaterial[i]
            if (material in self.materials) == puddles:
                rl.draw_mesh(self.model.meshes[i],self.model.materials[material],self.model.transform)

    def begin_reflection(self, camera):
        self.resize()
        def mirror(v):
            return rl.Vector3(*reflect_point((v.x,v.y,v.z)))
        reflected = rl.Camera3D(mirror(camera.position),mirror(camera.target),
                                rl.Vector3(camera.up.x,-camera.up.y,camera.up.z),
                                camera.fovy,camera.projection)
        rl.begin_texture_mode(self.target)
        rl.clear_background(rl.Color(179,199,208,255))
        rl.begin_mode_3d(reflected)
        self.vp = rl.matrix_multiply(rl.rl_get_matrix_modelview(),rl.rl_get_matrix_projection())

    def end_reflection(self):
        rl.end_mode_3d()
        rl.end_texture_mode()

    def draw(self, camera, elapsed):
        rl.set_shader_value_matrix(self.shader,self.locations['reflectionVP'],self.vp)
        rl.set_shader_value(self.shader,self.locations['viewPosition'],
                            ffi.new('float[]',[camera.position.x,camera.position.y,camera.position.z]),
                            rl.SHADER_UNIFORM_VEC3)
        rl.set_shader_value(self.shader,self.locations['elapsed'],ffi.new('float *',elapsed),rl.SHADER_UNIFORM_FLOAT)
        self.draw_environment(puddles=True)

    def close(self):
        for i,(shader,texture) in self.original.items():
            self.model.materials[i].shader = shader[0]
            self.model.materials[i].maps[0].texture = texture[0]
        if self.target is not None:
            rl.unload_render_texture(self.target)
        rl.unload_shader(self.shader)
