from aiida.plugins import DataFactory


def test_potential_lj(db_test_app, data_regression):
    potential_cls = DataFactory("gulp.potential")
    pot = potential_cls(
        "lj",
        {
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
    )
    data_regression.check(pot.attributes)

    assert pot.pair_style == "lj"
    assert len(pot.get_input_lines()) == 6
