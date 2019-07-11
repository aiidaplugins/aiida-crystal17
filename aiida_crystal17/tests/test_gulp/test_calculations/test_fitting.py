from aiida.orm import Dict

from aiida_crystal17.tests.utils import sanitize_calc_info


def test_calcjob_submit_mgo(db_test_app, get_structure,
                            data_regression, file_regression):
    """Test submitting a calculation"""
    code = db_test_app.get_or_create_code('gulp.fitting')
    builder = code.get_builder()
    builder.metadata = db_test_app.get_default_metadata(dry_run=True)
    builder.potential = {}
    builder.structures = {
        "MgO": get_structure("MgO")
    }
    builder.observables = {
        "MgO": Dict(dict={"energy": 1})
    }

    process_options = builder.process_class(inputs=builder).metadata.options

    with db_test_app.sandbox_folder() as folder:
        calc_info = db_test_app.generate_calcinfo(
            'gulp.fitting', folder, builder)

        with folder.open(process_options.input_file_name) as f:
            input_content = f.read()

    file_regression.check(input_content)
    data_regression.check(sanitize_calc_info(calc_info))
