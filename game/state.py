"""Display-independent movement and idle/smoke state."""
from dataclasses import dataclass
import math


@dataclass
class Player:
    x: float = -.7
    z: float = 3.2
    yaw: float = math.pi
    smoke_time: float | None = None
    duration: float = 215 / 24

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
            self.smoke_time += dt
            if self.smoke_time >= self.duration:
                self.smoke_time = None
            return
        length = math.hypot(forward, sideways)
        if not length:
            return
        dx = (math.sin(camera_yaw)*forward - math.cos(camera_yaw)*sideways) / length
        dz = (math.cos(camera_yaw)*forward + math.sin(camera_yaw)*sideways) / length
        self.yaw = math.atan2(dx, dz)
        # Small substeps plus sliding prevent tunnelling through building walls.
        distance = 2.3 * dt
        count = max(1, math.ceil(distance / .08))
        for _ in range(count):
            nx = self.x + dx * distance / count
            if not self.blocked(nx, self.z, obstacles):
                self.x = nx
            nz = self.z + dz * distance / count
            if not self.blocked(self.x, nz, obstacles):
                self.z = nz
