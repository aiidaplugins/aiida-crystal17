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
    "7231636fb32fa896709483defc8841fb": {
        "output": [[("mgo_sto3g_scf", "doss_total_only.f25"), ".f25"]]},
    "c1c5a85d0d799459f2e20fcb25bec0af": {
        "output": [[("mgo_sto3g_scf", "fermi_only.outp"), ".out"]]},
}


def main(sys_args=None):

    if sys_args is None:
        sys_args = sys.argv[1:]

    if len(sys_args) < 2:
        raise ValueError("input should have 2 arguments: infilename wfname")

    if sys_args[0] == "--test":
        # this used in the conda recipe, to test the executable is present
        return

    # script_path = os.path.dirname(os.path.realpath(__file__))
    test_path = os.path.join(os.path.dirname(tests.__file__), "raw_files", "doss")
    # runcry17 requires input file name without extension as first arg
    input_name = sys_args[0]

    with open(input_name + ".d3", "rb") as f:
        content = f.read()
        # hashkey = hashlib.md5(content).digest()
        hashkey = hashlib.md5(content).hexdigest()

    if str(hashkey) not in hash_map:
        raise IOError(
            "contents of {0} not in hash list, hashkey: {1}\n{2}".format(
                os.path.basename(input_name + ".d3"), str(hashkey), content))

    outfiles = hash_map[hashkey]

    for inpath, outext in outfiles.get("output", []):
        src = os.path.join(test_path, *inpath)
        dst = os.path.join(".", input_name + outext)
        copyfile(src, dst)

    sys.stdout.write(
        "running mock runprop17 for input arg: {}".format(input_name))


if __name__ == "__main__":
    main()
