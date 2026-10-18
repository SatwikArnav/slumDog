# Shanti Nagar — raylib viewer

Third-person interactive viewer built with raylib 6's Python bindings. It uses
geometry, diffuse textures, and the rigged smoking animation exported directly
from the two repository Blender files. The original `.blend` files are untouched.

## Run

### Local launcher (Windows, macOS, Linux)

Install Python 3.10 or newer (tested with 3.12). The prepared `slumDog-local-preview.zip` package
includes the exported assets, so Blender is not required to play. Extract it
first, then:

- **Windows:** double-click `game/Play.bat` (Python must be available through
  the `py` launcher or on PATH).
- **macOS / Linux:** open a terminal in the extracted folder and run
  `python3 game/launch.py`.

The launcher creates `game/.runtime`, installs pinned raylib bindings, runs the
control tests, and opens the game. An Internet connection to PyPI is needed for
the first setup. Subsequent launches reuse the installed environment. Run
`python3 game/launch.py --setup-only` to install without opening a window.
The platform needs a compatible raylib wheel; errors from pip are shown directly.
Linux was tested here; macOS/Windows execution has not been verified.

Use the `codex/raylib-local-preview` GitHub branch to obtain the game and its
exported assets. The original `main` branch does not include the viewer.

### Development setup

From the repository root, using Python 3.12+ and Blender 4.3.2:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r game/requirements.txt
blender -b --python game/export_assets.py
.venv/bin/python game/main.py
```

The current workspace already has dependencies and exported assets. To launch it:

```sh
cd /workspace/slumDog
.venv/bin/python game/main.py
```

The game opens a native desktop window and needs an X11/Wayland desktop and OpenGL
3.3 support. It cannot be played inside the chat. A display-less shell needs a
virtual display for automated checks, not for interactive play.

## Controls

| Input | Action |
| --- | --- |
| W / A / S / D | Forward / left / backward / right, relative to camera |
| Mouse | Orbit the following camera |
| E | Play the smoking action once, then return to idle |
| Mouse wheel | Change camera distance |
| Tab | Release or capture the mouse |
| R | Reset player position |
| Escape | Exit |

Movement pauses while smoking. Additional E presses during the action are ignored.
Walking uses a generated skeletal IK cycle with alternating planted steps, foot
lift, pelvis motion, and opposing arm swings. Playback follows actual distance
travelled; pushing against a wall fades back to idle. Turning and animation
transitions are smoothed. This is a procedural authored walk, not motion capture.
Building collision uses the Blender scene's `COL_` volumes. Small props, roofs,
stairs, and interiors are not a complete collision/navigation system. Camera rays
shorten the follow distance when a wall is behind the player.

## Real-time conversion

The exporter writes `game/assets/environment.glb`, `character.glb`, `walk.glb`, and
`scene.json`. Rerun it after changing source Blender scenes. The character retains
its sampled skeletal action and cigarette attachment. Fine beard geometry and
subdivision are omitted for performance. Static Blender materials are baked into
UV texture atlases before export: the original plaster, ground-level weathering,
brick, timber, roofing, fabric, and lane networks are evaluated in their original
world coordinates, with a restrained amount of local ambient occlusion. Existing
image UVs and transparent staining decals are preserved. Atlas textures use
mipmaps and trilinear filtering, and the shader converts between sRGB textures
and linear lighting. Static geometry is batched by material to reduce draw calls.
`game/assets/surface_bakes.json` records the baked materials and resolutions.
Re-exporting requires Blender/Cycles CPU and takes longer than a plain GLB export.
The GLBs include these textures; playing still does not require Blender.

Lighting uses a simple directional shader; Blender's full lighting, general
material reflections, normal/bump networks and volume fields are not reproduced.
Puddles have a separate water shader with a live, half-resolution planar reflection
of the buildings and animated character. The mirrored camera clips away geometry
below the water plane to avoid reflecting the ground or the water itself. Fresnel
reflectivity, subtle animated ripple distortion, a sun highlight, shallow-water
tint, and feathered edges replace the old opaque dark patches. The reflection
buffer resizes with the window and adds one extra scene render per frame. Smoke
particles are not included in the reflection pass.

Smoke uses persistent, noise-textured
billboards with transparent edges, upward drift, air drag, expansion, and gradual
fading. Cigarette wisps follow the animated ember, and the exhale plume starts at
the animated mouth during exhalation. Particles continue dissipating after the
action ends; they are not a volumetric fluid simulation. The two metallic textures missing in the
original environment are not needed by the diffuse renderer.

Exported assets are included in the game branch so local play does not require
Blender. Source asset licenses and credits remain as described in ../CREDITS.md.

## Validation

```sh
.venv/bin/python -m unittest discover -s game -v
.venv/bin/python game/main.py --verify
```

`--verify` needs a working display. It loads the actual models and action, moves
the player, advances idle/walking/smoking/idle states, checks that animated vertices
change, and writes nine screenshots plus the reflection buffer under ignored
`game/captures/`. The last two captures inspect puddles from different angles and
exercise reflection-buffer resizing. It exits
successfully only after those checks pass. A software OpenGL test was run with
`DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1` using a temporary Xorg dummy display.

The unit suite checks that shop and lane surfaces retain both UVs and image
texture references, as well as actual leg/arm rotation tracks and loop closure in
the exported GLB, distance-driven walk timing, collisions, smoke emission timing,
particle drift/lifetime, texture edges, and attachment interpolation.
Water checks verify the camera mirror plane and the actual exported puddle height
and edge mask.
