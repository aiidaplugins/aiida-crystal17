from aiida.plugins import DataFactory


def test_potential_lj(db_test_app, data_regression):
    potential_cls = DataFactory("gulp.potential")
    potential_dict = {
            "species": ["Fe core", "S core"],
            "2body": {
                "0-0": {
                    "lj_A": 1.0,
                    "lj_B": 1.0,
                    "lj_rmax": 12.0
                },
                "0-1": {
                    "lj_A": 1.0,
                    "lj_B": 1.0,
                    "lj_rmax": 12.0
                },
                "1-1": {
                    "lj_A": 1.0,
                    "lj_B": 1.0,
                    "lj_rmax": 12.0
                }
            }
        }
    pot = potential_cls("lj", potential_dict)
    data_regression.check(pot.attributes)

    assert pot.pair_style == "lj"
    assert len(pot.get_input_lines()) == 6
    assert pot.get_potential_dict() == potential_dict
    assert pot.species == ["Fe core", "S core"]
