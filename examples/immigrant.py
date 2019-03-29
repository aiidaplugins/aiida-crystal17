"""
Usage: verdi run test_immigrant.py
"""
import os

from aiida_crystal17.tests import TEST_DIR


def test_example(new_database):
    from aiida_crystal17.workflows.cry_main_immigrant import migrate_as_main

    inpath = os.path.join("input_files", 'nio_sto3g_afm.crystal.d12')
    outpath = os.path.join("output_files", 'nio_sto3g_afm.crystal.out')

    node = migrate_as_main(TEST_DIR, inpath, outpath)

    print("Calculation migrated to stored pk: {}".format(node.pk))


if __name__ == "__main__":
    test_example(None)