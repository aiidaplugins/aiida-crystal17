import pytest
from jsonschema import ValidationError


def test_fail(new_database):

    from aiida.orm import DataFactory
    StructSettingsData = DataFactory("crystal17.structsettings")

    with pytest.raises(ValidationError):
        StructSettingsData(data={})


def test_pass(new_database):

    from aiida.orm import DataFactory
    StructSettingsData = DataFactory("crystal17.structsettings")

    data = {
        "space_group": 1,
        "crystal_type": 1,
        "centring_code": 1,
        "operations": [[1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]]
    }

    node = StructSettingsData(data=data)

    assert node.data == data
