#!/usr/bin/env python
"""
this is a mock version of gulp (v4.5.3),
which compares an input file to a hash,
and writes an appropriate outputfile to stdoout

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
    '14b7194e25eb366328198908b3bcf840': {
        'stdout': ('single_lj_pyrite', 'main.gout'),
        'output': ()
    },
    'e2b297d73de5174741c94d52432e7b79': {
        'stdout': ('optimize_lj_pyrite', 'main.gout'),
        'output': [(('optimize_lj_pyrite', 'output.cif'), ('output.cif',))]
    },
    '6f373e02f3245c3b989f468c524a0d9d': {
        'stdout': ('optimize_lj_pyrite_symm', 'main.gout'),
        'output': [(('optimize_lj_pyrite_symm', 'output.cif'), ('output.cif',))]
    },
    # '83f4e528d0824eea430572fdda0b4f58': {  # angleprod 0.001 -> 0.00001
    'e7d3542e07249b47722baa39e4f9cd83': {
        'stdout': ('single_reaxff_pyrite', 'main.gout'),
        'output': ()
    },
    # '16f5c23e5c4072a25b7ed33a68744227': {  # angleprod 0.001 -> 0.00001
    '4889d8c7fb16c64e5cd33df557323194': {
        'stdout': ('optimize_reaxff_pyrite', 'main.gout'),
        'output': [(('optimize_reaxff_pyrite', 'output.cif'), ('output.cif',))]
    },
    # '59ea35116463a60fb1ffe055d95f1542': {  # angleprod 0.001 -> 0.00001
    '55fab27ab4cbfece6a7e8ca61c8005fe': {
        'stdout': ('optimize_reaxff_pyrite_symm', 'main.gout'),
        'output': [(('optimize_reaxff_pyrite_symm', 'output.cif'), ('output.cif',))],
        'stderr': ('optimize_reaxff_pyrite_symm', 'main_stderr.txt')
    },
    '1f77dad9265e394d88b58cd909f34f18': {
        'stdout': ('fit_lj_fes', 'main.gout'),
        'output': [(('fit_lj_fes', 'fitting.grs'), ('fitting.grs',))]
    },
    # 'bbfcc242e70205e5d418001dea5e3d63': {  # angleprod 0.001 -> 0.00001
    'ca3b8d79a5ccb44cb74f646ae2018899': {
        'stdout': ('fit_reaxff_fes', 'main.gout'),
        'output': [(('fit_reaxff_fes', 'fitting.grs'), ('fitting.grs',))]
    }
}


def main(sys_args=None):
    """Run mock version of gulp binary executable."""
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
        src = read_resource_binary('gulp', *inpath)
        with io.open(os.path.join('.', *outpath), 'wb') as handle:
            handle.write(src)

    if outfiles.get('stdout', None) is not None:
        sys.stdout.write(read_resource_text('gulp', *outfiles['stdout']))

    if outfiles.get('stderr', None) is not None:
        sys.stderr.write(read_resource_text('gulp', *outfiles['stderr']))


if __name__ == '__main__':
    main()
