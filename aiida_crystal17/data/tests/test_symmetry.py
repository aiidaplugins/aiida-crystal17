import pytest


def test_basic(db_test_app):
    from aiida_crystal17.data.symmetry import SymmetryData
    node = SymmetryData()
    data = {
        "hall_number": 1,
        "operations": [
            [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]
        ],
        "basis": "fractional"
    }
    node.set_data(data)
    assert node.hall_number == 1
    assert node.num_symops == 1
    assert node.data == data

    data["hall_number"] = 2
    node.set_data(data)
    assert node.hall_number == 2

    node.store()

    data["hall_number"] = 3
    from aiida.common.exceptions import ModificationNotAllowed
    with pytest.raises(ModificationNotAllowed):
        node.set_data(data)

    assert node.data["hall_number"] == 2


def test_fail(db_test_app):
    from jsonschema import ValidationError
    from aiida.plugins import DataFactory
    symmetry_data_cls = DataFactory("crystal17.symmetry")

    with pytest.raises(ValidationError):
        symmetry_data_cls(data={})

    node = symmetry_data_cls()
    with pytest.raises(ValidationError):
        node.store()
