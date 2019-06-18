from aiida.plugins import DataFactory


def get_potential_lj():
    return {
        "atoms": {
            "Fe": {
                "Fe": {
                    "A": 1.0,
                    "B": 1.0,
                    "rmax": 12.0
                },
                "S": {
                    "A": 1.0,
                    "B": 1.0,
                    "rmax": 12.0
                }
            },
            "S": {
                "S": {
                    "A": 1.0,
                    "B": 1.0,
                    "rmax": 12.0
                }
            }
        }
    }


def test_potential_lj(db_test_app, data_regression):
    potential_cls = DataFactory("gulp.potential")
    pot = potential_cls("lj", get_potential_lj())
    data_regression.check(pot.attributes)

    assert pot.pair_style == "lj"
