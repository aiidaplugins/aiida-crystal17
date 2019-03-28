"""
A parser to read output from a standard CRYSTAL17 run
"""
from aiida.common import exceptions
from aiida.parsers.parser import Parser

from aiida_crystal17.parsers.mainout_parse import parse_mainout


class CryMainParser(Parser):
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
            parser_result = parse_mainout(
                fileobj, parser_class=self.__class__.__name__,
                init_struct=self.node.inputs.structure,
                init_settings=self.node.inputs.symmetry)
            if not parser_result.success:
                fileobj.seek(0)
                self.logger.warning("parsing main output file failed: "
                                    "{}".format(fileobj.read()))

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
        if parser_result.nodes.structure is not None:
            self.out('structure', parser_result.nodes.structure)
        if parser_result.nodes.symmetry is not None:
            self.out('symmetry', parser_result.nodes.symmetry)

        if not parser_result.success:
            return self.exit_codes.ERROR_PARSING_FAILED
