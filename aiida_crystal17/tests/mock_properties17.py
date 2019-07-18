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
    "a3744c045b5572e93157a16decd1dd24": {
        "stdout": ("doss", "mgo_sto3g_scf", "main.out"),
        "output": [[("doss", "mgo_sto3g_scf", "fort.25"), "fort.25"]]},
    "c1c5a85d0d799459f2e20fcb25bec0af": {
        "stdout": ("fermi", "mgo_sto3g_scf", "main.out"),
        "output": ()},
}


def main(sys_args=None):

    if sys_args is None:
        sys_args = sys.argv[1:]

    if sys_args and sys_args[0] == "--test":
        # this used in the conda recipe, to test the executable is present
        return

    test_path = tests.TEST_FILES

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
