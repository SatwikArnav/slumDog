"""Inspect exported skeletal tracks so static-leg exports cannot pass unnoticed."""
import json
from pathlib import Path
import struct
import unittest


class ExportChecks(unittest.TestCase):
    def test_walk_has_looping_leg_and_arm_animation(self):
        path = Path(__file__).parent / 'assets/walk.glb'
        with path.open('rb') as f:
            magic, version, _ = struct.unpack('<III', f.read(12))
            self.assertEqual((magic,version),(0x46546c67,2))
            length, _ = struct.unpack('<II', f.read(8))
            gltf = json.loads(f.read(length))
            length, _ = struct.unpack('<II', f.read(8))
            binary = f.read(length)
        tracks = {}
        for animation in gltf['animations']:
            for channel in animation['channels']:
                if channel['target']['path'] != 'rotation':
                    continue
                name = gltf['nodes'][channel['target']['node']]['name']
                accessor = gltf['accessors'][animation['samplers'][channel['sampler']]['output']]
                view = gltf['bufferViews'][accessor['bufferView']]
                start = view.get('byteOffset',0)+accessor.get('byteOffset',0)
                tracks[name] = [struct.unpack_from('<4f',binary,start+i*view.get('byteStride',16))
                                for i in range(accessor['count'])]
        for bone in ['upperleg01.L','upperleg01.R','lowerleg01.L','lowerleg01.R',
                     'upperarm01.L','upperarm01.R']:
            values = tracks[bone]
            changes = [sum((x-y)**2 for x,y in zip(v,values[0])) for v in values]
            self.assertGreater(max(changes),.001,bone+' is static')
            self.assertLess(sum((x-y)**2 for x,y in zip(values[0],values[-1])),.00001,
                            bone+' has a discontinuous loop')


if __name__ == '__main__':
    unittest.main()
