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
import os
import sys
from shutil import copyfile

import six

import aiida_crystal17.tests as tests

# map of input file hashes to output files
hash_map = {
    "14b7194e25eb366328198908b3bcf840": {
        "stdout": ("single_lj_pyrite", "main.gout"),
        "output": ()
    },
    "e2b297d73de5174741c94d52432e7b79": {
        "stdout": ("optimize_lj_pyrite", "main.gout"),
        "output": [(("optimize_lj_pyrite", "output.cif"), ("output.cif",))]
    },
    "6f373e02f3245c3b989f468c524a0d9d": {
        "stdout": ("optimize_lj_pyrite_symm", "main.gout"),
        "output": [(("optimize_lj_pyrite_symm", "output.cif"), ("output.cif",))]
    },
    "f104b6cc996c97be76b3ee31761b7898": {
        "stdout": ("single_reaxff_pyrite", "main.gout"),
        "output": ()
    },
    "5dc8cb9621091a1a029b8149b0e02e33": {
        "stdout": ("optimize_reaxff_pyrite", "main.gout"),
        "output": [(("optimize_reaxff_pyrite", "output.cif"), ("output.cif",))]
    },
    "99595ec1cba6fb909a1de2377e21d82a": {
        "stdout": ("optimize_reaxff_pyrite_symm", "main.gout"),
        "output": [(("optimize_reaxff_pyrite_symm", "output.cif"), ("output.cif",))],
        "stderr": ("optimize_reaxff_pyrite_symm", "main_stderr.txt")
    },
    "1f77dad9265e394d88b58cd909f34f18": {
        "stdout": ("fit_lj_fes", "main.gout"),
        "output": [(("fit_lj_fes", "fitting.grs"), ("fitting.grs",))]
    },
    "bbfcc242e70205e5d418001dea5e3d63": {
        "stdout": ("fit_reaxff_fes", "main.gout"),
        "output": [(("fit_reaxff_fes", "fitting.grs"), ("fitting.grs",))]
    }
}


def main(sys_args=None):

    if sys_args is None:
        sys_args = sys.argv[1:]

    if sys_args and sys_args[0] == "--test":
        # this used in the conda recipe, to test the executable is present
        return

    test_path = os.path.join(tests.TEST_FILES, "gulp")

    content = six.ensure_text(sys.stdin.read())
    hashkey = hashlib.md5(content.encode()).hexdigest()

    if str(hashkey) not in hash_map:
        raise IOError(
            "contents from stdin not in hash list, hashkey: {0}\n{1}".format(
                str(hashkey), content))

    outfiles = hash_map[hashkey]

    for inpath, outpath in outfiles.get("output", []):
        src = os.path.join(test_path, *inpath)
        dst = os.path.join(".", *outpath)
        copyfile(src, dst)

    if outfiles.get("stdout", None) is not None:
        outpath = os.path.join(test_path, *outfiles["stdout"])
        with open(outpath) as f:
            sys.stdout.write(f.read())

    if outfiles.get("stderr", None) is not None:
        outpath = os.path.join(test_path, *outfiles["stderr"])
        with open(outpath) as f:
            sys.stderr.write(f.read())


if __name__ == "__main__":
    main()
