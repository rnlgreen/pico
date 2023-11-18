"""
Returns micropython version
I don't use this anywhere in my code though

To run, from rshell/repl just use "import version"

Output:
mpy version: 6
mpy sub-version: 1
mpy flags: -march=armv6m
"""
import sys
sys_mpy = sys.implementation._mpy
arch = [None, 'x86', 'x64',
    'armv6', 'armv6m', 'armv7m', 'armv7em', 'armv7emsp', 'armv7emdp',
    'xtensa', 'xtensawin'][sys_mpy >> 10]
print('mpy version:', sys_mpy & 0xff)
print('mpy sub-version:', sys_mpy >> 8 & 3)
print('mpy flags:', end='')
if arch:
    print(' -march=' + arch, end='')
print()