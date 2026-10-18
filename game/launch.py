"""Create a local virtual environment, prepare assets if needed, and run the game."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv

HERE = Path(__file__).resolve().parent


def run(command):
    print('+', ' '.join(map(str, command)), flush=True)
    subprocess.run(list(map(str, command)), cwd=HERE.parent, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--setup-only', action='store_true')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if sys.version_info < (3, 10):
        parser.error('Install Python 3.10 or newer, then run this launcher again.')
    runtime = HERE / '.runtime'
    python = runtime / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not python.is_file():
        print('Preparing an isolated Python environment...', flush=True)
        venv.EnvBuilder(with_pip=True).create(runtime)
    requirements = HERE / 'requirements.txt'
    marker = runtime / 'installed-requirements.txt'
    expected = requirements.read_text()
    if not marker.is_file() or marker.read_text() != expected:
        run([python, '-m', 'pip', 'install', '-r', requirements])
        marker.write_text(expected)
    missing = [name for name in ('environment.glb', 'character.glb', 'walk.glb', 'scene.json')
               if not (HERE / 'assets' / name).is_file()]
    if missing:
        blender = shutil.which('blender')
        if not blender:
            parser.error('Exported assets are missing. Install Blender 4.3.2 and add blender to PATH, '
                         'or use the prepared local-preview package, which includes the assets.')
        run([blender, '-b', '--python-exit-code', '1', '--python', HERE / 'export_assets.py'])
    run([python, '-m', 'unittest', 'discover', '-s', HERE, '-v'])
    if args.setup_only:
        print('Local setup complete. Run this launcher again to play.')
        return
    run([python, HERE / 'main.py', *(['--verify'] if args.verify else [])])


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as error:
        print(f'Setup or game exited with code {error.returncode}. See the error above.', file=sys.stderr)
        sys.exit(error.returncode)
