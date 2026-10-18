import math
import unittest
from state import Player


class Controls(unittest.TestCase):
    def test_wasd_and_diagonal_speed(self):
        for forward, side, expected_x, expected_z in [(1, 0, 0, -1), (-1, 0, 0, 1),
                                                       (0, 1, 1, 0), (0, -1, -1, 0)]:
            p = Player(x=0, z=0)
            p.step(.05, forward, side, math.pi, False, [])
            self.assertAlmostEqual(p.x, expected_x*.115)
            self.assertAlmostEqual(p.z, expected_z*.115)
        p = Player(x=0, z=0)
        p.step(.05, 1, 1, math.pi, False, [])
        self.assertAlmostEqual(math.hypot(p.x, p.z), .115)

    def test_smoke_returns_to_idle_and_can_repeat(self):
        p = Player()
        before = (p.x, p.z)
        p.step(.01, 1, 0, 0, True, [])
        for _ in range(100):
            p.step(.05, 1, 0, 0, False, [])
        self.assertIsNotNone(p.smoke_time)
        self.assertEqual(before, (p.x, p.z))
        # Another E press does not interrupt/restart the active action.
        elapsed = p.smoke_time
        p.step(.01, 0, 0, 0, True, [])
        self.assertGreater(p.smoke_time, elapsed)
        for _ in range(100):
            p.step(.05, 0, 0, 0, False, [])
        self.assertIsNone(p.smoke_time)
        p.step(.01, 0, 0, 0, True, [])
        self.assertIsNotNone(p.smoke_time)

    def test_collision_stops_at_building(self):
        p = Player(x=0, z=0)
        for _ in range(50):
            p.step(.05, 1, 0, 0, False, [[-.5, 1, .5, 2]])
        self.assertGreater(p.z, .6)
        self.assertLessEqual(p.z, .76)


if __name__ == '__main__':
    unittest.main()
