import json
import math
from pathlib import Path
import struct
import unittest
import wave
from dog_ai import StreetDog,blocked

ASSETS = Path(__file__).parent/'assets'


class StreetDogChecks(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ASSETS/'scene.json').read_text())

    def test_roams_without_entering_obstacles_or_player(self):
        dog = StreetDog(self.config['dog_obstacles'])
        start = dog.x,dog.z
        distance = 0
        seen,barks = set(),[]
        for i in range(2400):
            previous = dog.x,dog.z
            event = dog.update(.025,(-.7,3.2))
            moved = math.dist(previous,(dog.x,dog.z))
            self.assertLessEqual(moved,.65*.025+.000001)
            self.assertFalse(blocked(dog.x,dog.z,dog.nav.obstacles,.16))
            self.assertGreater(math.dist((dog.x,dog.z),(-.7,3.2)),.55)
            distance += moved
            seen.add(dog.mode)
            if event:
                barks.append(i*.025)
        self.assertGreater(distance,4)
        self.assertTrue({'roam','bark','idle','sniff'}.issubset(seen))
        self.assertGreaterEqual(len(barks),2)
        self.assertTrue(all(b-a>=8.9 for a,b in zip(barks,barks[1:])))

    def test_building_transforms_and_path_planning(self):
        self.assertGreater(len({tuple(v) for v in self.config['collision']}),5)
        dog = StreetDog(self.config['dog_obstacles'])
        start = dog.nav.nearest((dog.x,dog.z))
        goal = dog.nav.nearest((0,-10))
        path = dog.nav.path(start,goal)
        self.assertGreater(len(path),10)
        self.assertTrue(all(not blocked(x,z,dog.nav.obstacles,.28) for x,z in path))

    def test_bark_wav_has_two_audible_pulses(self):
        with wave.open(str(ASSETS/'dog-bark.wav'),'rb') as f:
            self.assertEqual((f.getnchannels(),f.getsampwidth(),f.getframerate()),(1,2,24000))
            data = struct.unpack('<'+'h'*f.getnframes(),f.readframes(f.getnframes()))
        self.assertEqual(len(data),18000)
        for a,b in ((.07,.20),(.31,.44)):
            values = data[int(a*24000):int(b*24000)]
            self.assertGreater(math.sqrt(sum(v*v for v in values)/len(values)),1000)
        self.assertTrue(all(v==0 for v in data[:1000]))

    def test_dog_assets_have_matching_skins_and_animated_clips(self):
        counts = []
        for name in ('dog.glb','dog_walk.glb','dog_bark.glb'):
            with (ASSETS/name).open('rb') as f:
                f.read(12)
                size,_ = struct.unpack('<II',f.read(8))
                gltf = json.loads(f.read(size))
                size,_ = struct.unpack('<II',f.read(8))
                binary = f.read(size)
            self.assertGreater(len(gltf['meshes']),3)
            coat = next(m for m in gltf['materials'] if m['name']=='Short fawn coat with white bib')
            texture = gltf['textures'][coat['pbrMetallicRoughness']['baseColorTexture']['index']]
            self.assertIn('bufferView',gltf['images'][texture['source']], 'Coat must ship inside the GLB')
            self.assertEqual(len(gltf['animations']),1)
            counts.append(len(gltf['skins'][0]['joints']))
            targets = {gltf['nodes'][c['target']['node']]['name'] for c in gltf['animations'][0]['channels']}
            self.assertIn('jaw' if 'bark' in name else 'FL_lower',targets)
            bone = 'jaw' if 'bark' in name else 'FL_upper' if 'walk' in name else 'head'
            for channel in gltf['animations'][0]['channels']:
                if (gltf['nodes'][channel['target']['node']]['name']==bone
                    and channel['target']['path']=='rotation'):
                    animation = gltf['animations'][0]
                    accessor = gltf['accessors'][animation['samplers'][channel['sampler']]['output']]
                    view = gltf['bufferViews'][accessor['bufferView']]
                    offset = view.get('byteOffset',0)+accessor.get('byteOffset',0)
                    values = [struct.unpack_from('<4f',binary,offset+i*view.get('byteStride',16))
                              for i in range(accessor['count'])]
                    self.assertGreater(max(math.dist(v,values[0]) for v in values),.03,bone+' did not animate')
                    self.assertLess(math.dist(values[0],values[-1]),.001,bone+' has a loop discontinuity')
        self.assertEqual(len(set(counts)),1)


if __name__=='__main__':
    unittest.main()
