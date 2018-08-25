"""
A parser to read the main output (stdout) of a standard CRYSTAL17 run
"""
from aiida.parsers.parser import Parser
from aiida.parsers.exceptions import OutputParsingError

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
        super(CryBasicParser, self).__init__(calculation)

        # check for valid input
        if not isinstance(calculation, CryBasicCalculation):
            raise OutputParsingError("Can only parse CryBasicCalculation")

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
        from aiida.orm.data.singlefile import SinglefileData
        success = False
        node_list = []

        # Check that the retrieved folder is there
        try:
            out_folder = retrieved[self._calc._get_linkname_retrieved()]
        except KeyError:
            self.logger.error("No retrieved folder found")
            return success, node_list

        # Check the folder content is as expected
        list_of_files = out_folder.get_folder_list()
        output_files = [self._calc._DEFAULT_OUTPUT_FILE]
        output_links = ['crystal17.basic']
        # Note: set(A) <= set(B) checks whether A is a subset
        if set(output_files) <= set(list_of_files):
            pass
        else:
            self.logger.error(
                "Not all expected output files {} were found".format(
                    output_files))

        # Use something like this to loop over multiple output files
        for fname, link in list(zip(output_files, output_links)):

            node = SinglefileData(file=out_folder.get_abs_path(fname))
            node_list.append((link, node))

        success = True
        return success, node_list
