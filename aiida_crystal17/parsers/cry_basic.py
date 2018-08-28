"""
A parser to read output from a standard CRYSTAL17 run
"""
import os

from aiida.parsers.parser import Parser
from aiida.parsers.exceptions import OutputParsingError
from aiida.common.datastructures import calc_states
from aiida.orm import CalculationFactory
from aiida.orm import DataFactory

# TODO remove dependancy on ejplugins?
import ejplugins
from ejplugins.crystal import CrystalOutputPlugin
from ase import Atoms

from aiida_crystal17 import __version__ as pkg_version


class CryBasicParser(Parser):
    """
    Parser class for parsing (stdout) output of a standard CRYSTAL17 run
    """

    def __init__(self, calculation):
        """
        Initialize Parser instance
        """
        CryBasicCalculation = CalculationFactory('crystal17.basic')
        # check for valid input
        if not isinstance(calculation, CryBasicCalculation):
            raise OutputParsingError("Can only parse CryBasicCalculation")

        super(CryBasicParser, self).__init__(calculation)

    # pylint: disable=protected-access
    def check_state(self):
        """Log an error if the calculation being parsed is not in PARSING state."""
        if self._calc.get_state() != calc_states.PARSING:
            self.logger.error('Calculation not in parsing state')

    # pylint: disable=protected-access
    def get_folder(self, retrieved):
        """Convenient access to the retrieved folder."""
        try:
            out_folder = retrieved[self._calc._get_linkname_retrieved()]
            return out_folder
        except KeyError:
            self.logger.error('No retrieved folder found')
            return None

    def get_parser_settings_key(self):
        """
        Return the name of the key to be used in the calculation settings, that
        contains the dictionary with the parser_options
        """
        return 'parser_options'

    def get_linkname_outstructure(self):
        """
        Returns the name of the link to the output_structure
        Node exists if positions or cell changed.
        """
        return 'output_structure'

    # pylint: disable=too-many-locals
    def parse_stdout(self, abs_path, parser_opts=None):
        """ parse the stdout file to the required nodes

        :param abs_path: absolute path of stdout file
        :param parser_opts: dictionary of parser settings

        :return param_dict: a dictionary with parsed parameters
        :return struct_dict: a representation of the output structure
        :return psuccess: a boolean that is False in case of failed calculations
        :return perrors: a list of errors
        """
        # TODO do we need to use settings for anything, or remove?

        parser_opts = {} if parser_opts is None else parser_opts

        psuccess = True
        out_data = {"parser_warnings": []}

        # TODO manage exception
        cryparse = CrystalOutputPlugin()
        if not os.path.exists(abs_path):
            raise OutputParsingError("The raw data file does not exist: {}".format(abs_path))
        with open(abs_path) as f:
            try:
                data = cryparse.read_file(f, log_warnings=False)
            except IOError as err:
                error_str = "Error in CRYSTAL 17 run output: {}".format(err)
                out_data["parser_warnings"].append(error_str)
                return out_data, psuccess, [error_str]

        # data contains the top-level keys:
        # "warnings" (list), "errors" (list), "meta" (dict), "creator" (dict),
        # "initial" (None or dict), "optimisation" (None or dict), "final" (dict)
        # "mulliken" (optional dict)

        # TODO could also read .gui file for definitive final (primitive) geometry, with symmetries
        # TODO could also read .SCFLOG, to get scf output for each opt step
        # TODO could also read files in .optstory folder, to get (primitive) geometrie (+ symmetries) for each opt step
        # Note the above files are only available for optimisation runs
        # TODO read symmetries (for primitive cell) from stdout
        # TODO read separate energy contributions

        perrors = data["errors"]
        pwarnings = data["warnings"]
        if perrors:
            psuccess = False
        out_data["errors"] = perrors
        # aiida-quantumespresso only has warnings
        out_data["warnings"] = perrors + pwarnings

        # get meta data
        meta_data = data.pop("meta")
        if "elapsed_time" in meta_data:
            h, m, s = meta_data["elapsed_time"].split(':')
            out_data["wall_time_seconds"] = int(h) * 3600 + int(m) * 60 + int(s)

        # get initial data
        initial_data = data.pop("initial")
        initial_data = {} if not initial_data else initial_data
        for name, val in initial_data.get("calculation", {}).items():
            out_data["calculation_{}".format(name)] = val
        init_scf_data = initial_data.get("scf", [])
        out_data["scf_iterations"] = len(init_scf_data)
        # TODO create TrajectoryData from init_scf_data data

        # optimisation trajectory data
        opt_data = data.pop("optimisation")
        if opt_data:
            out_data["opt_iterations"] = len(opt_data) + 1  # the first optimisation step is the initial scf
        # TODO create TrajectoryData from optimisation data

        final_data = data.pop("final")
        energy = final_data["energy"]["total_corrected"]
        out_data["energy"] = energy["magnitude"]
        out_data["energy_units"] = energy["units"]

        # create a StructureData object of final cell
        cell_data = final_data["primitive_cell"]

        # cell_params = []
        # for n in "a b c alpha beta gamma".split():
        #     assert cell_data["cell_parameters"][n]["units"] in ["angstrom", "degrees"]
        #     cell_params.append(cell_data["cell_parameters"][n]["magnitude"] )
        # fcoords = cell_data["fcoords"]

        # more precise to use cell vectors and ccoords (correct centering for symmetry)
        cell_vectors = []
        for n in "a b c".split():
            assert cell_data["cell_vectors"][n]["units"] == "angstrom"
            cell_vectors.append(cell_data["cell_vectors"][n]["magnitude"])
        ccoords = cell_data["ccoords"]["magnitude"]

        struct_data = {
            "cell_vectors": cell_vectors,
            "pbc": cell_data["pbc"],
            "symbols": cell_data["symbols"],
            "ccoords": ccoords
        }

        out_data["number_of_atoms"] = len(cell_data["atomic_numbers"])
        out_data["number_of_assymetric"] = sum(cell_data["assymetric"])

        atoms = Atoms(numbers=cell_data["atomic_numbers"],
                      positions=ccoords,
                      pbc=cell_data["pbc"],
                      cell=cell_vectors)
        out_data["volume"] = atoms.get_volume()

        if data.get("mulliken", False):
            if "alpha+beta_electrons" in data["mulliken"]:
                electrons = data["mulliken"]["alpha+beta_electrons"]["charges"]
                anum = data["mulliken"]["alpha+beta_electrons"]["atomic_numbers"]
                out_data["mulliken_electrons"] = electrons
                out_data["mulliken_charges"] = [a-e for a, e in zip(anum, electrons)]
            if "alpha-beta_electrons" in data["mulliken"]:
                out_data["mulliken_spins"] = data["mulliken"]["alpha-beta_electrons"]["charges"]
                out_data["mulliken_spin_total"] = sum(out_data["mulliken_spins"])

        # TODO only save StructureData if cell has changed?

        # add the version and class of parser
        out_data["parser_version"] = str(pkg_version)
        out_data["parser_class"] = str(self.__class__.__name__)
        out_data["ejplugins_version"] = str(ejplugins.__version__)

        return out_data, struct_data, psuccess, perrors

    # pylint: disable=too-many-locals
    def parse_with_retrieved(self, retrieved):
        """
        Parse outputs, store results in database.

        :param retrieved: a dictionary of retrieved nodes, where
          the key is the link name
        :returns: a tuple with two values ``(bool, node_list)``,
          where:

          * ``bool``: variable to tell if the parsing succeeded
          * ``node_list``: list of new nodes to be stored in the db
            (as a list of tuples ``(link_name, node)``)
        """
        node_list = []
        successful = True

        # check calc in parsing state
        self.check_state()

        # Load the input dictionary
        # parameters = self._calc.inp.parameters.get_dict()

        # Look for optional settings input node and potential 'parser_options' dictionary within it
        try:
            settings = self._calc.inp.settings.get_dict()
            parser_opts = settings[self.get_parser_settings_key()]
        except (AttributeError, KeyError):
            settings = {}
            parser_opts = {}

        # Look for optional input structure
        try:
            input_structure = self._calc.inp.structure
        except (AttributeError, KeyError):
            input_structure = None

        # Check that the retrieved folder is there
        out_folder = self.get_folder(retrieved)
        if not out_folder:
            return False, ()

        list_of_files = out_folder.get_folder_list()

        # Check that the main output flie is present
        stdout_file = self._calc._DEFAULT_OUTPUT_FILE  # pylint: disable=protected-access

        if stdout_file not in list_of_files:
            self.logger.error(
                "The standard output file '{}' was not found but is required".format(stdout_file))
            return False, ()

        # store the stdout file as a file node
        # node = DataFactory("singlefile")(file=out_folder.get_abs_path(stdout_file))
        # node_list.append(("output_stdout", node))

        # parse the stdout file and add nodes
        paramdict, structdict, psuccess, perrors = self.parse_stdout(out_folder.get_abs_path(stdout_file), parser_opts)

        if not psuccess:
            successful = False

        if perrors:
            self.logger.warning("the parser raised the following errors:\n{}".format("\n\t".join(perrors)))

        params = DataFactory("parameter")(dict=paramdict)
        node_list.append((self.get_linkname_outparams(), params))

        StructureData = DataFactory('structure')
        # we want to reuse the kinds from the input structure, if available
        if not input_structure:
            struct = StructureData(cell=structdict['cell_vectors'])
            for symbol, ccoord in zip(structdict['symbols'], structdict['ccoords']):
                struct.append_atom(position=ccoord, symbols=symbol)
            struct.set_pbc(structdict["pbc"])
        else:
            # TODO is there any issue with primitive and conventional cells
            # (we are expecting both input and output to be primitive)
            struct = input_structure.copy()
            struct.reset_cell(structdict['cell_vectors'])
            struct.reset_sites_positions(structdict['ccoords'])
        node_list.append((self.get_linkname_outstructure(), struct))

        return successful, node_list
