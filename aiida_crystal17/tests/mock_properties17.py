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
    "7231636fb32fa896709483defc8841fb": {
        "stdout": ("mgo_sto3g_scf", "doss_total_only.out"),
        "output": [[("mgo_sto3g_scf", "doss_total_only.f25"), "fort.25"]]},
    "c1c5a85d0d799459f2e20fcb25bec0af": {
        "stdout": ("mgo_sto3g_scf", "fermi_only.out"),
        "output": ()},
}


def main(sys_args=None):

    if sys_args is None:
        sys_args = sys.argv[1:]

    if sys_args and sys_args[0] == "--test":
        # this used in the conda recipe, to test the executable is present
        return

    test_path = os.path.join(tests.TEST_FILES, "doss")

    content = six.ensure_text(sys.stdin.read())
    hashkey = hashlib.md5(content.encode()).hexdigest()

    if str(hashkey) not in hash_map:
        raise IOError(
            "contents from stdin not in hash list, hashkey: {1}\n{2}".format(
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
