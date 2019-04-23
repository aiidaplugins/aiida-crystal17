"""
parse the main output file and create the required output nodes
"""
from collections import Mapping
# TODO remove dependancy on ejplugins?
import ejplugins
from aiida_crystal17.symmetry import convert_structure
from ejplugins.crystal import CrystalOutputPlugin
from aiida.plugins import DataFactory
from aiida.engine import ExitCode
from aiida_crystal17 import __version__
from aiida_crystal17.calculations.cry_main import CryMainCalculation


class OutputNodes(Mapping):

    def __init__(self):
        self._dict = {
            "results": None,
            "structure": None,
            "symmetry": None
        }

    def _get_results(self):
        return self._dict["results"]

    def _set_results(self, value):
        assert isinstance(value, DataFactory('dict'))
        self._dict["results"] = value

    results = property(_get_results, _set_results)

    def _get_structure(self):
        return self._dict["structure"]

    def _set_structure(self, value):
        assert isinstance(value, DataFactory('structure'))
        self._dict["structure"] = value

    structure = property(_get_structure, _set_structure)

    def _get_symmetry(self):
        return self._dict["symmetry"]

    def _set_symmetry(self, value):
        assert isinstance(value, DataFactory('crystal17.symmetry'))
        self._dict["symmetry"] = value

    symmetry = property(_get_symmetry, _set_symmetry)

    def __getitem__(self, value):
        out = self._dict[value]
        if out is None:
            raise KeyError(value)
        return out

    def __iter__(self):
        for key, val in self._dict.items():
            if val is not None:
                yield key

    def __len__(self):
        len([k for k, v in self._dict.items() if v is not None])


class ParserResult(object):
    def __init__(self):
        self.exit_code = ExitCode()
        self.nodes = OutputNodes()


# pylint: disable=too-many-locals,too-many-statements
def parse_main_out(fileobj, parser_class,
                   init_struct=None,
                   init_settings=None):
    """ parse the main output file and create the required output nodes

    :param abs_path: absolute path of stdout file
    :param parser_class: a string denoting the parser class
    :param init_struct: input structure
    :param init_settings: input structure settings

    :return parse_result
    """
    parser_result = ParserResult()
    exit_codes = CryMainCalculation.exit_codes

    results_data = {
        "parser_version": str(__version__),
        "parser_class": str(parser_class),
        "ejplugins_version": str(ejplugins.__version__),
        "parser_errors": [],
        "parser_warnings": [],
        "errors": [],
        "warnings": []
    }

    cryparse = CrystalOutputPlugin()
    try:
        data = cryparse.read_file(fileobj, log_warnings=False)
    except IOError as err:
        parser_result.exit_code = exit_codes.ERROR_OUTPUT_PARSING
        results_data["parser_errors"].append(
            "Error parsing CRYSTAL 17 main output: {0}".format(err))
        parser_result.nodes.results = DataFactory("dict")(dict=results_data)
        return parser_result

    # data contains the top-level keys:
    # "warnings" (list), "errors" (list), "meta" (dict), "creator" (dict),
    # "initial" (None or dict), "optimisation" (None or dict), "final" (dict)
    # "mulliken" (optional dict)

    # TODO could also read .gui file for definitive final (primitive) geometry,
    # with symmetries
    # TODO could also read .SCFLOG, to get scf output for each opt step
    # TODO could also read files in .optstory folder,
    # to get (primitive) geometries (+ symmetries) for each opt step
    # Note the above files are only available for optimisation runs

    if data["errors"]:
        parser_result.exit_code = exit_codes.ERROR_CRYSTAL_RUN
    results_data["errors"] = data["errors"]
    results_data["warnings"] = data["warnings"]

    # get meta data
    meta_data = data.pop("meta")
    if "elapsed_time" in meta_data:
        h, m, s = meta_data["elapsed_time"].split(':')
        wall_time = int(h) * 3600 + int(m) * 60 + int(s)
        results_data["wall_time_seconds"] = wall_time

    # get initial data
    initial_data = data.pop("initial")
    initial_data = {} if not initial_data else initial_data
    for name, val in initial_data.get("calculation", {}).items():
        results_data["calculation_{}".format(name)] = val
    init_scf_data = initial_data.get("scf", [])
    if init_scf_data:
        results_data["scf_iterations"] = len(init_scf_data)
        # TODO create TrajectoryData from init_scf_data data
    else:
        # TODO new parsing error codes?
        # ERROR **** EXTRN **** GEOMETRY DATA FILE NOT FOUND - EXTERNAL KEYWORD NOT ALLOWED
        # parser_result.exit_code = exit_codes.ERROR_CRYSTAL_RUN
        pass

    # optimisation trajectory data
    opt_data = data.pop("optimisation")
    if opt_data:
        results_data["opt_iterations"] = len(
            opt_data) + 1  # the first optimisation step is the initial scf
    # TODO create TrajectoryData from optimisation data

    final_data = data.pop("final")

    # TODO read separate energy contributions
    energy = final_data["energy"]["total_corrected"]
    results_data["energy"] = energy["magnitude"]
    results_data["energy_units"] = energy["units"]

    # TODO read from .gui file and check consistency of final cell/symmops
    structure = _extract_structure(
        final_data["primitive_cell"], init_struct, results_data)
    if opt_data or not init_struct:
        parser_result.nodes.structure = structure
    else:
        pass
        # TODO test intput structure is same as output structure

    _extract_symmetry(
        final_data, init_settings, results_data, parser_result, exit_codes)

    _extract_mulliken(data, results_data)

    parser_result.nodes.results = DataFactory("dict")(dict=results_data)

    # if array_dict:
    #     arraydata = DataFactory("array")()
    #     for name, array in array_dict.items():
    #         arraydata.set_array(name, np.array(array))
    # else:
    #     arraydata = None

    return parser_result


