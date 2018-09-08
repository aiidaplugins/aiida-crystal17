"""
parse the main output file and create the required output nodes
"""
import os

import numpy as np
# TODO remove dependancy on ejplugins?
import ejplugins
from ejplugins.crystal import CrystalOutputPlugin

from aiida.parsers.exceptions import OutputParsingError

from aiida_crystal17 import __version__ as pkg_version


# pylint: disable=too-many-locals,too-many-statements
def parse_mainout(abs_path,
                  parser_class,
                  parser_opts=None,
                  atomid_kind_map=None):
    """ parse the main output file and create the required output nodes

    :param abs_path: absolute path of stdout file
    :param parser_class: a string denoting the parser class
    :param parser_opts: dictionary of parser settings
    :param atomid_kind_map: a mapping of atom ids to aiida.orm.data.structure.Kind instances (or raw dict)

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

    # TODO only save StructureData if cell has changed?
    cell_vectors = []
    for n in "a b c".split():
        assert cell_data["cell_vectors"][n]["units"] == "angstrom"
        cell_vectors.append(cell_data["cell_vectors"][n]["magnitude"])

    structure = create_structure({
        "cell_vectors": cell_vectors,
        "pbc": cell_data["pbc"],
        "symbols": cell_data["symbols"],
        "ccoords": cell_data["ccoords"]["magnitude"]
    }, atomid_kind_map)
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


def create_structure(structdict, atomid_kind_map=None):
    """ create a StructureData from a dictionary and mapping

    :param structdict: dict containing 'symbols', 'ccoords', 'pbc', 'cell_vectors'
    :param atomid_kind_map: mapping of atom ids to Kind (or raw dict of kind)
    :return:
    """
    from aiida.orm import DataFactory
    StructureData = DataFactory('structure')
    struct = StructureData(cell=structdict['cell_vectors'])
    struct.set_pbc(structdict["pbc"])

    if atomid_kind_map is None:
        # self.logger.warning(
        #     "no atom id to kind map available, creating new kinds")
        for symbol, ccoord in zip(structdict['symbols'],
                                  structdict['ccoords']):
            struct.append_atom(position=ccoord, symbols=symbol)
    else:
        from aiida.orm.data.structure import Site, Kind
        for i, ccoord in enumerate(structdict['ccoords']):
            if i + 1 in atomid_kind_map:
                kind = atomid_kind_map[i + 1]
            elif str(i + 1) in atomid_kind_map:
                kind = atomid_kind_map[str(i + 1)]
            else:
                raise KeyError(
                    "could not find atom with id {} in map with ids: {}".
                    format(i + 1, list(atomid_kind_map.keys())))
            if not isinstance(kind, Kind):
                kind = Kind(raw=kind)
            if kind.name not in struct.get_site_kindnames():
                struct.append_kind(kind)
            struct.append_site(Site(position=ccoord, kind_name=kind.name))

    return struct
