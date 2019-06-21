"""
A parser to read output from a standard CRYSTAL17 run
"""
import warnings
from ase.io import read as ase_read
from aiida.common import exceptions
from aiida.parsers.parser import Parser
from aiida.plugins import DataFactory

from aiida_crystal17.gulp.parsers.parse_output import parse_output


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


class GulpOptParser(Parser):
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
                handle, parser_class=self.__class__.__name__,
                final=True, optimise=True)

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

        cif_file = self.node.get_option("out_cif_file_name")
        if cif_file not in output_folder.list_object_names():
            if parser_result.exit_code.status != 0:
                # if there was already an error identified, then return that
                return parser_result.exit_code
            return self.exit_codes.ERROR_CIF_FILE_MISSING

        # We do not use this method, since currently different kinds are set for each atom
        # see aiidateam/aiida_core#2942
        # NOTE cif files are read as binary, by default, since aiida-core v1.0.0b3
        # with output_folder.open(cif_file, mode="rb") as handle:
        #     cif = DataFactory('cif')(file=handle)
        # structure = cif.get_structure(converter="ase")

        with warnings.catch_warnings():
            # ase.io.read returns a warnings that can be ignored
            # UserWarning: crystal system 'triclinic' is not interpreted for space group 1.
            # This may result in wrong setting!
            warnings.simplefilter("ignore", UserWarning)
            with output_folder.open(cif_file, mode="r") as handle:
                atoms = ase_read(handle, index=':', format="cif")[-1]
        atoms.set_tags(0)
        structure = DataFactory('structure')(ase=atoms)

        # TODO use kinds from input structure

        self.out('structure', structure)

        return parser_result.exit_code
