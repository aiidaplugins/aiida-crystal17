"""
tests BasisSetData
"""
import os

import aiida_crystal17.tests as tests


def test_create_single(new_database, new_workdir):
    computer = tests.get_computer(workdir=new_workdir)

    from aiida.orm import DataFactory
    BasisSetData = DataFactory("crystal17.basisset")

    basis = BasisSetData(
        file=os.path.join(tests.TEST_DIR, "input_files", 'sto3g_Mg.basis'))

    expected = {
        'num_shells': 12,
        'author': 'John Smith',
        'atomic_number': 12,
        'filename': 'sto3g_Mg.basis',
        'element': 'Mg',
        'year': 1999,
        'basis_type': 'all-electron',
        'class': 'sto3g',
        'md5': 'd005f3a56f50b79f58e6206a987dd51d'
    }

    assert basis.metadata == expected


def test_create_group(new_database, new_workdir):
    computer = tests.get_computer(workdir=new_workdir)
    from aiida_crystal17.data.basis_set import upload_basisset_family

    nfiles, nuploaded = upload_basisset_family(
        os.path.join(tests.TEST_DIR, "input_files"), "sto3g",
        "group of sto3g basis sets")

    assert (nfiles, nuploaded) == (2, 2)

    from aiida.orm import DataFactory
    BasisSetData = DataFactory("crystal17.basisset")

    group = BasisSetData.get_basis_group("sto3g")

    assert group.description == "group of sto3g basis sets"

    groups = BasisSetData.get_basis_groups(filter_elements="O")
    # print(groups)
    assert len(groups) == 1


def test_bases_from_struct(new_database, new_workdir):

    computer = tests.get_computer(workdir=new_workdir)
    from aiida_crystal17.data.basis_set import upload_basisset_family

    nfiles, nuploaded = upload_basisset_family(
        os.path.join(tests.TEST_DIR, "input_files"), "sto3g",
        "group of sto3g basis sets")

    # MgO
    from ase.spacegroup import crystal
    atoms = crystal(
        symbols=[12, 8],
        basis=[[0, 0, 0], [0.5, 0.5, 0.5]],
        spacegroup=225,
        cellpar=[4.21, 4.21, 4.21, 90, 90, 90])

    atoms[0].tag = 1
    atoms[1].tag = 1

    print(atoms)
    from aiida.orm import DataFactory
    StructureData = DataFactory("structure")
    struct = StructureData(ase=atoms)

    from aiida_crystal17.data.basis_set import get_basisset_dict
    bases_dict = get_basisset_dict(struct, "sto3g")
    # print(bases_dict)

    assert set(bases_dict.keys()) == set(["Mg", "Mg1", "O"])
