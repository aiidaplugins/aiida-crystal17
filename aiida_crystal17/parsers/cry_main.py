"""
A parser to read output from a standard CRYSTAL17 run
"""
from aiida.common import exceptions
from aiida.parsers.parser import Parser
from aiida.plugins import CalculationFactory

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

        node_list = []
        successful = True

        # Look for optional input structure
        try:
            input_structure = self.node.incoming.structure
        except (AttributeError, KeyError):
            input_structure = None

        # Look for optional structure settings input node
        try:
            input_settings = self.node.incoming.settings
        except (AttributeError, KeyError):
            input_settings = None

        # Check that the main output file is present
        mainout_file = self.node.get_option("output_main_file_name")  # pylint: disable=protected-access

        if mainout_file not in output_folder.list_object_names():
            return self.exit_codes.ERROR_OUTPUT_FILE_MISSING

        # parse the stdout file and add nodes
        self.logger.info("parsing main out file")
        with output_folder.open(mainout_file) as fileobj:
            psuccess, output_nodes = parse_mainout(
                fileobj,
                parser_class=self.__class__.__name__,
                init_struct=input_structure,
                init_settings=input_settings)

        if not psuccess:
            successful = False

        outparams = output_nodes.pop("parameters")
        if outparams.get_attribute("errors", None) is None:
            perrors = outparams.get_attribute("errors")
            if perrors:
                self.logger.warning(
                    "the parser raised the following errors:\n{}".format(
                        "\n\t".join(perrors)))
        if outparams.get_attribute("parser_warnings", None) is None:
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
