#!/usr/bin/env python
"""This is a mock version of runcry17.

It compares an input file to a hash,
and writes an appropriate outputfile to STDOUT

to create a hashkey:

.. code-block:: python

    import hashlib
    input_path = 'path/to/input.d12'
    with open(input_path, "rb") as f:
        hashkey = hashlib.md5(f.read()).hexdigest()
    hashkey

"""
import hashlib
import io
import os
import sys

import six

from aiida_crystal17.tests import read_resource_binary, read_resource_text

# map of input file hashes to output files
hash_map = {
    'c1c5a85d0d799459f2e20fcb25bec0af': {
        'stdout': ('newk', 'mgo_sto3g_scf', 'main.out'),
        'output': ()
    },
    'a3744c045b5572e93157a16decd1dd24': {
        'stdout': ('doss', 'mgo_sto3g_scf', 'main.out'),
        'output': [[('doss', 'mgo_sto3g_scf', 'fort.25'), ('fort.25',)]]
    },
    '9b8e9a41b49014c1c91fc9142210c611': {
        'stdout': ('ech3', 'mgo_sto3g_scf', 'main.out'),
        'output': [[('ech3', 'mgo_sto3g_scf', 'DENS_CUBE.DAT'), ('DENS_CUBE.DAT',)]]
    }
}


def main(sys_args=None):
    """Run mock version of crystal17 properties binary executable."""
    if sys_args is None:
        sys_args = sys.argv[1:]

    if sys_args and sys_args[0] == '--test':
        # this used in the conda recipe, to test the executable is present
        return

    content = six.ensure_text(sys.stdin.read())
    hashkey = hashlib.md5(content.encode()).hexdigest()

    if str(hashkey) not in hash_map:
        raise IOError('contents from stdin not in hash list, hashkey: {0}\n{1}'.format(str(hashkey), content))

    outfiles = hash_map[hashkey]

    for inpath, outpath in outfiles.get('output', []):
        src = read_resource_binary(*inpath)
        with io.open(os.path.join('.', *outpath), 'wb') as handle:
            handle.write(src)

    if outfiles.get('stdout', None) is not None:
        sys.stdout.write(read_resource_text(*outfiles['stdout']))


if __name__ == '__main__':
    main()
