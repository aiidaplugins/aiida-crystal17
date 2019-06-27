#!/usr/bin/env python
"""
this is a mock version of runcry17,
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
    "f6090e9f0da6098e612cd26cb2f11620": {
        "stdout": None,
        "output": [("mgo_sto3g_scf.crystal.out", ".out")]},
    "4bfb50cb82980b82aabc6eb00e17f62c": {
        "stdout": None,
        "output": [("mgo_sto3g_external.crystal.out", ".out")]},
    "ff77b996a5081e64ab2e9970c6cd15cb": {
        "stdout": None,
        "output": [('mgo_sto3g_external.crystal.out', ".out")]},
    "a7bfd39835be4b6730b0df448f5f6a79": {
        "stdout": None,
        "output": [("mgo_sto3g_opt.crystal.out", ".out")]},
    "5d14a77cb27ee21ad5d151ff3769c094": {
        "stdout": None,
        "output": [('nio_sto3g_afm.crystal.out', ".out")]},
    "2eae63d662d8518376a208892be07b1d": {
        "stdout": None,
        "output": [('nio_sto3g_afm_opt.crystal.out', ".out")]},
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
    test_path = os.path.join(os.path.dirname(tests.__file__), "raw_files", "crystal")
    # runcry17 requires input file name without extension as first arg
    input_name = sys_args[0]

    with open(input_name + ".d12", "rb") as f:
        content = f.read()
        # hashkey = hashlib.md5(content).digest()
        hashkey = hashlib.md5(content).hexdigest()

    if str(hashkey) not in hash_map:
        raise IOError(
            "contents of {0} not in hash list, hashkey: {1}\n{2}".format(
                os.path.basename(input_name + ".d12"), str(hashkey), content))

    outfiles = hash_map[hashkey]

    for inname, outext in outfiles.get("output", []):
        src = os.path.join(test_path, "out", inname)
        dst = os.path.join(".", input_name + outext)
        copyfile(src, dst)

    if outfiles.get("stdout", None) is None:
        sys.stdout.write(
            "running mock runcry17 for input arg: {}".format(input_name))
    else:
        outpath = os.path.join(test_path, "out", outfiles["stdout"])
        with open(outpath) as f:
            sys.stdout.write(f.read())


if __name__ == "__main__":
    main()
