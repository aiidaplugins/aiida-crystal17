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

import six

import aiida_crystal17.tests as tests

# map of input file hashes to output files
hash_map = {
    "f6090e9f0da6098e612cd26cb2f11620": {
        "output": (),
        "stdout": ("mgo_sto3g_scf", "main.out")},
    "4bfb50cb82980b82aabc6eb00e17f62c": {
        "output": (),
        "stdout": ("mgo_sto3g_scf_external", "main.out")},
    "ff77b996a5081e64ab2e9970c6cd15cb": {
        "output": (),
        "stdout": ("mgo_sto3g_scf_external", 'main.out')},
    "a7bfd39835be4b6730b0df448f5f6a79": {
        "output": (),
        "stdout": ("mgo_sto3g_opt", "main.out")},
    "5d14a77cb27ee21ad5d151ff3769c094": {
        "output": (),
        "stdout": ("nio_sto3g_afm_scf", 'main.out')},
    "2eae63d662d8518376a208892be07b1d": {
        "output": (),
        "stdout": ("nio_sto3g_afm_opt", 'main.out')},
}


def main(sys_args=None):

    if sys_args is None:
        sys_args = sys.argv[1:]

    if sys_args and sys_args[0] == "--test":
        # this used in the conda recipe, to test the executable is present
        return

    test_path = os.path.join(tests.TEST_FILES, "crystal")

    content = six.ensure_text(sys.stdin.read())
    hashkey = hashlib.md5(content.encode()).hexdigest()

    if str(hashkey) not in hash_map:
        raise IOError(
            "contents from stdin not in hash list, hashkey: {0}\n{1}".format(
                str(hashkey), content))

    outfiles = hash_map[hashkey]

    for inname, outname in outfiles.get("output", []):
        src = os.path.join(test_path, *inname)
        dst = os.path.join(".", outname)
        copyfile(src, dst)

    if outfiles.get("stdout", None) is not None:
        outpath = os.path.join(test_path, *outfiles["stdout"])
        with open(outpath) as f:
            sys.stdout.write(f.read())


if __name__ == "__main__":
    main()
