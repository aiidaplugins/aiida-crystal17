"""
parse the main output file and create the required output nodes
"""
import os

# TODO remove dependancy on ejplugins?
import ejplugins
from aiida_crystal17.parsers.geometry import dict_to_structure, operation_frac_to_cart
from ejplugins.crystal import CrystalOutputPlugin

from aiida.parsers.exceptions import OutputParsingError

from aiida_crystal17 import __version__ as pkg_version


# pylint: disable=too-many-locals,too-many-statements
def parse_mainout(abs_path, parser_class, init_struct=None,
                  init_settings=None):
    """ parse the main output file and create the required output nodes

    :param abs_path: absolute path of stdout file
    :param parser_class: a string denoting the parser class
    :param init_struct: input structure
    :param init_settings: input structure settings

    :return psuccess: a boolean that is False in case of failed calculations
    :return output_nodes: containing "paramaters" and (optionally) "structure" and "settings"
    """
    from aiida.orm import DataFactory

    psuccess = True
    param_data = {"parser_warnings": []}
    output_nodes = {}

    cryparse = CrystalOutputPlugin()
    if not os.path.exists(abs_path):
        raise OutputParsingError(
            "The raw data file does not exist: {}".format(abs_path))
    with open(abs_path) as f:
        try:
            data = cryparse.read_file(f, log_warnings=False)
        except IOError as err:
            param_data["parser_warnings"].append(
                "Error in CRYSTAL 17 run output: {}".format(err))
            output_nodes["parameters"] = DataFactory("parameter")(
                dict=param_data)
            return False, output_nodes

    # data contains the top-level keys:
    # "warnings" (list), "errors" (list), "meta" (dict), "creator" (dict),
    # "initial" (None or dict), "optimisation" (None or dict), "final" (dict)
    # "mulliken" (optional dict)

    # TODO could also read .gui file for definitive final (primitive) geometry, with symmetries
    # TODO could also read .SCFLOG, to get scf output for each opt step
    # TODO could also read files in .optstory folder, to get (primitive) geometries (+ symmetries) for each opt step
    # Note the above files are only available for optimisation runs

    perrors = data["errors"]
    pwarnings = data["warnings"]
    if perrors:
        psuccess = False
    param_data["errors"] = perrors
    # aiida-quantumespresso only has warnings, so we group errors and warnings for compatibility
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

    # TODO read separate energy contributions
    energy = final_data["energy"]["total_corrected"]
    param_data["energy"] = energy["magnitude"]
    param_data["energy_units"] = energy["units"]

    # TODO only save StructureData if cell has changed
    # TODO read from .gui file and check consistency of final cell/symmops
    structure = _extract_structure(final_data["primitive_cell"], init_struct,
                                   param_data)
    output_nodes["structure"] = structure

    ssuccess = _extract_symmetry(final_data, init_settings, output_nodes,
                                 param_data, structure.cell)
    psuccess = False if not ssuccess else psuccess

    _extract_mulliken(data, param_data)

    # add the version and class of parser
    param_data["parser_version"] = str(pkg_version)
    param_data["parser_class"] = str(parser_class)
    param_data["ejplugins_version"] = str(ejplugins.__version__)

    output_nodes["parameters"] = DataFactory("parameter")(dict=param_data)

    # if array_dict:
    #     arraydata = DataFactory("array")()
    #     for name, array in array_dict.items():
    #         arraydata.set_array(name, np.array(array))
    # else:
    #     arraydata = None

    return psuccess, output_nodes


def _extract_symmetry(final_data, init_settings, output_nodes, param_data,
                      lattice):
    """extract symmetry operations"""
    psuccess = True
    if "primitive_symmops" in final_data:

        cart_ops = []
        for op in final_data["primitive_symmops"]:
            rot = [op[0:3], op[3:6], op[6:9]]
            trans = op[9:12]
            rot, trans = operation_frac_to_cart(lattice, rot, trans)
            cart_ops.append(rot[0] + rot[1] + rot[2] + trans)

        if init_settings:
            differences = init_settings.compare_operations(cart_ops)
            if differences:
                param_data["parser_warnings"].append(
                    "output symmetry operations were not the same as those input: {}".
                    format(differences))
                psuccess = False
        else:
            from aiida.orm import DataFactory
            StructSettings = DataFactory('crystal17.structsettings')
            # TODO retrieve centering code, crystal system and spacegroup
            settings_dict = {
                "operations": cart_ops,
                "space_group": 1,
                "crystal_type": 1,
                "centring_code": 1
            }
            output_nodes["settings"] = StructSettings(data=settings_dict)
    else:
        param_data["parser_warnings"].append(
            "primitive symmops were not found in the output file")
        psuccess = False

    return psuccess


def _extract_structure(cell_data, init_struct, param_data):
    """create a StructureData object of the final configuration"""
    param_data["number_of_atoms"] = len(cell_data["atomic_numbers"])
    param_data["number_of_assymetric"] = sum(cell_data["assymetric"])

    cell_vectors = []
    for n in "a b c".split():
        assert cell_data["cell_vectors"][n]["units"] == "angstrom"
        cell_vectors.append(cell_data["cell_vectors"][n]["magnitude"])

    # we want to reuse the kinds from the input structure, if available
    if not init_struct:
        param_data["parser_warnings"].append(
            "no initial structure available, creating new kinds for atoms")
        kinds = None
    else:
        kinds = [
            init_struct.get_kind(n) for n in init_struct.get_site_kindnames()
        ]
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
        kinds
    })
    param_data["volume"] = structure.get_cell_volume()
    return structure


def _extract_mulliken(indata, param_data):
    """extract mulliken electronic charge partition data"""
    if indata.get("mulliken", False):
        if "alpha+beta_electrons" in indata["mulliken"]:
            electrons = indata["mulliken"]["alpha+beta_electrons"]["charges"]
            anum = indata["mulliken"]["alpha+beta_electrons"]["atomic_numbers"]
            param_data["mulliken_electrons"] = electrons
            param_data["mulliken_charges"] = [
                a - e for a, e in zip(anum, electrons)
            ]
        if "alpha-beta_electrons" in indata["mulliken"]:
            param_data["mulliken_spins"] = indata["mulliken"][
                "alpha-beta_electrons"]["charges"]
            param_data["mulliken_spin_total"] = sum(
                param_data["mulliken_spins"])
