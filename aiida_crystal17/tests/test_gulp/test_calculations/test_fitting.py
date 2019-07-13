import os

from aiida.engine import run_get_node
from aiida.orm import Dict
from aiida.plugins import DataFactory

from aiida_crystal17.tests import TEST_FILES
from aiida_crystal17.tests.utils import sanitize_calc_info

from aiida_crystal17.common import recursive_round
from aiida_crystal17.gulp.potentials.common import filter_by_species
from aiida_crystal17.gulp.potentials.raw_reaxff import read_lammps_format


def test_calcjob_submit_lj_fes(db_test_app, get_structure,
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
    builder.settings = {
        "observables": {
            "energy": {"energy_key": "final_energy"}
        }
    }
    builder.structures = {
        "pyrite": get_structure("pyrite"),
        "marcasite": get_structure("marcasite"),
        "zincblende": get_structure("zincblende")
    }
    builder.observables = {
        "pyrite": Dict(dict={"final_energy": -1, "energy_units": "eV"}),
        "marcasite": Dict(dict={"final_energy": -1, "energy_units": "eV"}),
        "zincblende": Dict(dict={"final_energy": 1, "energy_units": "eV"})
    }

    process_options = builder.process_class(inputs=builder).metadata.options

    with db_test_app.sandbox_folder() as folder:
        calc_info = db_test_app.generate_calcinfo(
            'gulp.fitting', folder, builder)

        with folder.open(process_options.input_file_name) as f:
            input_content = f.read()

    file_regression.check(input_content)
    data_regression.check(sanitize_calc_info(calc_info))


def test_calcjob_submit_reaxff_fes(db_test_app, get_structure,
                                   data_regression, file_regression):
    """Test submitting a calculation"""
    code = db_test_app.get_or_create_code('gulp.fitting')
    builder = code.get_builder()
    builder.metadata = db_test_app.get_default_metadata(dry_run=True)
    potential_cls = DataFactory("gulp.potential")
    with open(os.path.join(TEST_FILES, "gulp", "potentials", "FeCrOSCH.reaxff")) as handle:
        content = handle.read()
    pot_data = read_lammps_format(content.splitlines())
    pot_data = filter_by_species(pot_data, ["Fe core", "S core"])
    builder.settings = {
        "observables": {
            "energy": {}
        }
    }
    builder.potential = potential_cls(
        "reaxff",
        pot_data,
        fitting_data={
            "species": ["Fe core", "S core"],
            "global": ["reaxff0_boc1", "reaxff0_boc2"]
        }
    )
    builder.structures = {
        "pyrite": get_structure("pyrite"),
        "marcasite": get_structure("marcasite"),
        "zincblende": get_structure("zincblende")
    }
    builder.observables = {
        "pyrite": Dict(dict={"energy": -1, "energy_units": "eV"}),
        "marcasite": Dict(dict={"energy": -1, "energy_units": "eV"}),
        "zincblende": Dict(dict={"energy": 1, "energy_units": "eV"})
    }

    process_options = builder.process_class(inputs=builder).metadata.options

    with db_test_app.sandbox_folder() as folder:
        calc_info = db_test_app.generate_calcinfo(
            'gulp.fitting', folder, builder)

        with folder.open(process_options.input_file_name) as f:
            input_content = f.read()

    file_regression.check(input_content)
    data_regression.check(sanitize_calc_info(calc_info))


def test_run_lj_fes(db_test_app, get_structure,
                    data_regression):
    """Test running a calculation"""
    code = db_test_app.get_or_create_code('gulp.fitting')
    builder = code.get_builder()
    builder.metadata = db_test_app.get_default_metadata()
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
    builder.settings = {
        "observables": {
            "energy": {}
        }
    }
    builder.structures = {
        "pyrite": get_structure("pyrite"),
        "marcasite": get_structure("marcasite"),
        "zincblende": get_structure("zincblende")
    }
    builder.observables = {
        "pyrite": Dict(dict={"energy": -1, "energy_units": "eV"}),
        "marcasite": Dict(dict={"energy": -1, "energy_units": "eV"}),
        "zincblende": Dict(dict={"energy": 1, "energy_units": "eV"})
    }

    calc_node = run_get_node(builder).node

    db_test_app.check_calculation(calc_node, ["results"])

    result = recursive_round(calc_node.outputs.results.get_dict(), 6)
    for key in ['parser_version', 'peak_dynamic_memory_mb', 'opt_time_second', 'total_time_second']:
        result.pop(key, None)
    data_regression.check(result)


def test_run_reaxff_fes(db_test_app, get_structure, data_regression):
    """Test submitting a calculation"""
    code = db_test_app.get_or_create_code('gulp.fitting')
    builder = code.get_builder()
    builder.metadata = db_test_app.get_default_metadata()
    potential_cls = DataFactory("gulp.potential")
    with open(os.path.join(TEST_FILES, "gulp", "potentials", "FeCrOSCH.reaxff")) as handle:
        content = handle.read()
    pot_data = read_lammps_format(content.splitlines())
    pot_data = filter_by_species(pot_data, ["Fe core", "S core"])
    builder.settings = {
        "observables": {
            "energy": {}
        }
    }
    builder.potential = potential_cls(
        "reaxff",
        pot_data,
        fitting_data={
            "species": ["Fe core", "S core"],
            "global": ["reaxff0_boc1", "reaxff0_boc2"]
        }
    )
    builder.structures = {
        "pyrite": get_structure("pyrite"),
        "marcasite": get_structure("marcasite"),
        "zincblende": get_structure("zincblende")
    }
    builder.observables = {
        "pyrite": Dict(dict={"energy": -1, "energy_units": "eV"}),
        "marcasite": Dict(dict={"energy": -1, "energy_units": "eV"}),
        "zincblende": Dict(dict={"energy": 1, "energy_units": "eV"})
    }

    calc_node = run_get_node(builder).node

    db_test_app.check_calculation(calc_node, ["results"])

    result = recursive_round(calc_node.outputs.results.get_dict(), 6)
    for key in ['parser_version', 'peak_dynamic_memory_mb', 'opt_time_second', 'total_time_second']:
        result.pop(key, None)
    data_regression.check(result)
