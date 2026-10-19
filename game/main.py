"""Third-person raylib viewer. Run from any directory with Python 3.12+."""
import argparse
import json
import math
import hashlib
from pathlib import Path

import pyray as rl
from raylib import ffi
from state import Player
from smoke import Smoke, texture_rgba, socket_at, world_socket
from water import Water, HEIGHT
from record_preview import Preview
from dog import Dog

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
out vec3 worldPosition;
void main() {
    uv = vertexTexCoord;
    normal = normalize(vec3(matNormal*vec4(vertexNormal, 0.0)));
    color = vertexColor;
    worldPosition = vec3(matModel*vec4(vertexPosition,1.0));
    gl_Position = mvp*vec4(vertexPosition, 1.0);
}
'''
FRAGMENT = '''#version 330
in vec2 uv;
in vec3 normal;
in vec4 color;
in vec3 worldPosition;
uniform int reflectionPass;
uniform float waterHeight;
uniform sampler2D texture0;
uniform vec4 colDiffuse;
out vec4 finalColor;
void main() {
    if (reflectionPass == 1 && worldPosition.y < waterHeight+0.001) discard;
    vec4 texel = texture(texture0, uv);
    vec4 base = vec4(pow(texel.rgb, vec3(2.2))*colDiffuse.rgb*color.rgb,
                     texel.a*colDiffuse.a*color.a);
    if (base.a < 0.25) discard;
    float sunlight = max(dot(normalize(normal), normalize(vec3(-0.4, 0.85, 0.3))), 0.0);
    finalColor = vec4(pow(base.rgb*(0.65 + 0.55*sunlight), vec3(1.0/2.2)), base.a);
}
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true', help='Run scripted movement/smoke checks and capture frames')
    parser.add_argument('--record',metavar='MP4',help='Record a 20-second scripted gameplay preview (requires ffmpeg)')
    parser.add_argument('--record-dog',metavar='MP4',help='Record the roaming dog with bark audio')
    parser.add_argument('--mute',action='store_true',help='Disable live audio playback')
    args = parser.parse_args()
    dog_focus = bool(args.record_dog)
    if args.record_dog:
        if args.record:
            parser.error('Choose one recording mode')
        args.record = args.record_dog
    if args.verify and args.record:
        parser.error('Use either --verify or --record')
    for name in ('environment.glb', 'character.glb', 'walk.glb', 'scene.json',
                 'dog.glb','dog_walk.glb','dog_bark.glb','dog-bark.wav'):
        if not (HERE / 'assets' / name).is_file():
            parser.error('Missing exported assets. Run blender -b --python game/export_assets.py first.')
    config = json.loads((HERE / 'assets' / 'scene.json').read_text())
    player = Player(x=config['spawn'][0], z=config['spawn'][2], duration=config['smoking_seconds'])
    rl.set_config_flags(rl.FLAG_MSAA_4X_HINT | rl.FLAG_WINDOW_RESIZABLE)
    rl.init_window(960 if args.record else 1100, 640 if args.record else 700, 'slumDog | Shanti Nagar')
    rl.set_target_fps(0 if args.record else 60)
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
    walk_count = ffi.new('int *')
    walks = rl.load_model_animations(str(HERE / 'assets/walk.glb'), walk_count)
    if not walk_count[0] or not rl.is_model_animation_valid(character, walks[0]):
        raise RuntimeError('Walking animation missing or skeleton mismatch')
    walk = walks[0]
    smoke = Smoke()
    pixels = ffi.new('unsigned char[]', bytes(texture_rgba()))
    smoke_texture = rl.load_texture_from_image(rl.Image(pixels, 128, 128, 1,
                                                       rl.PIXELFORMAT_UNCOMPRESSED_R8G8B8A8))
    rl.set_texture_filter(smoke_texture, rl.TEXTURE_FILTER_BILINEAR)
    print('LOADED', environment.meshCount, 'environment meshes;', character.meshCount,
          'character meshes;', animation.keyframeCount, 'animation keyframes', flush=True)
    shader = rl.load_shader_from_memory(VERTEX, FRAGMENT)
    filtered = set()
    for model in (environment, character):
        for i in range(model.materialCount):
            model.materials[i].shader = shader
            surface = model.materials[i].maps[rl.MATERIAL_MAP_ALBEDO]
            if surface.texture.id not in filtered:
                if surface.texture.width > 1 and surface.texture.height > 1:
                    rl.gen_texture_mipmaps(ffi.addressof(surface,'texture'))
                    rl.set_texture_filter(surface.texture,rl.TEXTURE_FILTER_TRILINEAR)
                filtered.add(surface.texture.id)
    dog = Dog(HERE/'assets',config,VERTEX,audio=not (args.mute or args.record))
    water = Water(environment,HERE / 'assets/environment.glb')
    reflection_location = rl.get_shader_location(shader,'reflectionPass')
    rl.set_shader_value(shader,rl.get_shader_location(shader,'waterHeight'),ffi.new('float *',HEIGHT),rl.SHADER_UNIFORM_FLOAT)
    yaw, pitch, distance = math.pi, .18, 2.7
    captured = not (args.verify or args.record)
    if captured:
        rl.disable_cursor()
    camera = rl.Camera3D(rl.Vector3(), rl.Vector3(), rl.Vector3(0, 1, 0), 58, rl.CAMERA_PERSPECTIVE)
    stage = 0
    initial = (player.x, player.z)
    signatures = []
    recording = Preview(args.record,dog_focus=dog_focus) if args.record else None
    while not rl.window_should_close():
        dt = 1/recording.fps if recording else min(rl.get_frame_time(), .05)
        dog_bounds = [dog.actor.x-.22,dog.actor.z-.22,dog.actor.x+.22,dog.actor.z+.22]
        obstacles = config['collision']+[dog_bounds]
        if recording:
            player,yaw = recording.step(player,{**config,'collision':obstacles})
        elif args.verify:
            if stage == 1:
                for _ in range(20):
                    player.step(.05, 1, 0, yaw, False, config['collision'])
                assert math.hypot(player.x-initial[0], player.z-initial[1]) > 1
            elif stage == 2:
                player.walk_phase = (player.walk_phase+.5) % 1
            elif stage == 3:
                player.step(.01, 0, 0, yaw, True, config['collision'])
                player.smoke_time = 3.2
                player.walk_weight = 0
            elif stage == 4:
                player.smoke_time = 5.7
            elif stage == 5:
                player.smoke_time = 7.0
            elif stage == 6:
                player.smoke_time = player.duration - .01
                player.step(.02, 0, 0, yaw, False, config['collision'])
                assert player.smoke_time is None
            elif stage == 8:
                rl.set_window_size(960,640)
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
                        yaw, rl.is_key_pressed(rl.KEY_E), obstacles)
            if rl.is_key_pressed(rl.KEY_R):
                player = Player(x=config['spawn'][0], z=config['spawn'][2], duration=config['smoking_seconds'])
                yaw = math.pi

        # raylib samples glTF animations at 60 keyframes/sec, independently of Blender FPS.
        fraction = 0 if player.smoke_time is None else min(player.smoke_time/player.duration, .9999)
        rl.update_model_animation_ex(character, animation, fraction*(animation.keyframeCount-1),
                                     walk, player.walk_phase*(walk.keyframeCount-1), player.walk_weight)
        idle_sockets = socket_at(config['smoke_sockets'], fraction)
        walk_sockets = socket_at(config['walk_sockets'], player.walk_phase)
        anchors = [world_socket([a*(1-player.walk_weight)+b*player.walk_weight
                                  for a,b in zip(idle, moving)], player.x, player.z, player.yaw)
                   for idle,moving in zip(idle_sockets,walk_sockets)]
        if args.verify and stage in (4,5):
            for i in range(24):
                smoke.update(.05, *anchors, player.yaw,
                             4.9+i*.05 if stage == 4 else 7.0)
        else:
            smoke.update(dt, *anchors, player.yaw, player.smoke_time)
        bark_event = dog.update(dt,player)
        if args.verify and stage == 9:
            travelled = 0.
            for _ in range(200):
                before = dog.actor.x,dog.actor.z
                bark_event = dog.update(.025,player) or bark_event
                travelled += math.dist(before,(dog.actor.x,dog.actor.z))
            assert travelled > .5,'Dog did not roam in the live scene'
        elif args.verify and stage == 10:
            dog.actor.cooldown = dog.actor.ambient = 0
            assert dog.update(.025,player),'Dog did not trigger a bark'
            for _ in range(7):
                dog.update(.05,player)
            bark_event = True
            assert dog.actor.mode == 'bark'
        # Follow camera with a ray against the environment to avoid crossing walls.
        target = rl.Vector3(player.x, 1.35, player.z)
        view_yaw = player.yaw+1.15 if args.verify and stage >= 1 else yaw
        camera_distance = distance
        if dog_focus:
            target = rl.Vector3(dog.actor.x,.38,dog.actor.z)
            view_yaw = dog.actor.yaw+1.35+1.4*(recording.time/recording.duration)
            camera_distance = 1.6
        offset = rl.Vector3(-math.sin(view_yaw)*math.cos(pitch)*camera_distance,
                            .45+math.sin(pitch)*camera_distance, -math.cos(view_yaw)*math.cos(pitch)*camera_distance)
        if dog_focus:
            offset.y = .27
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
        if args.verify and 7 <= stage <= 8:
            camera.position = rl.Vector3(1.2 if stage == 7 else .15,.68,1.0)
            camera.target = rl.Vector3(.665,HEIGHT,-.307)
        elif args.verify and stage >= 9:
            angle = dog.actor.yaw+math.pi/2
            camera.target = rl.Vector3(dog.actor.x,.38,dog.actor.z)
            camera.position = rl.Vector3(dog.actor.x-math.sin(angle)*1.5,1.0,
                                         dog.actor.z-math.cos(angle)*1.5)
        volume,pan = dog.play_bark(bark_event,camera)
        if args.verify and stage == 10 and dog.audio:
            assert rl.is_sound_playing(dog.sound),'Dog bark was not submitted to the audio device'
            print('DOG_BARK_PLAYBACK_OK',flush=True)
        if bark_event and recording:
            recording.bark(volume,pan)
        # Mirror only surfaces above the puddle plane; the ground must not hide
        # the reflected buildings, and water must not reflect itself recursively.
        rl.set_shader_value(shader,reflection_location,ffi.new('int *',1),rl.SHADER_UNIFORM_INT)
        water.begin_reflection(camera)
        water.draw_environment()
        rl.draw_model_ex(character,rl.Vector3(player.x,0,player.z),rl.Vector3(0,1,0),
                         math.degrees(player.yaw),rl.Vector3(1,1,1),rl.WHITE)
        dog.draw(camera,reflection=True)
        water.end_reflection()
        rl.set_shader_value(shader,reflection_location,ffi.new('int *',0),rl.SHADER_UNIFORM_INT)
        rl.begin_drawing()
        rl.clear_background(rl.Color(179, 199, 208, 255))
        rl.begin_mode_3d(camera)
        water.draw_environment()
        rl.draw_model_ex(character, rl.Vector3(player.x, 0, player.z), rl.Vector3(0, 1, 0),
                         math.degrees(player.yaw), rl.Vector3(1, 1, 1), rl.WHITE)
        dog.draw(camera)
        water.draw(camera,recording.time if recording else rl.get_time())
        # Depth-test against the street, but do not let transparent puffs occlude
        # each other. Back-to-front sorting gives stable alpha compositing.
        rl.rl_draw_render_batch_active()
        rl.rl_disable_depth_mask()
        particles = sorted(smoke.particles, key=lambda p: (
            (p.x-camera.position.x)**2+(p.y-camera.position.y)**2+(p.z-camera.position.z)**2), reverse=True)
        for puff in particles:
            radius = puff.radius
            rl.draw_billboard_pro(camera, smoke_texture, rl.Rectangle(0,0,128,128),
                                  rl.Vector3(puff.x,puff.y,puff.z), rl.Vector3(0,1,0),
                                  rl.Vector2(radius*2,radius*2), rl.Vector2(radius,radius),
                                  puff.rotation, rl.Color(240,244,248,int(puff.alpha)))
        rl.rl_draw_render_batch_active()
        rl.rl_enable_depth_mask()
        rl.end_mode_3d()
        rl.draw_rectangle(0, 0, rl.get_screen_width(), 79, rl.Color(18, 24, 24, 225))
        rl.draw_text('SHANTI NAGAR', 20, 13, 24, rl.RAYWHITE)
        rl.draw_text('WASD move   Mouse look   E smoke   Wheel zoom   Tab release mouse   R reset   Esc exit',
                     20, 47, 17, rl.LIGHTGRAY)
        status = ('WALKING' if player.walk_weight > .1 else 'IDLE')+'  |  Press E to smoke'
        if player.smoke_time is not None:
            status = 'SMOKING  |  Returns to idle when finished'
        if dog_focus or (args.verify and stage >= 9):
            status = 'INDIAN STREET DOG  |  '+dog.actor.mode.upper()
        rl.draw_rectangle(12, rl.get_screen_height()-46, 490, 34, rl.Color(18, 24, 24, 225))
        rl.draw_text(status, 23, rl.get_screen_height()-37, 18, rl.RAYWHITE)
        if recording:
            rl.draw_text('PREVIEW',rl.get_screen_width()-100,15,18,rl.LIGHTGRAY)
        else:
            rl.draw_fps(rl.get_screen_width()-95, 15)
        rl.end_drawing()
        if recording and recording.capture():
            break
        if args.verify:
            captures = HERE / 'captures'
            captures.mkdir(exist_ok=True)
            image = rl.load_image_from_screen()
            path = captures / f'{stage:02d}.png'
            assert rl.export_image(image, str(path)), 'Capture export failed'
            rl.unload_image(image)
            assert path.is_file()
            if stage == 7:
                reflected_image = rl.load_image_from_texture(water.target.texture)
                assert rl.export_image(reflected_image,str(captures/'reflection.png'))
                rl.unload_image(reflected_image)
            if stage == 8:
                assert water.size == (rl.get_screen_width()//2,rl.get_screen_height()//2)
            # Animation must deform mesh geometry, not just advance a state label.
            signature = hashlib.sha256()
            for i in range(character.meshCount):
                mesh = character.meshes[i]
                if mesh.animVertices != ffi.NULL:
                    signature.update(ffi.buffer(mesh.animVertices,mesh.vertexCount*3*4))
            signatures.append(signature.digest())
            stage += 1
            if stage == 11:
                assert len(set(signatures)) > 1, 'Character vertices did not animate'
                assert signatures[1] != signatures[2], 'Walk poses did not change'
                assert signatures[3] != signatures[0], 'Smoking pose did not change'
                print('GAME_VERIFY_OK: player, puddles, roaming dog and bark, eleven captures', flush=True)
                break
    if recording:
        recording.close()
    dog.close()
    rl.unload_model_animations(animations, count[0])
    rl.unload_model_animations(walks, walk_count[0])
    rl.unload_texture(smoke_texture)
    water.close()
    rl.unload_model(character)
    rl.unload_model(environment)
    rl.unload_shader(shader)
    rl.close_window()


if __name__ == '__main__':
    main()
