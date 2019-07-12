"""
A parser to read output from a standard CRYSTAL17 run
"""
import traceback
import warnings
from ase.io import read as ase_read
from aiida.common import exceptions
from aiida.engine import ExitCode
from aiida.orm import Dict
from aiida.parsers.parser import Parser
from aiida.plugins import DataFactory

from aiida_crystal17.gulp.parsers.raw.parse_output_std import parse_file


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
            try:
                result_dict, exit_code = parse_file(
                    handle, parser_class=self.__class__.__name__)
            except Exception:
                traceback.print_exc()
                return self.exit_codes.ERROR_PARSING_STDOUT

        if result_dict["parser_errors"]:
            self.logger.warning(
                "the parser raised the following errors:\n{}".format(
                    "\n\t".join(result_dict["parser_errors"])))
        if result_dict["errors"]:
            self.logger.warning(
                "the calculation raised the following errors:\n{}".format(
                    "\n\t".join(result_dict["errors"])))

        # look a stderr for fortran warnings, etc,
        # e.g. IEEE_INVALID_FLAG IEEE_OVERFLOW_FLAG IEEE_UNDERFLOW_FLAG
        stderr_file = self.node.get_option("output_stderr_file_name")
        if stderr_file in output_folder.list_object_names():
            with output_folder.open(stderr_file) as handle:
                stderr_content = handle.read()
                if stderr_content:
                    self.logger.warning("the calculation stderr file was not empty:")
                    self.logger.warning(stderr_content)
                    result_dict["warnings"].append(stderr_content.strip())

        self.out('results', Dict(dict=result_dict))

        cif_file = self.node.get_option("out_cif_file_name")
        if cif_file not in output_folder.list_object_names():
            self.logger.error("the output cif file is missing")
            if exit_code is not None:
                # if there was already an error identified, then return that
                return self.exit_codes[exit_code]
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

        if self.node.get_option("use_input_kinds"):

            if "structure" not in self.node.inputs:
                self.logger.error("the input structure node is not set")
                if exit_code is not None:
                    # if there was already an error identified, then return that
                    return self.exit_codes[exit_code]
                return self.exit_codes.ERROR_MISSING_INPUT_STRUCTURE

            in_structure = self.node.inputs.structure
            in_atoms = in_structure.get_ase()

            if in_atoms.get_chemical_symbols() != atoms.get_chemical_symbols():
                self.logger.error(
                    "the input and cif structures have different atomic configurations")
                if exit_code is not None:
                    # if there was already an error identified, then return that
                    return self.exit_codes[exit_code]
                return self.exit_codes.ERROR_CIF_INCONSISTENT

            out_structure = in_structure.clone()
            out_structure.set_cell(atoms.cell)
            out_structure.reset_sites_positions(atoms.positions)

        else:
            out_structure = DataFactory('structure')(ase=atoms)

        self.out('structure', out_structure)

        if exit_code is not None:
            return self.exit_codes[exit_code]
        return ExitCode()
