"""
A parser to read output from a CRYSTAL17 DOSS run
"""
import traceback

import numpy as np

from aiida.common import exceptions
from aiida.engine import ExitCode
from aiida.orm import Dict, ArrayData
from aiida.parsers.parser import Parser

from aiida_crystal17.parsers.raw.doss_output_f25 import read_doss_f25_content


class CryDossParser(Parser):
    """
    Parser class for parsing (stdout) output of a standard CRYSTAL17 run
    """
    def parse(self, **kwargs):
        """
        Parse outputs, store results in database.
        """
        try:
            output_folder = self.retrieved
        except exceptions.NotExistent:
            return self.exit_codes.ERROR_NO_RETRIEVED_FOLDER

        output_f25_fname = self.node.get_option("output_f25_fname")
        if output_f25_fname not in output_folder.list_object_names():
            return self.exit_codes.ERROR_OUTPUT_FILE_MISSING

        self.logger.info("parsing file: {}".format(output_f25_fname))

        try:
            with output_folder.open(output_f25_fname) as handle:
                data, arrays = read_doss_f25_content(
                    handle, self.__class__.__name__)
        except Exception:
            traceback.print_exc()
            return self.exit_codes.ERROR_OUTPUT_PARSING

        errors = data.get("errors", [])
        parser_errors = data.get("parser_errors", [])
        if parser_errors:
            self.logger.warning(
                "the parser raised the following errors:\n{}".format(
                    "\n\t".join(parser_errors)))
        if errors:
            self.logger.warning(
                "the calculation raised the following errors:\n{}".format(
                    "\n\t".join(errors)))

        self.out('results', Dict(dict=data))
        if arrays is not None:
            array_data = ArrayData()
            for name, array in arrays.items():
                array_data.set_array(name, np.array(array))
            self.out('arrays', array_data)

        if parser_errors:
            return self.exit_codes.ERROR_OUTPUT_PARSING
        elif errors:
            return self.exit_codes.ERROR_DOSS_RUN

        return ExitCode()
