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
    "83e3c1e78aab9588bc5039588645cb4d": {
        "stdout": ("single_lj_pyrite", "main.gout"),
        "output": ()
    },
    "99ff0a023f71744e5f0e2dbfd38b382c": {
        "stdout": ("optimize_lj_pyrite", "main.gout"),
        "output": [(("optimize_lj_pyrite", "output.cif"), ("output.cif",))]
    },
    "efa125cda73b3a42ac1d3641e619e860": {
        "stdout": ("optimize_lj_pyrite_symm", "main.gout"),
        "output": [(("optimize_lj_pyrite_symm", "output.cif"), ("output.cif",))]
    },
    "7ca8e6e9a6f544e43f0aaf45e65e54df": {
        "stdout": ("single_reaxff_pyrite", "main.gout"),
        "output": ()
    },
    "3b662a2567df952cee2bdf09fc4197c4": {
        "stdout": ("optimize_reaxff_pyrite", "main.gout"),
        "output": [(("optimize_reaxff_pyrite", "output.cif"), ("output.cif",))]
    },
    "fdc074fd4e053802ae44e841389ceceb": {
        "stdout": ("optimize_reaxff_pyrite_symm", "main.gout"),
        "output": [(("optimize_reaxff_pyrite_symm", "output.cif"), ("output.cif",))],
        "stderr": ("optimize_reaxff_pyrite_symm", "main_stderr.txt")
    },
    "03ae4d9f97ca466ac92c223892672b0f": {
        "stdout": ("fit_lj_fes", "main.gout"),
        "output": [(("fit_lj_fes", "fitting.grs"), ("fitting.grs",))]
    },
    "f5b53088f258b6521db4741dc5cded30": {
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
