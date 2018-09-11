import pytest


def test_fail(new_database):
    from aiida.common.exceptions import ValidationError
    from aiida.orm import DataFactory
    StructSettingsData = DataFactory("crystal17.structsettings")

    with pytest.raises(ValidationError):
        StructSettingsData(data={})

    node = StructSettingsData()
    with pytest.raises(ValidationError):
        node.store()


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

    data["space_group"] = 2
    node.set_data(data)

    node.store()

    data["space_group"] = 3
    from aiida.common.exceptions import ModificationNotAllowed
    with pytest.raises(ModificationNotAllowed):
        node.set_data(data)

    assert node.data["space_group"] == 2
