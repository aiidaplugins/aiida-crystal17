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
from aiida_crystal17.gulp.potentials.base import PotentialWriterAbstract, PotentialContent
from aiida_crystal17.validation import load_schema
from aiida_crystal17.gulp.potentials.raw_reaxff import write_gulp_format


class PotentialWriterReaxff(PotentialWriterAbstract):
    """class for creating gulp reaxff type
    inter-atomic potential inputs
    """

    @classmethod
    def get_description(cls):
        return 'ReaxFF potential'

    @classmethod
    def get_schema(cls):
        return load_schema('potential.reaxff.schema.json')

    @classmethod
    def _get_fitting_schema(cls):
        return load_schema('fitting.reaxff.schema.json')

    # pylint: disable=too-many-locals
    def _make_string(self, data, fitting_data=None):
        """write reaxff data in GULP input format

        Parameters
        ----------
        data : dict
            dictionary of data
        species_filter : list[str] or None
            list of atomic symbols to filter by

        Returns
        -------
        str:
            the potential file content
        int:
            number of potential flags for fitting

        """
        return PotentialContent(*write_gulp_format(data, fitting_data=fitting_data))

    # TODO implement `read_existing` method
