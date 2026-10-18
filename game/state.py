"""Display-independent movement and idle/smoke state."""
from dataclasses import dataclass
import math

WALK_SPEED = 1.35
STRIDE_LENGTH = 1.1


@dataclass
class Player:
    x: float = -.7
    z: float = 3.2
    yaw: float = math.pi
    smoke_time: float | None = None
    duration: float = 215 / 24
    walk_phase: float = 0.
    walk_weight: float = 0.
    speed: float = 0.

    def blocked(self, x, z, obstacles):
        radius = .24
        for left, near, right, far in obstacles:
            nx, nz = max(left, min(x, right)), max(near, min(z, far))
            if (x - nx)**2 + (z - nz)**2 < radius**2:
                return True
        return False

    def step(self, dt, forward, sideways, camera_yaw, smoke, obstacles):
        dt = max(0, min(dt, .05))
        if smoke and self.smoke_time is None:
            self.smoke_time = 0.
        if self.smoke_time is not None:
            self.speed = 0.
            self.walk_weight *= math.exp(-15*dt)
            self.smoke_time += dt
            if self.smoke_time >= self.duration:
                self.smoke_time = None
            return
        length = math.hypot(forward, sideways)
        target_speed = 0.
        if length:
            dx = (math.sin(camera_yaw)*forward - math.cos(camera_yaw)*sideways) / length
            dz = (math.cos(camera_yaw)*forward + math.sin(camera_yaw)*sideways) / length
            desired = math.atan2(dx, dz)
            turn = (desired-self.yaw+math.pi) % math.tau-math.pi
            self.yaw += max(-5*dt, min(5*dt, turn))
            remaining = (desired-self.yaw+math.pi) % math.tau-math.pi
            target_speed = WALK_SPEED*max(0,math.cos(remaining))
        self.speed += max(-4*dt,min(3.5*dt,target_speed-self.speed))
        dx,dz = math.sin(self.yaw),math.cos(self.yaw)
        # Small substeps plus sliding prevent tunnelling through building walls.
        before = self.x, self.z
        distance = self.speed * dt
        count = max(1, math.ceil(distance / .08))
        for _ in range(count):
            nx = self.x + dx * distance / count
            if not self.blocked(nx, self.z, obstacles):
                self.x = nx
            nz = self.z + dz * distance / count
            if not self.blocked(self.x, nz, obstacles):
                self.z = nz
        moved = math.hypot(self.x-before[0], self.z-before[1])
        self.walk_phase = (self.walk_phase + moved/STRIDE_LENGTH) % 1
        target = min(1.,moved/(WALK_SPEED*dt)) if dt and moved > .0001 else 0.
        self.walk_weight += (target-self.walk_weight)*(1-math.exp(-12*dt))
