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
    "95db701a89083842f917418f7cf59f3d": {
        "output": [("single_lj_pyrite.gout", ".gout", None)]
    },
    "1f639518b936001e435bf032e2f764fe": {
        "output": [("optimize_lj_pyrite.gout", ".gout", None),
                   ("optimize_lj_pyrite.cif", ".cif", "output")]
    },
    "dc0eac053e11561ee13acea272345e20": {
        "output": [("optimize_lj_pyrite_symm.gout", ".gout", None),
                   ("optimize_lj_pyrite_symm.cif", ".cif", "output")]
    },
    "ec39b0c69c6ef97d2a701f86054702ee": {
        "stdout": None,
        "output": [("opt_reaxff_pyrite.gout", ".gout", None),
                   ("opt_reaxff_pyrite.cif", ".cif", "output")]},
    "57649b5ce90996cd71e233e2509068b7": {
        "stdout": None,
        "output": [("single_reaxff_pyrite.gout", ".gout", None)]},
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
    test_path = os.path.dirname(tests.__file__)
    # runcry17 requires input file name without extension as first arg
    input_name = sys_args[0]

    with open(input_name + ".gin", "rb") as f:
        content = f.read()
        # hashkey = hashlib.md5(content).digest()
        hashkey = hashlib.md5(content).hexdigest()

    if str(hashkey) not in hash_map:
        raise IOError(
            "contents of {0} not in hash list, hashkey: {1}".format(
                os.path.basename(input_name + ".gin"), str(hashkey)))

    outfiles = hash_map[hashkey]

    for inname, outext, outname in outfiles.get("output", []):
        src = os.path.join(test_path, "gulp_output_files", inname)
        if outname is None:
            dst = os.path.join(".", input_name + outext)
        else:
            dst = os.path.join(".", outname + outext)
        copyfile(src, dst)

    if outfiles.get("stdout", None) is None:
        sys.stdout.write(
            "running mock gulp for input arg: {}".format(input_name))
    else:
        outpath = os.path.join(
            test_path, "gulp_output_files", outfiles["stdout"])
        with open(outpath) as f:
            sys.stdout.write(f.read())


if __name__ == "__main__":
    main()
