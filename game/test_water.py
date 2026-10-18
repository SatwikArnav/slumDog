import json
from pathlib import Path
import struct
import unittest
from water import HEIGHT, reflect_point


class WaterChecks(unittest.TestCase):
    def test_camera_reflection_across_water_plane(self):
        eye = (2.,1.7,-3.)
        mirrored = reflect_point(eye)
        self.assertAlmostEqual(eye[1]-HEIGHT,HEIGHT-mirrored[1])
        self.assertEqual(reflect_point(mirrored),eye)
        self.assertEqual(reflect_point((1,HEIGHT,2)),(1,HEIGHT,2))

    def test_puddle_surface_retains_height_and_feather_mask(self):
        with (Path(__file__).parent/'assets/environment.glb').open('rb') as f:
            f.read(12)
            length,_ = struct.unpack('<II',f.read(8))
            gltf = json.loads(f.read(length))
            length,_ = struct.unpack('<II',f.read(8))
            binary = f.read(length)
        def read(index,components):
            accessor = gltf['accessors'][index]
            view = gltf['bufferViews'][accessor['bufferView']]
            offset = view.get('byteOffset',0)+accessor.get('byteOffset',0)
            return [struct.unpack_from('<'+'f'*components,binary,offset+i*view.get('byteStride',components*4))
                    for i in range(accessor['count'])]
        count = 0
        for mesh in gltf['meshes']:
            for primitive in mesh['primitives']:
                name = gltf['materials'][primitive['material']]['name']
                if name.startswith('Dark shallow puddles'):
                    count += 1
                    positions = read(primitive['attributes']['POSITION'],3)
                    self.assertTrue(all(abs(p[1]-HEIGHT)<.00001 for p in positions))
                    mask = [uv[0] for uv in read(primitive['attributes']['TEXCOORD_0'],2)]
                    self.assertEqual(set(mask),{0.,1.},'Puddle edge feathering was lost during export')
        self.assertGreater(count,0)


if __name__ == '__main__':
    unittest.main()
