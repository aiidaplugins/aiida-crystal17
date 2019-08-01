"""
tests BasisSetData
"""
import os

from aiida.plugins import DataFactory
import pytest

from aiida_crystal17.tests import TEST_FILES


def test_create_single(db_test_app):
    db_test_app.get_or_create_computer()

    basisset_data_cls = DataFactory('crystal17.basisset')

    basis = basisset_data_cls(filepath=os.path.join(TEST_FILES, 'basis_sets', 'sto3g', 'sto3g_Mg.basis'))

    print(basis.filename)

    expected_meta = {
        'num_shells': 3,
        'author': 'John Smith',
        'atomic_number': 12,
        'filename': 'sto3g_Mg.basis',
        'element': 'Mg',
        'year': 1999,
        'basis_type': 'all-electron',
        'class': 'sto3g',
        'md5': '0731ecc3339d2b8736e61add113d0c6f',
        'orbital_types': ['S', 'SP', 'SP']
    }

    assert basis.metadata == expected_meta

    expected_content = """\
12 3
1 0 3  2.  0.
1 1 3  8.  0.
1 1 3  2.  0."""
    assert basis.content == expected_content

    basis.store()

    # try retrieving a pre-existing (stored) basis
    basis, created = basisset_data_cls.get_or_create(
        filepath=os.path.join(TEST_FILES, 'basis_sets', 'sto3g', 'sto3g_Mg.basis'))
    assert not created


def test_create_group(db_test_app):
    db_test_app.get_or_create_computer()
    basisset_data_cls = DataFactory('crystal17.basisset')
    upload_basisset_family = basisset_data_cls.upload_basisset_family

    nfiles, nuploaded = upload_basisset_family(
        os.path.join(TEST_FILES, 'basis_sets', 'sto3g'), 'sto3g', 'group of sto3g basis sets')

    assert (nfiles, nuploaded) == (3, 3)

    group = basisset_data_cls.get_basis_group('sto3g')

    assert group.description == 'group of sto3g basis sets'

    groups = basisset_data_cls.get_basis_groups(filter_elements='O')
    # print(groups)
    assert len(groups) == 1

    # try uploading the files to a second group
    with pytest.raises(ValueError):
        upload_basisset_family(
            os.path.join(TEST_FILES, 'basis_sets', 'sto3g'),
            'another_sto3g',
            'another group of sto3g basis sets',
            stop_if_existing=True)

    nfiles, nuploaded = upload_basisset_family(
        os.path.join(TEST_FILES, 'basis_sets', 'sto3g'),
        'another_sto3g',
        'another group of sto3g basis sets',
        stop_if_existing=False)
    assert (nfiles, nuploaded) == (3, 0)


def test_bases_from_struct(db_test_app):
    db_test_app.get_or_create_computer()
    basisset_data_cls = DataFactory('crystal17.basisset')
    upload_basisset_family = basisset_data_cls.upload_basisset_family

    nfiles, nuploaded = upload_basisset_family(
        os.path.join(TEST_FILES, 'basis_sets', 'sto3g'), 'sto3g', 'group of sto3g basis sets')

    # MgO
    import ase  # noqa: F401
    from ase.spacegroup import crystal
    atoms = crystal(
        symbols=[12, 8], basis=[[0, 0, 0], [0.5, 0.5, 0.5]], spacegroup=225, cellpar=[4.21, 4.21, 4.21, 90, 90,
                                                                                      90])  # type: ase.Atoms

    # atoms[0].tag = 1
    # atoms[1].tag = 1
    atoms.set_tags([1, 1, 0, 0, 0, 0, 0, 0])

    structure_data_cls = DataFactory('structure')
    struct = structure_data_cls(ase=atoms)

    bases_dict = basisset_data_cls.get_basissets_by_kind(struct, 'sto3g')
    # print(bases_dict)

    assert set(bases_dict.keys()) == set(['Mg', 'Mg1', 'O'])
