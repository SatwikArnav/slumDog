"""Third-person raylib viewer. Run from any directory with Python 3.12+."""
import argparse
import json
import math
from pathlib import Path

import pyray as rl
from raylib import ffi
from state import Player

HERE = Path(__file__).resolve().parent

VERTEX = '''#version 330
in vec3 vertexPosition;
in vec2 vertexTexCoord;
in vec3 vertexNormal;
in vec4 vertexColor;
uniform mat4 mvp;
uniform mat4 matModel;
uniform mat4 matNormal;
out vec2 uv;
out vec3 normal;
out vec4 color;
void main() {
    uv = vertexTexCoord;
    normal = normalize(vec3(matNormal*vec4(vertexNormal, 0.0)));
    color = vertexColor;
    gl_Position = mvp*vec4(vertexPosition, 1.0);
}
'''
FRAGMENT = '''#version 330
in vec2 uv;
in vec3 normal;
in vec4 color;
uniform sampler2D texture0;
uniform vec4 colDiffuse;
out vec4 finalColor;
void main() {
    vec4 base = texture(texture0, uv)*colDiffuse*color;
    if (base.a < 0.25) discard;
    float sunlight = max(dot(normalize(normal), normalize(vec3(-0.4, 0.85, 0.3))), 0.0);
    finalColor = vec4(base.rgb*(0.58 + 0.42*sunlight), base.a);
}
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true', help='Run scripted movement/smoke checks and capture frames')
    args = parser.parse_args()
    for name in ('environment.glb', 'character.glb', 'scene.json'):
        if not (HERE / 'assets' / name).is_file():
            parser.error('Missing exported assets. Run blender -b --python game/export_assets.py first.')
    config = json.loads((HERE / 'assets' / 'scene.json').read_text())
    player = Player(x=config['spawn'][0], z=config['spawn'][2], duration=config['smoking_seconds'])
    rl.set_config_flags(rl.FLAG_MSAA_4X_HINT | rl.FLAG_WINDOW_RESIZABLE)
    rl.init_window(1100, 700, 'slumDog | Shanti Nagar')
    rl.set_target_fps(60)
    environment = rl.load_model(str(HERE / 'assets/environment.glb'))
    character = rl.load_model(str(HERE / 'assets/character.glb'))
    if environment.meshCount == 0 or character.meshCount == 0:
        raise RuntimeError('Model loading failed')
    count = ffi.new('int *')
    animations = rl.load_model_animations(str(HERE / 'assets/character.glb'), count)
    if count[0] == 0:
        raise RuntimeError('Smoking animation missing from character export')
    animation = animations[0]
    if not rl.is_model_animation_valid(character, animation):
        raise RuntimeError('Animation skeleton does not match character')
    print('LOADED', environment.meshCount, 'environment meshes;', character.meshCount,
          'character meshes;', animation.keyframeCount, 'animation keyframes', flush=True)
    shader = rl.load_shader_from_memory(VERTEX, FRAGMENT)
    for model in (environment, character):
        for i in range(model.materialCount):
            model.materials[i].shader = shader
    yaw, pitch, distance = math.pi, .18, 2.7
    captured = not args.verify
    if captured:
        rl.disable_cursor()
    camera = rl.Camera3D(rl.Vector3(), rl.Vector3(), rl.Vector3(0, 1, 0), 58, rl.CAMERA_PERSPECTIVE)
    stage = 0
    initial = (player.x, player.z)
    signatures = []
    while not rl.window_should_close():
        dt = min(rl.get_frame_time(), .05)
        if args.verify:
            if stage == 1:
                for _ in range(20):
                    player.step(.05, 1, 0, yaw, False, config['collision'])
                assert math.hypot(player.x-initial[0], player.z-initial[1]) > 1
            elif stage == 2:
                player.step(.01, 0, 0, yaw, True, config['collision'])
                player.smoke_time = 3.2
            elif stage == 3:
                player.smoke_time = 6.0
            elif stage == 4:
                player.smoke_time = player.duration - .01
                player.step(.02, 0, 0, yaw, False, config['collision'])
                assert player.smoke_time is None
        else:
            if rl.is_key_pressed(rl.KEY_TAB):
                captured = not captured
                rl.disable_cursor() if captured else rl.enable_cursor()
            if captured:
                mouse = rl.get_mouse_delta()
                yaw -= mouse.x*.003
                pitch = max(-.15, min(.75, pitch + mouse.y*.003))
            distance = max(1.3, min(5., distance - rl.get_mouse_wheel_move()*.3))
            player.step(dt, int(rl.is_key_down(rl.KEY_W))-int(rl.is_key_down(rl.KEY_S)),
                        int(rl.is_key_down(rl.KEY_D))-int(rl.is_key_down(rl.KEY_A)),
                        yaw, rl.is_key_pressed(rl.KEY_E), config['collision'])
            if rl.is_key_pressed(rl.KEY_R):
                player = Player(x=config['spawn'][0], z=config['spawn'][2], duration=config['smoking_seconds'])
                yaw = math.pi

        # raylib samples glTF animations at 60 keyframes/sec, independently of Blender FPS.
        fraction = 0 if player.smoke_time is None else min(player.smoke_time/player.duration, .9999)
        rl.update_model_animation(character, animation, fraction*(animation.keyframeCount-1))
        # Follow camera with a ray against the environment to avoid crossing walls.
        target = rl.Vector3(player.x, 1.35, player.z)
        offset = rl.Vector3(-math.sin(yaw)*math.cos(pitch)*distance,
                            .45+math.sin(pitch)*distance, -math.cos(yaw)*math.cos(pitch)*distance)
        length = math.sqrt(offset.x**2+offset.y**2+offset.z**2)
        direction = rl.Vector3(offset.x/length, offset.y/length, offset.z/length)
        safe = length
        ray = rl.Ray(target, direction)
        for i in range(environment.meshCount):
            hit = rl.get_ray_collision_mesh(ray, environment.meshes[i], environment.transform)
            if hit.hit:
                safe = min(safe, max(.3, hit.distance-.15))
        camera.target = target
        camera.position = rl.Vector3(target.x+direction.x*safe, target.y+direction.y*safe,
                                     target.z+direction.z*safe)
        rl.begin_drawing()
        rl.clear_background(rl.Color(179, 199, 208, 255))
        rl.begin_mode_3d(camera)
        rl.draw_model(environment, rl.Vector3(0, 0, 0), 1., rl.WHITE)
        rl.draw_model_ex(character, rl.Vector3(player.x, 0, player.z), rl.Vector3(0, 1, 0),
                         math.degrees(player.yaw), rl.Vector3(1, 1, 1), rl.WHITE)
        # Lightweight real-time exhale; Blender volume shaders cannot run in raylib.
        if player.smoke_time is not None and 4.9 < player.smoke_time < 8.5:
            t = player.smoke_time - 4.9
            for i in range(12):
                age = (t-i*.09) % 1.3
                if t < i*.09:
                    continue
                forward = .15 + age*.35
                pos = rl.Vector3(player.x+math.sin(player.yaw)*forward,
                                 1.65+age*.16, player.z+math.cos(player.yaw)*forward)
                rl.draw_sphere(pos, .015+age*.045, rl.Color(207, 211, 209, int(100*(1-age/1.3))))
        rl.end_mode_3d()
        rl.draw_rectangle(0, 0, rl.get_screen_width(), 79, rl.Color(18, 24, 24, 225))
        rl.draw_text('SHANTI NAGAR', 20, 13, 24, rl.RAYWHITE)
        rl.draw_text('WASD move   Mouse look   E smoke   Wheel zoom   Tab release mouse   R reset   Esc exit',
                     20, 47, 17, rl.LIGHTGRAY)
        status = 'IDLE  |  Press E to smoke' if player.smoke_time is None else 'SMOKING  |  Returns to idle when finished'
        rl.draw_rectangle(12, rl.get_screen_height()-46, 490, 34, rl.Color(18, 24, 24, 225))
        rl.draw_text(status, 23, rl.get_screen_height()-37, 18, rl.RAYWHITE)
        rl.draw_fps(rl.get_screen_width()-95, 15)
        rl.end_drawing()
        if args.verify:
            captures = HERE / 'captures'
            captures.mkdir(exist_ok=True)
            image = rl.load_image_from_screen()
            path = captures / f'{stage:02d}.png'
            assert rl.export_image(image, str(path)), 'Capture export failed'
            rl.unload_image(image)
            assert path.is_file()
            # Animation must deform mesh geometry, not just advance a state label.
            mesh = character.meshes[0]
            if mesh.animVertices != ffi.NULL:
                signatures.append(tuple(round(mesh.animVertices[i], 5) for i in range(min(mesh.vertexCount*3, 900))))
            stage += 1
            if stage == 5:
                assert len(set(signatures)) > 1, 'Character vertices did not animate'
                print('GAME_VERIFY_OK: moved, idle -> smoke -> idle, animated vertices changed, five captures', flush=True)
                break
    rl.unload_model_animations(animations, count[0])
    rl.unload_model(character)
    rl.unload_model(environment)
    rl.unload_shader(shader)
    rl.close_window()


if __name__ == '__main__':
    main()
