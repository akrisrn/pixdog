import sys
from PyInstaller.__main__ import run

bit = "x32"
if sys.maxsize > (2 ** 31 - 1):
    bit = "x64"

opts = ['start.py',
        '-F','-y',
        '--clean',
        '--specpath=spec',
        '--name=pixdog-' + bit,
        '--icon=pixdog.ico'
        ]
run(opts)
