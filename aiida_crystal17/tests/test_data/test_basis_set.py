"""Tests for BasisSetData."""
from io import StringIO

import pytest

from aiida.plugins import DataFactory

from aiida_crystal17.data.basis_set import BasisSetData
from aiida_crystal17.tests import open_resource_text, read_resource_text, resource_context


def test_create_single_from_file(db_test_app):
    db_test_app.get_or_create_computer()

    with open_resource_text('basis_sets', 'sto3g', 'sto3g_Mg.basis') as handle:
        basis = BasisSetData(filepath=handle)

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
    with open_resource_text('basis_sets', 'sto3g', 'sto3g_Mg.basis') as handle:
        basis, created = BasisSetData.get_or_create(basis_file=handle)
    assert not created


def test_create_single_from_stringio(db_test_app):
    db_test_app.get_or_create_computer()

    content = read_resource_text('basis_sets', 'sto3g', 'sto3g_Mg.basis')
    basis = BasisSetData(filepath=StringIO(content))

    print(basis.filename)

    expected_meta = {
        'num_shells': 3,
        'author': 'John Smith',
        'atomic_number': 12,
        'filename': 'stringio.txt',
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
    basis, created = BasisSetData.get_or_create(basis_file=StringIO(content))
    assert not created


def test_create_group(db_test_app):
    db_test_app.get_or_create_computer()

    with resource_context('basis_sets', 'sto3g') as path:
        nfiles, nuploaded = BasisSetData.upload_basisset_family(path, 'sto3g', 'group of sto3g basis sets')

    assert (nfiles, nuploaded) == (3, 3)

    group = BasisSetData.get_basis_group('sto3g')

    assert group.description == 'group of sto3g basis sets'

    groups = BasisSetData.get_basis_groups(filter_elements='O')
    # print(groups)
    assert len(groups) == 1

    # try uploading the files to a second group
    with pytest.raises(ValueError):
        with resource_context('basis_sets', 'sto3g') as path:
            BasisSetData.upload_basisset_family(path,
                                                'another_sto3g',
                                                'another group of sto3g basis sets',
                                                stop_if_existing=True)

    with resource_context('basis_sets', 'sto3g') as path:
        nfiles, nuploaded = BasisSetData.upload_basisset_family(path,
                                                                'another_sto3g',
                                                                'another group of sto3g basis sets',
                                                                stop_if_existing=False)
    assert (nfiles, nuploaded) == (3, 0)


def test_bases_from_struct(db_test_app):
    db_test_app.get_or_create_computer()

    with resource_context('basis_sets', 'sto3g') as path:
        nfiles, nuploaded = BasisSetData.upload_basisset_family(path, 'sto3g', 'group of sto3g basis sets')

    # MgO
    import ase  # noqa: F401
    from ase.spacegroup import crystal
    atoms = crystal(symbols=[12, 8],
                    basis=[[0, 0, 0], [0.5, 0.5, 0.5]],
                    spacegroup=225,
                    cellpar=[4.21, 4.21, 4.21, 90, 90, 90])  # type: ase.Atoms

    # atoms[0].tag = 1
    # atoms[1].tag = 1
    atoms.set_tags([1, 1, 0, 0, 0, 0, 0, 0])

    structure_data_cls = DataFactory('structure')
    struct = structure_data_cls(ase=atoms)

    bases_dict = BasisSetData.get_basissets_by_kind(struct, 'sto3g')
    # print(bases_dict)

    assert set(bases_dict.keys()) == set(['Mg', 'Mg1', 'O'])

    assert bases_dict['Mg'].get_basis_family_names() == ['sto3g']
