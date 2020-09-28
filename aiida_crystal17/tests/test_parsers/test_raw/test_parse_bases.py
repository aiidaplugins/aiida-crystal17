import pytest

from aiida_crystal17.common import recursive_round
from aiida_crystal17.parsers.raw import parse_bases
from aiida_crystal17.tests import read_resource_text


@pytest.mark.parametrize(
    "filename", ("3-21g", "3-21g-star", "tzvp", "free", "barthe", "free_ecp", "haywlc")
)
def test_single_bases(filename, data_regression):
    content = read_resource_text("basis_sets", "manual_examples", filename + ".basis")
    output = parse_bases.parse_bsets_stdin(content, isolated=True)
    output = recursive_round(output, 12)
    data_regression.check(output)


@pytest.mark.parametrize(
    "name,filepath",
    (
        ("mgo_sto3g", ("crystal", "mgo_sto3g_scf", "INPUT")),
        ("nio_sto3g", ("crystal", "nio_sto3g_afm_scf", "INPUT")),
    ),
)
def test_full_files(name, filepath, data_regression):
    content = read_resource_text(*filepath)
    output = parse_bases.parse_bsets_stdin(content, isolated=False)
    output = recursive_round(output, 12)
    data_regression.check(output)


@pytest.mark.parametrize(
    "name,filepath,atoms",
    (
        ("mgo_sto3g", ("crystal", "mgo_sto3g_scf", "INPUT"), (12, 8)),
        ("nio_sto3g", ("crystal", "nio_sto3g_afm_scf", "INPUT"), (28, 28, 8, 8)),
    ),
)
def test_compute_orbitals(name, filepath, atoms, data_regression):
    content = read_resource_text(*filepath)
    basis_sets = parse_bases.parse_bsets_stdin(content, isolated=False)
    orbitals = parse_bases.compute_orbitals(atoms, basis_sets)
    data_regression.check(dict(orbitals._asdict()))
