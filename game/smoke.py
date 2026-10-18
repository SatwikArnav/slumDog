"""Persistent wind-advected smoke particles; rendering is kept in main.py."""
from dataclasses import dataclass
import math
import random


@dataclass
class Puff:
    x: float
    y: float
    z: float
    vx: float
    vy: float
    vz: float
    life: float
    size: float
    opacity: float
    rotation: float
    age: float = 0.

    @property
    def radius(self):
        return self.size + self.age*.045

    @property
    def alpha(self):
        t = self.age/self.life
        return max(0, self.opacity*min(1, t*12)*(1-t)**1.6)


class Smoke:
    def __init__(self, seed=7):
        self.random = random.Random(seed)
        self.particles = []
        self.clock = 0.
        self.carry = [0., 0.]

    def update(self, dt, mouth, ember, yaw, smoking_time):
        dt = min(.05, max(0, dt))
        self.clock += dt
        for p in self.particles:
            p.age += dt
            drag = math.exp(-1.3*dt)
            p.vx *= drag
            p.vz *= drag
            p.vy += .045*dt
            wobble = math.sin(p.rotation*.017+p.age*3.1)
            p.x += (p.vx + .035 + .025*wobble)*dt
            p.y += p.vy*dt
            p.z += (p.vz+.02*math.cos(p.age*2+p.rotation))*dt
            p.rotation += dt*12
        self.particles = [p for p in self.particles if p.age < p.life]
        exhaling = smoking_time is not None and 4.88 <= smoking_time < 6.5
        # Cigarette wisps persist between draws, with lower output during inhalation.
        drawing = smoking_time is not None and 2.7 <= smoking_time < 4.5
        for channel, origin, rate in [(0, ember, 5 if drawing else 16),
                                      (1, mouth, 65 if exhaling else 0)]:
            self.carry[channel] += rate*dt
            while self.carry[channel] >= 1:
                self.carry[channel] -= 1
                r = self.random
                speed = r.uniform(.65, 1.0) if channel else .02
                self.particles.append(Puff(
                    origin[0]+r.uniform(-.004,.004), origin[1]+r.uniform(-.004,.004),
                    origin[2]+r.uniform(-.004,.004),
                    math.sin(yaw)*speed+r.uniform(-.035,.035),
                    r.uniform(.07,.13) if channel else r.uniform(.07,.11),
                    math.cos(yaw)*speed+r.uniform(-.035,.035),
                    r.uniform(2.0,3.2), .018 if channel else .006,
                    30 if channel else 24, r.uniform(0,360)))


def texture_rgba(size=128):
    """Feathered density sprite, with layered noise to break up circular outlines."""
    def noise(x, y):
        def value(a, b):
            n = math.sin(a*127.1+b*311.7)*43758.5453
            return n-math.floor(n)
        a, b = math.floor(x), math.floor(y)
        u, v = x-a, y-b
        u, v = u*u*(3-2*u), v*v*(3-2*v)
        return ((1-u)*value(a,b)+u*value(a+1,b))*(1-v)+((1-u)*value(a,b+1)+u*value(a+1,b+1))*v
    pixels = bytearray()
    for y in range(size):
        for x in range(size):
            u, v = (x+.5)/size*2-1, (y+.5)/size*2-1
            radial = max(0, 1-u*u-v*v)**2.4
            density = sum(noise(u*f+12,v*f+19)*w for f,w in [(3,.5),(7,.3),(15,.2)])
            pixels.extend((220, 226, 230, int(255*radial*(.25+.75*density))))
    return pixels


def socket_at(track, fraction):
    position = min(1, max(0, fraction))*(len(track)-1)
    a = int(position)
    b = min(a+1,len(track)-1)
    t = position-a
    return [[track[a][s][j]*(1-t)+track[b][s][j]*t for j in range(3)] for s in range(2)]


def world_socket(point, x, z, yaw):
    return (x+point[0]*math.cos(yaw)+point[2]*math.sin(yaw), point[1],
            z-point[0]*math.sin(yaw)+point[2]*math.cos(yaw))
