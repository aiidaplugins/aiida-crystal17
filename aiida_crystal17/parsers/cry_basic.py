"""
A parser to read the main output (stdout) of a standard CRYSTAL17 run
"""
from aiida.parsers.parser import Parser
from aiida.parsers.exceptions import OutputParsingError
from aiida.common.datastructures import calc_states

from aiida.orm import CalculationFactory
CryBasicCalculation = CalculationFactory('crystal17.basic')


class CryBasicParser(Parser):
    """
    Parser class for parsing (stdout) output of a standard CRYSTAL17 run
    """
    def __init__(self, calculation):
        """
        Initialize Parser instance
        """
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

    # pylint: disable=protected-access
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
        from aiida.orm import DataFactory
        from ejplugins.crystal import CrystalOutputPlugin

        success = False
        node_list = []

        # check calc in parsing state
        self.check_state()

        # Check that the retrieved folder is there
        out_folder = self.get_folder(retrieved)
        if not out_folder:
            return success, node_list

        list_of_files = out_folder.get_folder_list()

        # Check the folder content is as expected
        output_files = [self._calc._DEFAULT_OUTPUT_FILE]
        output_links = ['outfile']
        if set(output_files).issubset(list_of_files):
            pass
        else:
            self.logger.error(
                "Not all expected output files {} were found".format(
                    output_files))
            return success, node_list

        # store the main output file
        node = DataFactory("singlefile")(file=out_folder.get_abs_path(output_files[0]))
        node_list.append((output_links[0], node))

        cryparse = CrystalOutputPlugin()
        with open(out_folder.get_abs_path(output_files[0])) as f:
            data = cryparse.read_file(f)

        params = DataFactory("parameter")()
        params.set_dict(data)
        node_list.append(("parameters", params))

        success = True
        return success, node_list
