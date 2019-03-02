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

stdoutfiles = {
    '\xf6\t\x0e\x9f\r\xa6\t\x8ea,\xd2l\xb2\xf1\x16 ': None,
    '\xffw\xb9\x96\xa5\x08\x1ed\xab.\x99p\xc6\xcd\x15\xcb': None,
    ']\x14\xa7|\xb2~\xe2\x1a\xd5\xd1Q\xff7i\xc0\x94': None,
    '.\xaec\xd6b\xd8Q\x83v\xa2\x08\x89+\xe0{\x1d': None
}

additional_files = {
    '\xf6\t\x0e\x9f\r\xa6\t\x8ea,\xd2l\xb2\xf1\x16 ':
    [("mgo_sto3g_scf.crystal.out", ".out")],
    '\xffw\xb9\x96\xa5\x08\x1ed\xab.\x99p\xc6\xcd\x15\xcb':
    [('mgo_sto3g_external.crystal.out', ".out")],
    ']\x14\xa7|\xb2~\xe2\x1a\xd5\xd1Q\xff7i\xc0\x94':
    [('nio_sto3g_afm.crystal.out', ".out")],
    '.\xaec\xd6b\xd8Q\x83v\xa2\x08\x89+\xe0{\x1d':
    [('nio_sto3g_afm_opt.crystal.out', ".out")]
}


def main():

    # script_path = os.path.dirname(os.path.realpath(__file__))
    test_path = os.path.dirname(tests.__file__)
    # runcry17 requires input file name without extension as first arg
    input_name = sys.argv[1]

    with open(input_name + ".d12", "rb") as f:
        hashkey = hashlib.md5(f.read()).digest()

    if hashkey not in stdoutfiles:
        raise IOError("contents of {0} not in hash list, hashkey: {1}".format(
            os.path.basename(input_name + ".d12"), str(hashkey)))

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
