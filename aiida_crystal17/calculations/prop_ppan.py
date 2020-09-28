#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 Chris Sewell
#
# This file is part of aiida-crystal17.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms and conditions
# of version 3 of the GNU Lesser General Public License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
"""Plugin for running CRYSTAL17 properties computations."""


from aiida_crystal17.calculations.prop_abstract import PropAbstractCalculation
from aiida_crystal17.parsers.raw.prop_inputs import create_rotref_content
from aiida_crystal17.validation import validate_against_schema


class CryPpanCalculation(PropAbstractCalculation):
    """
    AiiDA calculation plugin to run the ``properties`` executable,
    for PPAN (Mulliken population analysis) calculations.
    """

    @classmethod
    def validate_parameters(cls, data):
        dct = data.get_dict()
        validate_against_schema(dct, "prop.rotref.schema.json")

    @classmethod
    def define(cls, spec):
        super(CryPpanCalculation, cls).define(spec)

        spec.input(
            "metadata.options.output_ppan_fname", valid_type=str, default="PPAN.DAT"
        )

        spec.input(
            "metadata.options.parser_name", valid_type=str, default="crystal17.ppan"
        )

        # TODO make dict optional

        spec.exit_code(
            352,
            "ERROR_PPAN_FILE_MISSING",
            message="parser could not find the output PPAN.dat file",
        )
        spec.exit_code(
            353, "ERROR_PARSING_PPAN_FILE", message="error parsing output PPAN.dat file"
        )

    def create_input_content(self):
        dct = self.inputs.parameters.get_dict()
        lines = create_rotref_content(dct)
        lines.append("PPAN")
        lines.append("END")
        return "\n".join(lines)

    def get_retrieve_list(self):
        return [
            self.metadata.options.stdout_file_name,
            self.metadata.options.output_ppan_fname,
        ]

    def get_retrieve_temp_list(self):
        return []
