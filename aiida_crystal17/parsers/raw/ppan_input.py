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
import numpy as np

from aiida_crystal17.validation import validate_against_schema


def create_ppan_content(params, validate=True):
    """create the contents of a ppan.d3 input file

    Parameters
    ----------
    params : dict
    validate : bool
        Validate the parameters against the JSON schema

    Returns
    -------
    list[str]

    """
    if validate:
        validate_against_schema(params, 'prop.ppan.schema.json')

    lines = []

    if 'ROTREF' in params:
        if 'MATRIX' in params['ROTREF']:
            if not _test_unitary(params['ROTREF']['MATRIX']):
                raise ValueError('The ROTREF matrix must be unitary: {}'.format(params['ROTREF']['MATRIX']))
            lines.extend([
                'ROTREF',
                'MATRIX',
            ])
            for row in params['ROTREF']['MATRIX']:
                lines.append('{0:.6f} {1:.6f} {2:.6f}'.format(*row))
        if 'ATOMS' in params['ROTREF']:
            lines.extend([
                'ROTREF',
                'ATOMS',
            ])
            for row in params['ROTREF']['ATOMS']:
                lines.append('{0}'.format(row[0]))
                lines.append('{0} {1} {2}'.format(*row[1:]))

    lines.append('PPAN')
    lines.append('END')
    return lines


def _test_unitary(matrix):
    """Test whether a matrix is unitary (inverse == conjugate transpose)."""
    m = np.array(matrix)
    return np.allclose(np.eye(len(m)), m.dot(m.T.conj()))
