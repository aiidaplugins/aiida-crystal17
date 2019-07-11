"""
A parser to read output from a standard CRYSTAL17 run
"""
from aiida.common import exceptions
from aiida.parsers.parser import Parser

from aiida_crystal17.gulp.parsers.raw.parse_output import parse_output


class GulpSingleParser(Parser):
    """
    Parser class for parsing output of a GULP single point energy calculation
    """

    def parse(self, **kwargs):
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

        # parse the main output file and add nodes
        self.logger.info("parsing main out file")
        with output_folder.open(mainout_file) as handle:
            parser_result = parse_output(
                handle, parser_class=self.__class__.__name__, final=False)

        errors = parser_result.nodes.results.get_attribute("errors")
        parser_errors = parser_result.nodes.results.get_attribute(
            "parser_errors")
        if parser_errors:
            self.logger.warning(
                "the parser raised the following errors:\n{}".format(
                    "\n\t".join(parser_errors)))
        if errors:
            self.logger.warning(
                "the calculation raised the following errors:\n{}".format(
                    "\n\t".join(errors)))

        self.out('results', parser_result.nodes.results)

        return parser_result.exit_code
