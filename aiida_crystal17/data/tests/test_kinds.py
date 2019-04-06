def test_basic(db_test_app):
    from aiida_crystal17.data.kinds import KindData
    node = KindData()
    data = {
        "kind_names": ["A", "B", "C"],
        "field1": [1, 2, 3]
    }
    node.set_data(data)
    assert node.data == data
    assert node.kind_dict == {
        "A": {"field1": 1},
        "B": {"field1": 2},
        "C": {"field1": 3}
    }
    assert node.field_dict == {
        "field1": {
            "A": 1,
            "B": 2,
            "C": 3
        }
    }
