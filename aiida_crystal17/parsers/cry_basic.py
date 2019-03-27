"""
A parser to read output from a standard CRYSTAL17 run
"""
from aiida.common import exceptions
from aiida.parsers.parser import Parser
from aiida.plugins import CalculationFactory

from aiida_crystal17.parsers.mainout_parse import parse_mainout


class CryBasicParser(Parser):
    """
    Parser class for parsing (stdout) output of a standard CRYSTAL17 run
    """

    def parse(self, retrieved_temporary_folder, **kwargs):
        """
        Parse outputs, store results in database.
        """
        try:
            output_folder = self.retrieved
        except exceptions.NotExistent:
            return self.exit_codes.ERROR_NO_RETRIEVED_FOLDER

        mainout_file = self.node.get_option("output_main_file_name")
        if mainout_file not in output_folder.list_object_names():
            return self.exit_codes.ERROR_OUTPUT_FILE_MISSING

        # parse the stdout file and add nodes
        self.logger.info("parsing main out file")
        with output_folder.open(mainout_file) as fileobj:
            psuccess, output_nodes = parse_mainout(
                fileobj, parser_class=self.__class__.__name__)

        outparams = output_nodes.pop("parameters")
        if outparams.get_attribute("errors"):
            perrors = outparams.get_attribute("errors")
            if perrors:
                self.logger.warning(
                    "the parser raised the following errors:\n{}".format(
                        "\n\t".join(perrors)))
        if outparams.get_attribute("parser_warnings"):
            pwarns = outparams.get_attribute("parser_warnings")
            if pwarns:
                self.logger.warning(
                    "the parser raised the following errors:\n{}".format(
                        "\n\t".join(pwarns)))

        self.out('results', outparams)
        if "structure" in output_nodes:
            self.out('structure', output_nodes.pop("structure"))
        if "settings" in output_nodes:
            self.out('symmetry', output_nodes.pop("settings"))

        if not psuccess:
            return self.exit_codes.ERROR_PARSING_FAILED
