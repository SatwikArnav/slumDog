import math
import unittest
from state import Player, WALK_SPEED, STRIDE_LENGTH


class Controls(unittest.TestCase):
    def test_wasd_and_diagonal_speed(self):
        for forward, side, expected_x, expected_z in [(1, 0, 0, -1), (-1, 0, 0, 1),
                                                       (0, 1, 1, 0), (0, -1, -1, 0)]:
            p = Player(x=0,z=0,yaw=math.atan2(expected_x,expected_z),speed=WALK_SPEED)
            p.step(.05, forward, side, math.pi, False, [])
            self.assertAlmostEqual(p.x, expected_x*WALK_SPEED*.05)
            self.assertAlmostEqual(p.z, expected_z*WALK_SPEED*.05)
        p = Player(x=0,z=0,yaw=3*math.pi/4,speed=WALK_SPEED)
        p.step(.05, 1, 1, math.pi, False, [])
        self.assertAlmostEqual(math.hypot(p.x, p.z), WALK_SPEED*.05)

    def test_walk_tracks_distance_and_stops_at_wall(self):
        p = Player(x=0,z=0,yaw=0)
        p.step(.05, 1, 0, 0, False, [])
        self.assertAlmostEqual(p.walk_phase,p.z/STRIDE_LENGTH)
        self.assertGreater(p.walk_weight, 0)
        for _ in range(80):
            p.step(.05, 1, 0, 0, False, [[-.5, 1, .5, 2]])
        stopped = p.walk_phase
        for _ in range(20):
            p.step(.05, 1, 0, 0, False, [[-.5, 1, .5, 2]])
        self.assertEqual(p.walk_phase, stopped)
        self.assertLess(p.walk_weight, .001)

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
        p = Player(x=0,z=0,yaw=0)
        for _ in range(50):
            p.step(.05, 1, 0, 0, False, [[-.5, 1, .5, 2]])
        self.assertGreater(p.z, .6)
        self.assertLessEqual(p.z, .76)

    def test_start_stop_and_turn_are_not_instantaneous(self):
        p = Player(x=0,z=0,yaw=0)
        p.step(.05,1,0,0,False,[])
        self.assertGreater(p.speed,0)
        self.assertLess(p.speed,WALK_SPEED)
        for _ in range(20):
            p.step(.05,1,0,0,False,[])
        before = p.z
        p.step(.05,0,0,0,False,[])
        self.assertGreater(p.z,before)
        self.assertLess(p.speed,WALK_SPEED)
        for _ in range(20):
            p.step(.05,0,0,0,False,[])
        self.assertEqual(p.speed,0)
        before = p.x,p.z
        p.step(.05,-1,0,0,False,[])
        self.assertEqual((p.x,p.z),before)
        self.assertLess(abs(p.yaw),.26)


if __name__ == '__main__':
    unittest.main()
