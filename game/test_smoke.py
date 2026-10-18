import unittest
from smoke import Smoke, socket_at, world_socket, texture_rgba


class SmokeChecks(unittest.TestCase):
    def test_exhale_timing_and_persistent_drift(self):
        s = Smoke()
        for _ in range(20):
            s.update(.05, (0,1.6,0), (1,1,0), 0, 3.)
        before = len(s.particles)
        for _ in range(20):
            s.update(.05, (0,1.6,0), (1,1,0), 0, 5.5)
        self.assertGreater(len(s.particles), before+40)
        exhaled = next(p for p in s.particles if p.opacity == 30)
        old = (exhaled.x, exhaled.y, exhaled.z, exhaled.radius)
        s.update(.05, (0,1.6,0), (1,1,0), 0, None)
        self.assertGreater(exhaled.y, old[1])
        self.assertGreater(exhaled.radius, old[3])
        self.assertGreater(exhaled.z, old[2])
        for _ in range(80):
            s.update(.05, (0,1.6,0), (1,1,0), 0, None)
        self.assertNotIn(exhaled, s.particles)

    def test_sprite_has_transparent_edges_and_density(self):
        rgba = texture_rgba(32)
        self.assertEqual(len(rgba), 32*32*4)
        self.assertEqual(rgba[3], 0)
        self.assertGreater(rgba[(16*32+16)*4+3], 40)

    def test_socket_interpolation_and_rotation(self):
        track = [[[0,1,0],[0,0,1]], [[0,3,0],[0,0,3]]]
        self.assertEqual(socket_at(track,.5), [[0,2,0],[0,0,2]])
        self.assertEqual(world_socket((0,1,2), 3,4,0), (3,1,6))


if __name__ == '__main__':
    unittest.main()
