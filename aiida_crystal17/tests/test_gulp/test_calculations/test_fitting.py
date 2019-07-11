from aiida.orm import Dict
from aiida.plugins import DataFactory

from aiida_crystal17.tests.utils import sanitize_calc_info


def test_calcjob_submit_fes(db_test_app, get_structure,
                            data_regression, file_regression):
    """Test submitting a calculation"""
    code = db_test_app.get_or_create_code('gulp.fitting')
    builder = code.get_builder()
    builder.metadata = db_test_app.get_default_metadata(dry_run=True)
    potential_cls = DataFactory("gulp.potential")
    builder.potential = potential_cls(
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
        },
        fitting_data={
            "species": ["Fe core", "S core"],
            "2body": {
                "0-0": ["lj_A", "lj_B"],
                "0-1": [],
                "1-1": [],
            }
        }
    )
    builder.structures = {
        "pyrite": get_structure("pyrite"),
        "marcasite": get_structure("marcasite"),
        "zincblende": get_structure("zincblende")
    }
    builder.observables = {
        "pyrite": Dict(dict={"energy": -1}),
        "marcasite": Dict(dict={"energy": -1}),
        "zincblende": Dict(dict={"energy": 1})
    }

    process_options = builder.process_class(inputs=builder).metadata.options

    with db_test_app.sandbox_folder() as folder:
        calc_info = db_test_app.generate_calcinfo(
            'gulp.fitting', folder, builder)

        with folder.open(process_options.input_file_name) as f:
            input_content = f.read()

    file_regression.check(input_content)
    data_regression.check(sanitize_calc_info(calc_info))
