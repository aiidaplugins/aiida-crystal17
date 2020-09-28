#!/usr/bin/env python
"""This is a mock version of runcry17.

It compares an input file to a hash,
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



from aiida_crystal17.tests import read_resource_binary, read_resource_text

# map of input file hashes (and optional fort.34 hashes) to output files
hash_map = {
    'f6090e9f0da6098e612cd26cb2f11620': {
        None: {
            'output': (),
            'stdout': ('mgo_sto3g_scf', 'main.out')
        }
    },
    'ee3e7aa100e0ffcd8c23ac626c54c538': {
        None: {
            'output': [(('mgo_sto3g_scf_external', 'mock_fort.9'), ('fort.9',))],
            'stdout': ('mgo_sto3g_scf_external', 'main.out')
        }
    },
    'ee712942682b1e4fa73a6c8456dd6fda': {
        None: {
            'output': [(('mgo_sto3g_scf_external', 'mock_fort.9'), ('fort.9',))],
            'stdout': ('mgo_sto3g_scf_external', 'main.out')
        }
    },
    # TODO I think the above two are the same just with minor differences (and 4bfb50cb82980b82aabc6eb00e17f62c)
    'ff77b996a5081e64ab2e9970c6cd15cb': {
        None: {
            'output': [(('mgo_sto3g_scf_external', 'mock_fort.9'), ('fort.9',))],
            'stdout': ('mgo_sto3g_scf_external', 'main.out')
        }
    },
    'a7bfd39835be4b6730b0df448f5f6a79': {
        None: {
            'output': (),
            'stdout': ('mgo_sto3g_opt', 'main.out')
        }
    },
    '5d14a77cb27ee21ad5d151ff3769c094': {
        None: {
            'output': (),
            'stdout': ('nio_sto3g_afm_scf', 'main.out')
        }
    },
    '2eae63d662d8518376a208892be07b1d': {
        None: {
            'output': (),
            'stdout': ('nio_sto3g_afm_opt', 'main.out')
        }
    },
    '6e68e432a1b852bb82d1d09af40b23ab': {
        '1f92bb67c0d8398e2de23b58b2fec766': {
            'output': [(('nio_sto3g_afm_opt_walltime', 'optc{:03}'.format(n + 1)),
                        ('optc{:03}'.format(n + 1),)) for n in range(18) if n not in (6, 10)] +
                      [(('nio_sto3g_afm_opt_walltime', 'HESSOPT.DAT'), ('HESSOPT.DAT',)),
                       (('nio_sto3g_afm_opt_walltime', '_scheduler-stderr.txt'), ('_scheduler-stderr.txt',))],
            'stdout': ('nio_sto3g_afm_opt_walltime', 'main.out')
        },
        '580bba20ba3e73342ddeb05d26e96164': {
            'output': (),
            'stdout': ('nio_sto3g_afm_opt_walltime2', 'main.out')
        }
    },
    '549d584022bc77572cebf56cd9cccb3e': {
        None: {
            'output': [(('nio_sto3g_afm_scf_maxcyc', 'fort.9'), ('fort.9',))],
            'stdout': ('nio_sto3g_afm_scf_maxcyc', 'main.out')
        }
    },
    '580e34966940b27f707d24e51ce659ed': {
        None: {
            'output': (),
            'stdout': ('nio_sto3g_afm_scf_maxcyc2', 'main.out')
        }
    }
}


def main(sys_args=None):
    """Run mock version of crystal17 binary executable."""
    if sys_args is None:
        sys_args = sys.argv[1:]

    if sys_args and sys_args[0] == '--test':
        # this used in the conda recipe, to test the executable is present
        return

    content = sys.stdin.read()
    hashkey = hashlib.md5(content.encode()).hexdigest()

    if str(hashkey) not in hash_map:
        raise IOError('contents from stdin not in hash list, hashkey: {0}\n{1}'.format(str(hashkey), content))

    if None in hash_map[hashkey]:
        outfiles = hash_map[hashkey][None]
    else:
        gui_path = os.path.join(os.getcwd(), 'fort.34')
        with open(gui_path) as handle:
            content = handle.read()
        gui_hashkey = hashlib.md5(content.encode()).hexdigest()
        if str(gui_hashkey) not in hash_map[hashkey]:
            raise IOError('contents from fort.34 not in hash list, hashkey: {0}'.format(str(gui_hashkey)))
        outfiles = hash_map[hashkey][gui_hashkey]

    for inpath, outpath in outfiles.get('output', []):
        src = read_resource_binary('crystal', *inpath)
        with io.open(os.path.join('.', *outpath), 'wb') as handle:
            handle.write(src)

    if outfiles.get('stdout', None) is not None:
        sys.stdout.write(read_resource_text('crystal', *outfiles['stdout']))


if __name__ == '__main__':
    main()
