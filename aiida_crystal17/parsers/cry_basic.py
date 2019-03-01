"""
A parser to read output from a standard CRYSTAL17 run
"""
from aiida.parsers.parser import Parser
from aiida.common.exceptions import OutputParsingError
from aiida.common.datastructures import calc_states
from aiida.orm import CalculationFactory

from aiida_crystal17.parsers.mainout_parse import parse_mainout


class CryBasicParser(Parser):
    """
    Parser class for parsing (stdout) output of a standard CRYSTAL17 run
    """

    def __init__(self, calculation):
        """
        Initialize Parser instance
        """
        CryBasicCalculation = CalculationFactory('crystal17.basic')
        CryMainCalculation = CalculationFactory('crystal17.main')
        # check for valid input
        if not isinstance(calculation,
                          (CryBasicCalculation, CryMainCalculation)):
            raise OutputParsingError(
                "Can only parse CryBasicCalculation or CryMainCalculation")

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

    # def get_parser_settings_key(self):
    #     """
    #     Return the name of the key to be used in the calculation settings, that
    #     contains the dictionary with the parser_options
    #     """
    #     return 'parser_options'

    @classmethod
    def get_linkname_outstructure(cls):
        """
        Returns the name of the link to the output_structure
        Node exists if positions or cell changed.
        """
        return 'output_structure'

    @classmethod
    def get_linkname_outsettings(cls):
        """
        Returns the name of the link to the output_structure
        Node exists if positions or cell changed.
        """
        return 'output_settings'

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

        # Look for optional input structure
        try:
            input_structure = self._calc.inp.structure
        except (AttributeError, KeyError):
            input_structure = None

        # Look for optional structure settings input node
        try:
            input_settings = self._calc.inp.settings
        except (AttributeError, KeyError):
            input_settings = None

        # Check that the retrieved folder is there
        out_folder = self.get_folder(retrieved)
        if not out_folder:
            return False, ()

        list_of_files = out_folder.get_folder_list()

        # Check that the main output file is present
        mainout_file = self._calc._DEFAULT_OUTPUT_FILE  # pylint: disable=protected-access

        if mainout_file not in list_of_files:
            self.logger.error(
                "The standard output file '{}' was not found but is required".
                format(mainout_file))
            return False, ()

        # parse the stdout file and add nodes
        self.logger.info("parsing main out file")
        psuccess, output_nodes = parse_mainout(
            out_folder.get_abs_path(mainout_file),
            parser_class=self.__class__.__name__,
            init_struct=input_structure,
            init_settings=input_settings)

        if not psuccess:
            successful = False

        outparams = output_nodes.pop("parameters")
        if "errors" in outparams.get_attrs():
            perrors = outparams.get_attribute("errors")
            if perrors:
                self.logger.warning(
                    "the parser raised the following errors:\n{}".format(
                        "\n\t".join(perrors)))
        if "parser_warnings" in outparams.get_attrs():
            pwarns = outparams.get_attribute("parser_warnings")
            if pwarns:
                self.logger.warning(
                    "the parser raised the following errors:\n{}".format(
                        "\n\t".join(pwarns)))

        node_list.append((self.get_linkname_outparams(), outparams))
        if "settings" in output_nodes:
            node_list.append((self.get_linkname_outsettings(),
                              output_nodes.pop("settings")))
        if "structure" in output_nodes:
            node_list.append((self.get_linkname_outstructure(),
                              output_nodes.pop("structure")))
        if output_nodes:
            self.logger.warning("unknown key(s) in output_nodes: {}".format(
                list(output_nodes.keys())))
            successful = False

        return successful, node_list
