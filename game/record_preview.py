"""Deterministic capture of real game frames, encoded directly with ffmpeg."""
from pathlib import Path
import math
import shutil
import subprocess
import pyray as rl
from raylib import ffi
from state import Player


class Preview:
    fps = 24
    duration = 20

    def __init__(self,output):
        ffmpeg = shutil.which('ffmpeg')
        if not ffmpeg:
            raise RuntimeError('Video recording requires ffmpeg on PATH')
        self.output = Path(output).resolve()
        self.output.parent.mkdir(parents=True,exist_ok=True)
        self.frame = 0
        self.process = subprocess.Popen([
            ffmpeg,'-hide_banner','-loglevel','error','-y','-f','rawvideo',
            '-pixel_format','rgba','-video_size',f'{rl.get_screen_width()}x{rl.get_screen_height()}',
            '-framerate',str(self.fps),'-i','pipe:0','-an','-c:v','libx264',
            '-preset','medium','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(self.output)
        ],stdin=subprocess.PIPE,stderr=subprocess.PIPE)

    @property
    def time(self):
        return self.frame/self.fps

    def step(self,player,config):
        if self.frame in (0,5*self.fps):
            player = Player(x=config['spawn'][0],z=config['spawn'][2],duration=config['smoking_seconds'])
        t = self.time
        walking = 1 <= t < 9
        smoke = self.frame == int(9.5*self.fps)
        player.step(1/self.fps,int(walking),0,math.pi,smoke,config['collision'])
        view_yaw = math.pi if t < 5 else 2*math.pi-.35
        return player,view_yaw

    def capture(self):
        image = rl.load_image_from_screen()
        try:
            assert image.format == rl.PIXELFORMAT_UNCOMPRESSED_R8G8B8A8
            self.process.stdin.write(ffi.buffer(image.data,image.width*image.height*4))
        finally:
            rl.unload_image(image)
        self.frame += 1
        if self.frame % self.fps == 0:
            print('PREVIEW_RECORDED',self.frame//self.fps,'/',self.duration,'seconds',flush=True)
        return self.frame >= self.duration*self.fps

    def close(self):
        self.process.stdin.close()
        error = self.process.stderr.read().decode(errors='replace')
        code = self.process.wait()
        if code:
            raise RuntimeError(f'ffmpeg failed ({code}): {error}')
        print('PREVIEW_VIDEO_SAVED',self.output,self.frame,'frames',flush=True)
