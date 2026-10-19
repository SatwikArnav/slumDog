"""Check that expanded shop interiors are genuinely reachable and enclosed."""
import json,math,unittest
from pathlib import Path
from state import Player

class ShopLayouts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=json.loads((Path(__file__).parent/'assets/scene.json').read_text())

    def test_five_distinct_full_depth_interiors(self):
        shops=self.config['shops']
        self.assertEqual({s['kind'] for s in shops},{'grocer','tailor','tea','cycle','electrical'})
        for shop in shops:
            self.assertGreater(shop['depth'],3.3)
            self.assertGreater(shop['width']*shop['depth'],10)

    def test_walk_from_street_to_back_of_each_shop(self):
        obstacles=self.config['collision']
        for s in self.config['shops']:
            p=Player(x=s['front']-s['side']*.70,z=-s['center_y'],yaw=s['side']*math.pi/2)
            # End in the aisle in front of the repair workbench, allowing the
            # player's 24cm collision radius; do not demand walking into it.
            target=s['front']+s['side']*(s['depth']-1.3)
            self.assertFalse(p.blocked(p.x,p.z,obstacles),s['name']+' entrance blocked')
            for _ in range(160):
                if (target-p.x)*s['side']<=.05:break
                p.step(.025,1,0,s['side']*math.pi/2,False,obstacles)
            self.assertLess(abs(p.x-target),.10,s['name']+' interior unreachable')
            self.assertFalse(p.blocked(p.x,p.z,obstacles),s['name'])

    def test_outer_walls_and_back_counter_remain_solid(self):
        p=Player()
        for s in self.config['shops']:
            x=s['front']+s['side']*1.5
            for edge in (-1,1):
                self.assertTrue(p.blocked(x,-s['center_y']+edge*(s['width']/2+.10),self.config['collision']),s['name'])
            self.assertTrue(p.blocked(s['front']+s['side']*(s['depth']+.10),-s['center_y'],self.config['collision']),s['name'])

if __name__=='__main__':unittest.main()
