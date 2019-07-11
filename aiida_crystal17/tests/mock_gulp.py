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

import aiida_crystal17.tests as tests

# map of input file hashes to output files
hash_map = {
    "83e3c1e78aab9588bc5039588645cb4d": {
        "output": [(("single_lj_pyrite", "main.gout"), "{inname}.gout")]
    },
    "99ff0a023f71744e5f0e2dbfd38b382c": {
        "output": [(("optimize_lj_pyrite", "main.gout"), "{inname}.gout"),
                   (("optimize_lj_pyrite", "output.cif"), "output.cif")]
    },
    "efa125cda73b3a42ac1d3641e619e860": {
        "output": [(("optimize_lj_pyrite_symm", "main.gout"), "{inname}.gout"),
                   (("optimize_lj_pyrite_symm", "output.cif"), "output.cif")]
    },
    "7ca8e6e9a6f544e43f0aaf45e65e54df": {
        "stdout": None,
        "output": [(("single_reaxff_pyrite", "main.gout"), "{inname}.gout")]},
    "3b662a2567df952cee2bdf09fc4197c4": {
        "stdout": None,
        "output": [(("optimize_reaxff_pyrite", "main.gout"), "{inname}.gout"),
                   (("optimize_reaxff_pyrite", "output.cif"), "output.cif")]},
    "fdc074fd4e053802ae44e841389ceceb": {
        "output": [(("optimize_reaxff_pyrite_symm", "main.gout"), "{inname}.gout"),
                   (("optimize_reaxff_pyrite_symm", "output.cif"), "output.cif")]
    }
}


def main(sys_args=None):

    if sys_args is None:
        sys_args = sys.argv[1:]

    if len(sys_args) < 1:
        raise ValueError("no input name given (as 1st argument)")

    if sys_args[0] == "--test":
        # this used in the conda recipe, to test the executable is present
        return

    # script_path = os.path.dirname(os.path.realpath(__file__))
    test_path = os.path.join(os.path.dirname(tests.__file__), "raw_files", "gulp")
    # runcry17 requires input file name without extension as first arg
    input_name = sys_args[0]

    with open(input_name + ".gin", "rb") as f:
        content = f.read()
        # hashkey = hashlib.md5(content).digest()
        hashkey = hashlib.md5(content).hexdigest()

    if str(hashkey) not in hash_map:
        raise IOError(
            "contents of {0} not in hash list, hashkey: {1}\n{2}".format(
                os.path.basename(input_name + ".gin"), str(hashkey), content))

    outfiles = hash_map[hashkey]

    for opath, dest_file in outfiles.get("output", []):
        src = os.path.join(test_path, *opath)
        dst = os.path.join(".", dest_file.format(inname=input_name))
        copyfile(src, dst)

    if outfiles.get("stdout", None) is None:
        sys.stdout.write(
            "running mock gulp for input arg: {}".format(input_name))
    else:
        outpath = os.path.join(
            test_path, *outfiles["stdout"])
        with open(outpath) as f:
            sys.stdout.write(f.read())


if __name__ == "__main__":
    main()
