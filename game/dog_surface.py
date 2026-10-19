"""Short-coat lighting and a soft ground contact shadow for the street dog."""
import math
import pyray as rl
from raylib import ffi

FRAGMENT = '''#version 330
in vec2 uv;
in vec3 normal;
in vec4 color;
in vec3 worldPosition;
uniform sampler2D texture0;
uniform sampler2D texture2;
uniform vec4 colDiffuse;
uniform vec3 eyePosition;
uniform int reflectionPass;
out vec4 finalColor;
void main() {
    if (reflectionPass == 1 && worldPosition.y < 0.019) discard;
    vec4 texel = texture(texture0, uv);
    vec3 base = pow(texel.rgb,vec3(2.2))*colDiffuse.rgb*color.rgb;
    vec3 n = normalize(normal);
    vec3 micro = texture(texture2,uv).rgb;
    if (micro.b > .7 && micro.r < .85 && micro.g < .85) {
        vec3 q1 = dFdx(worldPosition), q2 = dFdy(worldPosition);
        vec2 t1 = dFdx(uv), t2 = dFdy(uv);
        vec3 tangent = q1*t2.y-q2*t1.y;
        vec3 bitangent = -q1*t2.x+q2*t1.x;
        float determinant = t1.x*t2.y-t1.y*t2.x;
        if (abs(determinant)>1e-10 && dot(tangent,tangent)>1e-10) {
            tangent = normalize(tangent*sign(determinant));
            bitangent = normalize(bitangent*sign(determinant));
            n = normalize(mat3(tangent,bitangent,n)*(micro*2.0-1.0));
        }
    }
    vec3 light = normalize(vec3(-0.4,0.85,0.3));
    vec3 view = normalize(eyePosition-worldPosition);
    float diffuse = max(0.0,dot(n,light));
    // Sky/ground fill keeps the underside shaded; the old constant ambient
    // made the torso and face read as flat solid-colour silhouettes.
    vec3 fill = mix(vec3(.16,.13,.10),vec3(.42,.47,.52),n.y*.5+.5);
    vec3 lit = base*(fill+vec3(1.02,.94,.81)*diffuse);
    float darkSurface = 1.0-smoothstep(.018,.065,max(base.r,max(base.g,base.b)));
    float highlight = pow(max(0.0,dot(n,normalize(light+view))),48.0);
    lit += vec3(.13)*highlight*darkSurface;
    // Restrained grazing sheen on short hair, without a plastic body highlight.
    lit += base*.12*pow(1.0-max(0.0,dot(n,view)),3.0)*diffuse;
    finalColor = vec4(pow(max(lit,vec3(0)),vec3(1.0/2.2)),texel.a*colDiffuse.a*color.a);
}
'''


class ContactShadow:
    def __init__(self):
        size = 128
        pixels = bytearray()
        for y in range(size):
            for x in range(size):
                r2 = ((x+.5)/size*2-1)**2+((y+.5)/size*2-1)**2
                alpha = int(75*max(0,math.exp(-3*r2)-math.exp(-3))/(1-math.exp(-3)))
                pixels.extend((24,20,16,alpha))
        data = ffi.new('unsigned char[]',bytes(pixels))
        self.texture = rl.load_texture_from_image(rl.Image(data,size,size,1,rl.PIXELFORMAT_UNCOMPRESSED_R8G8B8A8))
        rl.set_texture_filter(self.texture,rl.TEXTURE_FILTER_BILINEAR)
        self.model = rl.load_model_from_mesh(rl.gen_mesh_plane(1,1,1,1))
        self.model.materials[0].maps[rl.MATERIAL_MAP_ALBEDO].texture = self.texture

    def draw(self,x,z,yaw):
        rl.rl_draw_render_batch_active()
        rl.rl_disable_depth_mask()
        rl.draw_model_ex(self.model,rl.Vector3(x+.08,.009,z-.04),rl.Vector3(0,1,0),
                         math.degrees(yaw),rl.Vector3(.53,1,1.1),rl.WHITE)
        rl.rl_draw_render_batch_active()
        rl.rl_enable_depth_mask()

    def close(self):
        rl.unload_model(self.model)
        rl.unload_texture(self.texture)