def _extract_symmetry(final_data, init_settings, param_data,
                      parser_result, exit_codes):
    """extract symmetry operations"""

    if "primitive_symmops" in final_data:

        if init_settings:
            if init_settings.num_symops != len(final_data["primitive_symmops"]):
                param_data["parser_errors"].append(
                    "number of symops different")
                parser_result.exit_code = exit_codes.ERROR_SYMMETRY_INCONSISTENCY
            # differences = init_settings.compare_operations(
            #     final_data["primitive_symmops"])
            # if differences:
            #     param_data["parser_errors"].append(
            #         "output symmetry operations were not the same as "
            #         "those input: {}".format(differences))
            #     parser_result.success = False
        else:
            from aiida.plugins import DataFactory
            SymmetryData = DataFactory('crystal17.symmetry')
            data_dict = {
                "operations": final_data["primitive_symmops"],
                "basis": "fractional",
                "hall_number": None
            }
            parser_result.nodes.symmetry = SymmetryData(data=data_dict)
    else:
        param_data["parser_errors"].append(
            "primitive symmops were not found in the output file")
        parser_result.exit_code = exit_codes.ERROR_SYMMETRY_NOT_FOUND


def _extract_structure(cell_data, init_struct, results_data):
    """create a StructureData object of the final configuration"""
    results_data["number_of_atoms"] = len(cell_data["atomic_numbers"])
    results_data["number_of_assymetric"] = sum(cell_data["assymetric"])

    cell_vectors = []
    for n in "a b c".split():
        assert cell_data["cell_vectors"][n]["units"] == "angstrom"
        cell_vectors.append(cell_data["cell_vectors"][n]["magnitude"])

    # we want to reuse the kinds from the input structure, if available
    if not init_struct:
        results_data["parser_warnings"].append(
            "no initial structure available, creating new kinds for atoms")
        kinds = None
    else:
        kinds = [
            init_struct.get_kind(n) for n in init_struct.get_site_kindnames()
        ]
    structure = convert_structure({
        "lattice": cell_vectors,
        "pbc": cell_data["pbc"],
        "symbols": cell_data["symbols"],
        "ccoords": cell_data["ccoords"]["magnitude"],
        "kinds": kinds
    }, "aiida")
    results_data["volume"] = structure.get_cell_volume()
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
