"""Display-independent movement and idle/smoke state."""
from dataclasses import dataclass
import math

WALK_SPEED = 1.5
STRIDE_LENGTH = 1.2


@dataclass
class Player:
    x: float = -.7
    z: float = 3.2
    yaw: float = math.pi
    smoke_time: float | None = None
    duration: float = 215 / 24
    walk_phase: float = 0.
    walk_weight: float = 0.

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
            self.walk_weight *= math.exp(-15*dt)
            self.smoke_time += dt
            if self.smoke_time >= self.duration:
                self.smoke_time = None
            return
        length = math.hypot(forward, sideways)
        if not length:
            self.walk_weight *= math.exp(-12*dt)
            return
        dx = (math.sin(camera_yaw)*forward - math.cos(camera_yaw)*sideways) / length
        dz = (math.cos(camera_yaw)*forward + math.sin(camera_yaw)*sideways) / length
        desired = math.atan2(dx, dz)
        turn = (desired-self.yaw+math.pi) % math.tau-math.pi
        self.yaw += max(-10*dt, min(10*dt, turn))
        # Small substeps plus sliding prevent tunnelling through building walls.
        before = self.x, self.z
        distance = WALK_SPEED * dt
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
        target = 1. if moved > .0001 else 0.
        self.walk_weight += (target-self.walk_weight)*(1-math.exp(-12*dt))
