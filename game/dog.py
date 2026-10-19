"""Animated Indie dog and distance-attenuated barking in raylib."""
from pathlib import Path
import math
import pyray as rl
from raylib import ffi
from dog_ai import StreetDog


class Dog:
    def __init__(self,assets,config,shader,audio=True):
        self.assets = Path(assets)
        self.actor = StreetDog(config['dog_obstacles'])
        self.model = rl.load_model(str(self.assets/'dog.glb'))
        self.clips = {}
        for name,file in [('idle','dog.glb'),('walk','dog_walk.glb'),('bark','dog_bark.glb')]:
            count = ffi.new('int *')
            clips = rl.load_model_animations(str(self.assets/file),count)
            if not count[0] or not rl.is_model_animation_valid(self.model,clips[0]):
                raise RuntimeError('Street dog animation failed: '+name)
            self.clips[name] = clips,count[0]
        for i in range(self.model.materialCount):
            self.model.materials[i].shader = shader
        self.audio = False
        self.sound = None
        if audio:
            rl.init_audio_device()
            self.audio = rl.is_audio_device_ready()
            if self.audio:
                self.sound = rl.load_sound(str(self.assets/'dog-bark.wav'))
                if not rl.is_sound_valid(self.sound):
                    raise RuntimeError('Dog bark audio could not be loaded')
            else:
                print('DOG_AUDIO_UNAVAILABLE: no playback device; roaming and barking animation remain active',flush=True)

    def update(self,dt,player):
        event = self.actor.update(dt,(player.x,player.z))
        a = self.actor
        base = self.clips['bark' if a.mode=='bark' else 'idle'][0][0]
        if a.mode=='bark':
            fraction = min(.999,a.age/.75)
        elif a.mode=='sniff':
            fraction = min(.999,a.age/a.wait)
        else:
            fraction = 0
        walk = self.clips['walk'][0][0]
        rl.update_model_animation_ex(self.model,base,fraction*(base.keyframeCount-1),
                                     walk,a.phase*(walk.keyframeCount-1),a.walk_weight)
        return event

    def sound_levels(self,camera):
        a = self.actor
        dx,dz = a.x-camera.position.x,a.z-camera.position.z
        distance = math.hypot(dx,dz)
        volume = .85/(1+.12*distance*distance) if distance < 20 else 0
        fx,fz = camera.target.x-camera.position.x,camera.target.z-camera.position.z
        length = max(.001,math.hypot(fx,fz))
        side = (dx*(-fz/length)+dz*(fx/length))/max(1,distance)
        return volume,max(.1,min(.9,.5+.4*side))

    def play_bark(self,event,camera):
        volume,pan = self.sound_levels(camera)
        if self.audio:
            rl.set_sound_volume(self.sound,volume)
            rl.set_sound_pan(self.sound,pan)
            if event:
                rl.play_sound(self.sound)
        return volume,pan

    def draw(self):
        a = self.actor
        rl.draw_model_ex(self.model,rl.Vector3(a.x,0,a.z),rl.Vector3(0,1,0),
                         math.degrees(a.yaw),rl.Vector3(1,1,1),rl.WHITE)

    def close(self):
        if self.sound is not None:
            rl.unload_sound(self.sound)
        if self.audio:
            rl.close_audio_device()
        for clips,count in self.clips.values():
            rl.unload_model_animations(clips,count)
        rl.unload_model(self.model)
