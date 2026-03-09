"""Build script for BigBadAbler using PyInstaller."""

import subprocess
import sys


def build():
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name', 'BigBadAbler',
        '--onedir',
        '--windowed',

        # Bundle asset directories
        '--add-data', 'soundFX;soundFX',
        '--add-data', 'art;art',

        # Hidden imports for dynamic/deferred imports
        '--hidden-import', 'content',
        '--hidden-import', 'content.augments',
        '--hidden-import', 'content.items',
        '--hidden-import', 'content.unit_registry',
        '--hidden-import', 'content.units',
        '--hidden-import', 'content.units.assassin',
        '--hidden-import', 'content.units.berserker',
        '--hidden-import', 'content.units.cleric',
        '--hidden-import', 'content.units.dragon',
        '--hidden-import', 'content.units.magic_knight',
        '--hidden-import', 'content.units.necromancer',
        '--hidden-import', 'content.units.ogre_shaman',
        '--hidden-import', 'content.units.paladin',
        '--hidden-import', 'content.units.pyromancer',
        '--hidden-import', 'content.units.slime',
        '--hidden-import', 'content.units.wizard',
        '--hidden-import', 'content.units.yeti',
        '--hidden-import', 'augment',
        '--hidden-import', 'paths',

        # Exclude unused heavy packages
        '--exclude-module', 'numpy',

        # Overwrite previous build without prompting
        '--noconfirm',

        # Entry point
        'main.py',
    ]

    print('Running PyInstaller...')
    print(' '.join(cmd))
    result = subprocess.run(cmd)
    if result.returncode == 0:
        print('\nBuild successful! Output is in dist/BigBadAbler/')
        print('Zip that folder to distribute to playtesters.')
    else:
        print(f'\nBuild failed with return code {result.returncode}')
    sys.exit(result.returncode)


if __name__ == '__main__':
    build()
