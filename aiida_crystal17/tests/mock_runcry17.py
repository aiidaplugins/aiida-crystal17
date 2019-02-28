#!/usr/bin/env python
"""
this is a mock version of runcry17,
which compares an input file to a hash and writes an appropriate outputfile st stdoout

to add find hashkeys:

input_path = 'path/to/input.d12'
with open(input_path, "rb") as f:
    hashkey = hashlib.md5(f.read()).digest()
hashkey

"""
import hashlib
import os
import sys
from shutil import copyfile

import aiida_crystal17.tests as tests

# Note: moved to hex hashes because they are easy to deal with in python3

# stdoutfiles = {
#     '\xf6\t\x0e\x9f\r\xa6\t\x8ea,\xd2l\xb2\xf1\x16 ': None,
#     '\xffw\xb9\x96\xa5\x08\x1ed\xab.\x99p\xc6\xcd\x15\xcb': None,
#     ']\x14\xa7|\xb2~\xe2\x1a\xd5\xd1Q\xff7i\xc0\x94': None,
#     '.\xaec\xd6b\xd8Q\x83v\xa2\x08\x89+\xe0{\x1d': None
# }

# additional_files = {
#     '\xf6\t\x0e\x9f\r\xa6\t\x8ea,\xd2l\xb2\xf1\x16 ':
#     [("mgo_sto3g_scf.crystal.out", ".out")],
#     '\xffw\xb9\x96\xa5\x08\x1ed\xab.\x99p\xc6\xcd\x15\xcb':
#     [('mgo_sto3g_external.crystal.out', ".out")],
#     ']\x14\xa7|\xb2~\xe2\x1a\xd5\xd1Q\xff7i\xc0\x94':
#     [('nio_sto3g_afm.crystal.out', ".out")],
#     '.\xaec\xd6b\xd8Q\x83v\xa2\x08\x89+\xe0{\x1d':
#     [('nio_sto3g_afm_opt.crystal.out', ".out")]
# }

stdoutfiles = {
    "f6090e9f0da6098e612cd26cb2f11620": None,
    "ff77b996a5081e64ab2e9970c6cd15cb": None,
    "5d14a77cb27ee21ad5d151ff3769c094": None,
    "2eae63d662d8518376a208892be07b1d": None
}

additional_files = {
    "f6090e9f0da6098e612cd26cb2f11620":
    [("mgo_sto3g_scf.crystal.out", ".out")],
    "ff77b996a5081e64ab2e9970c6cd15cb":
    [('mgo_sto3g_external.crystal.out', ".out")],
    "5d14a77cb27ee21ad5d151ff3769c094":
    [('nio_sto3g_afm.crystal.out', ".out")],
    "2eae63d662d8518376a208892be07b1d":
    [('nio_sto3g_afm_opt.crystal.out', ".out")]
}


def main(input_name=None):

    if input_name is None:
        input_name = sys.argv[1]

    # script_path = os.path.dirname(os.path.realpath(__file__))
    test_path = os.path.dirname(tests.__file__)
    # runcry17 requires input file name without extension as first arg

    with open(input_name + ".d12", "rb") as f:
        content = f.read()
        # hashkey = hashlib.md5(content).digest()
        hashkey = hashlib.md5(content).hexdigest()

    if str(hashkey) not in stdoutfiles:
        raise IOError(
            "contents of {0} not in hash list, hashkey: {1}\n{2}".format(
                os.path.basename(input_name + ".d12"), str(hashkey), content))

    for inname, outext in additional_files.get(hashkey, []):
        src = os.path.join(test_path, "output_files", inname)
        dst = os.path.join(".", input_name + outext)
        copyfile(src, dst)

    if stdoutfiles[hashkey] is None:
        sys.stdout.write(
            "running mock runcry17 for input arg: {}".format(input_name))
    else:
        outpath = os.path.join(test_path, "output_files", stdoutfiles[hashkey])
        with open(outpath) as f:
            sys.stdout.write(f.read())


if __name__ == "__main__":
    main()
