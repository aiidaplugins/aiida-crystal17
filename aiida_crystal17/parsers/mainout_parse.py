"""
parse the main output file and create the required output nodes
"""
import os

import numpy as np
# TODO remove dependancy on ejplugins?
import ejplugins
from aiida_crystal17.parsers.geometry import dict_to_structure
from ejplugins.crystal import CrystalOutputPlugin

from aiida.parsers.exceptions import OutputParsingError

from aiida_crystal17 import __version__ as pkg_version


# pylint: disable=too-many-locals,too-many-statements
def parse_mainout(abs_path, parser_class, parser_opts=None, atom_kinds=None):
    """ parse the main output file and create the required output nodes

    :param abs_path: absolute path of stdout file
    :param parser_class: a string denoting the parser class
    :param parser_opts: dictionary of parser settings
    :param atom_kinds: aiida.orm.data.structure.Kind instances (or raw dict) for each atom

    :return param_dict: ParameterData with parsed parameters
    :return array_data: None or ArryayData with parsed arrays
    :return struct_dict: None of StructureData of final (primitive) structure
    :return psuccess: a boolean that is False in case of failed calculations
    :return perrors: a list of errors
    """
    from aiida.orm import DataFactory
    # TODO do we need to use settings for anything, or remove?
    parser_opts = {} if parser_opts is None else parser_opts

    psuccess = True
    param_data = {"parser_warnings": []}
    array_dict = {}

    cryparse = CrystalOutputPlugin()
    if not os.path.exists(abs_path):
        raise OutputParsingError(
            "The raw data file does not exist: {}".format(abs_path))
    with open(abs_path) as f:
        try:
            data = cryparse.read_file(f, log_warnings=False)
        except IOError as err:
            error_str = "Error in CRYSTAL 17 run output: {}".format(err)
            param_data["parser_warnings"].append(error_str)
            return param_data, psuccess, [error_str]

    # data contains the top-level keys:
    # "warnings" (list), "errors" (list), "meta" (dict), "creator" (dict),
    # "initial" (None or dict), "optimisation" (None or dict), "final" (dict)
    # "mulliken" (optional dict)

    # TODO could also read .gui file for definitive final (primitive) geometry, with symmetries
    # TODO could also read .SCFLOG, to get scf output for each opt step
    # TODO could also read files in .optstory folder, to get (primitive) geometries (+ symmetries) for each opt step
    # Note the above files are only available for optimisation runs
    # TODO read separate energy contributions

    perrors = data["errors"]
    pwarnings = data["warnings"]
    if perrors:
        psuccess = False
    param_data["errors"] = perrors
    # aiida-quantumespresso only has warnings
    param_data["warnings"] = perrors + pwarnings

    # get meta data
    meta_data = data.pop("meta")
    if "elapsed_time" in meta_data:
        h, m, s = meta_data["elapsed_time"].split(':')
        param_data["wall_time_seconds"] = int(h) * 3600 + int(m) * 60 + int(s)

    # get initial data
    initial_data = data.pop("initial")
    initial_data = {} if not initial_data else initial_data
    for name, val in initial_data.get("calculation", {}).items():
        param_data["calculation_{}".format(name)] = val
    init_scf_data = initial_data.get("scf", [])
    param_data["scf_iterations"] = len(init_scf_data)
    # TODO create TrajectoryData from init_scf_data data

    # optimisation trajectory data
    opt_data = data.pop("optimisation")
    if opt_data:
        param_data["opt_iterations"] = len(
            opt_data) + 1  # the first optimisation step is the initial scf
    # TODO create TrajectoryData from optimisation data

    final_data = data.pop("final")
    energy = final_data["energy"]["total_corrected"]
    param_data["energy"] = energy["magnitude"]
    param_data["energy_units"] = energy["units"]

    # create a StructureData object of final cell
    cell_data = final_data["primitive_cell"]
    # TODO read from .gui file and/or check consistency

    param_data["number_of_atoms"] = len(cell_data["atomic_numbers"])
    param_data["number_of_assymetric"] = sum(cell_data["assymetric"])

    if "primitive_symmops" in final_data:
        symm_data = final_data["primitive_symmops"]
        param_data["number_of_symmops"] = len(symm_data)
        array_dict["primitive_symmops"] = symm_data

    _extract_mulliken(array_dict, data, param_data)

    # TODO only save StructureData if cell has changed?
    cell_vectors = []
    for n in "a b c".split():
        assert cell_data["cell_vectors"][n]["units"] == "angstrom"
        cell_vectors.append(cell_data["cell_vectors"][n]["magnitude"])

    if not atom_kinds:
        param_data["parser_warnings"].append(
            "no 'kinds' available, creating new kinds")

    structure = dict_to_structure({
        "lattice":
        cell_vectors,
        "pbc":
        cell_data["pbc"],
        "symbols":
        cell_data["symbols"],
        "ccoords":
        cell_data["ccoords"]["magnitude"],
        "kinds":
        atom_kinds
    })
    param_data["volume"] = structure.get_cell_volume()

    # add the version and class of parser
    param_data["parser_version"] = str(pkg_version)
    param_data["parser_class"] = str(parser_class)
    param_data["ejplugins_version"] = str(ejplugins.__version__)

    param_data = DataFactory("parameter")(dict=param_data)

    if array_dict:
        arraydata = DataFactory("array")()
        for name, array in array_dict.items():
            arraydata.set_array(name, np.array(array))
    else:
        arraydata = None

    return param_data, arraydata, structure, psuccess, perrors


def _extract_mulliken(array_dict, data, param_data):
    """extract mulliken data"""
    if data.get("mulliken", False):
        if "alpha+beta_electrons" in data["mulliken"]:
            electrons = data["mulliken"]["alpha+beta_electrons"]["charges"]
            anum = data["mulliken"]["alpha+beta_electrons"]["atomic_numbers"]
            array_dict["mulliken_electrons"] = electrons
            array_dict["mulliken_charges"] = [
                a - e for a, e in zip(anum, electrons)
            ]
        if "alpha-beta_electrons" in data["mulliken"]:
            param_data["mulliken_spins"] = data["mulliken"][
                "alpha-beta_electrons"]["charges"]
            param_data["mulliken_spin_total"] = sum(
                param_data["mulliken_spins"])
