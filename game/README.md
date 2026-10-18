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
The supplied source contains no walking clip; movement translates the idle model.
Building collision uses the Blender scene's `COL_` volumes. Small props, roofs,
stairs, and interiors are not a complete collision/navigation system. Camera rays
shorten the follow distance when a wall is behind the player.

## Real-time conversion

The exporter writes `game/assets/environment.glb`, `character.glb`, and
`scene.json`. Rerun it after changing source Blender scenes. The character retains
its sampled skeletal action and cigarette attachment. Fine beard geometry and
subdivision are omitted for performance. Procedural materials are reduced to
diffuse textures/colours with simple directional lighting. Exhaled smoke uses
lightweight raylib particles. Blender's volume fields, baked lighting, and full
material networks are not reproduced. The two metallic textures missing in the
original environment are not needed by the diffuse renderer.

Exported assets are included in the game branch so local play does not require
Blender. Source asset licenses and credits remain as described in ../CREDITS.md.

## Validation

```sh
.venv/bin/python -m unittest discover -s game -v
.venv/bin/python game/main.py --verify
```

`--verify` needs a working display. It loads the actual models and action, moves
the player, advances idle/smoking/idle states, checks that animated vertices
change, and writes five screenshots under ignored `game/captures/`. It exits
successfully only after those checks pass. A software OpenGL test was run with
`DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1` using a temporary Xorg dummy display.
