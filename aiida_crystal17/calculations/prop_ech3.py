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
from aiida_crystal17.data.gcube import GaussianCube
from aiida_crystal17.validation import validate_against_schema


class CryEch3Calculation(PropAbstractCalculation):
    """AiiDA calculation plugin to run the ``properties`` executable, for 3D charge density (ECH3)."""

    requires_newk = False

    @classmethod
    def validate_parameters(cls, data):
        validate_against_schema(data.get_dict(), "prop.ech3.schema.json")

    @classmethod
    def define(cls, spec):
        super(CryEch3Calculation, cls).define(spec)

        spec.input(
            "metadata.options.output_charge_fname",
            valid_type=str,
            default="DENS_CUBE.DAT",
        )
        spec.input(
            "metadata.options.output_spin_fname",
            valid_type=str,
            default="SPIN_CUBE.DAT",
        )

        spec.input(
            "metadata.options.parser_name", valid_type=str, default="crystal17.ech3"
        )

        spec.exit_code(
            352,
            "ERROR_DENSITY_FILE_MISSING",
            message="parser could not find the output density file",
        )
        spec.exit_code(
            353,
            "ERROR_PARSING_DENSITY_FILE",
            message="error parsing output density file",
        )

        spec.output(
            "charge",
            required=True,
            valid_type=GaussianCube,
            help="The charge density cube",
        )
        spec.output(
            "spin",
            required=False,
            valid_type=GaussianCube,
            help="The spin density cube",
        )

    def create_input_content(self):
        params = self.inputs.parameters.get_dict()
        lines = ["ECH3", str(params["npoints"]), "END"]
        # TODO params for non-periodic dimensions
        return "\n".join(lines)

    def get_retrieve_list(self):
        return [self.metadata.options.stdout_file_name]

    def get_retrieve_temp_list(self):
        return [
            self.metadata.options.output_charge_fname,
            self.metadata.options.output_spin_fname,
        ]
