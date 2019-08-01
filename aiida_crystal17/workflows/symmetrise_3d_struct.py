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
"""a work flow to symmetrise a structure and compute the symmetry operations"""
import traceback
from aiida.plugins import DataFactory
from aiida.engine import WorkChain, calcfunction
from aiida_crystal17.symmetry import (reset_kind_names, standardize_cell, find_primitive, compute_symmetry_dict)
from aiida_crystal17.validation import validate_against_schema

from aiida.orm.nodes.data.base import to_aiida_type
StructureData = DataFactory('structure')
DictData = DataFactory('dict')
SymmetryData = DataFactory('crystal17.symmetry')


@calcfunction
def standard_structure(structure, settings):
    atol = settings.get_attribute('angle_tolerance', None)
    return standardize_cell(structure, settings['symprec'], atol, to_primitive=False, no_idealize=True)


@calcfunction
def standard_primitive_structure(structure, settings):
    atol = settings.get_attribute('angle_tolerance', None)
    return standardize_cell(structure, settings['symprec'], atol, to_primitive=True, no_idealize=True)


@calcfunction
def standard_primitive_ideal_structure(structure, settings):
    atol = settings.get_attribute('angle_tolerance', None)
    return standardize_cell(structure, settings['symprec'], atol, to_primitive=True, no_idealize=False)


@calcfunction
def standard_ideal_structure(structure, settings):
    atol = settings.get_attribute('angle_tolerance', None)
    return standardize_cell(structure, settings['symprec'], atol, to_primitive=False, no_idealize=False)


@calcfunction
def primitive_structure(structure, settings):
    atol = settings.get_attribute('angle_tolerance', None)
    return find_primitive(structure, settings['symprec'], atol)


@calcfunction
def change_kind_names(structure, settings):
    return reset_kind_names(structure, settings['kind_names'])


@calcfunction
def compute_symmetry(structure, settings):
    atol = settings.get_attribute('angle_tolerance', None)
    data = compute_symmetry_dict(structure, settings['symprec'], atol)
    return SymmetryData(data=data)


@calcfunction
def cif_to_structure(cif):
    return cif.get_structure(converter='ase')


class Symmetrise3DStructure(WorkChain):
    """modify an AiiDa structure instance and compute its symmetry

    Inequivalent atomic sites are dictated by atom kinds
    """

    @classmethod
    def define(cls, spec):
        super(Symmetrise3DStructure, cls).define(spec)
        spec.input('structure', valid_type=StructureData, required=False)
        spec.input('cif', valid_type=DataFactory('cif'), required=False)
        spec.input(
            'settings',
            valid_type=DataFactory('dict'),
            serializer=to_aiida_type,
            required=True,
            validator=cls.validate_settings)

        spec.outline(cls.validate_inputs, cls.compute)

        spec.output('symmetry', valid_type=SymmetryData, required=True)
        spec.output('structure', valid_type=StructureData, required=False)

        spec.exit_code(
            300, 'ERROR_INVALID_INPUT_RESOURCES', message='one of either a structure or cif input must be supplied')
        spec.exit_code(
            301,
            'ERROR_NON_3D_STRUCTURE',
            message='the supplied structure must be 3D (i.e. have all dimensions pbc=True)"')
        spec.exit_code(302, 'ERROR_COMPUTE_OPTIONS', message='idealize can only be used when standardize=True')
        spec.exit_code(
            303, 'ERROR_RESET_KIND_NAMES', message='the kind names supplied are not compatible with the structure')
        spec.exit_code(304, 'ERROR_NEW_STRUCTURE', message='error creating new structure')
        spec.exit_code(305, 'ERROR_COMPUTING_SYMMETRY', message='error computing symmetry operations')

    @classmethod
    def get_settings_schema(cls):
        return {
            '$schema': 'http://json-schema.org/draft-07/schema',
            'type': 'object',
            'required': ['symprec'],
            'properties': {
                'symprec': {
                    'description': ('Length tolerance for symmetry finding: '
                                    '0.01 is fairly strict and works well for properly refined structures'),
                    'default':
                    0.01,
                    'type':
                    'number',
                    'exclusiveMinimum':
                    0
                },
                'angle_tolerance': {
                    'description': 'Angle tolerance for symmetry finding, in the unit of angle degrees',
                    'default': None,
                    'type': ['number', 'null'],
                    'exclusiveMinimum': 0
                },
                'kind_names': {
                    'description': 'a list of kind names, to assign each Site of the StructureData',
                    'type': 'array',
                    'minItems': 1,
                    'items': {
                        'type': 'string'
                    }
                },
                'compute_primitive': {
                    'description': 'whether to convert the structure to its primitive form',
                    'type': 'boolean',
                    'default': False
                },
                'standardize_cell': {
                    'description':
                    ('whether to standardize the structure, see '
                     'https://atztogo.github.io/spglib/definition.html#conventions-of-standardized-unit-cell'),
                    'type':
                    'boolean',
                    'default':
                    False
                },
                'idealize_cell': {
                    'description': ("whether to remove distortions of the unit cell's atomic positions, "
                                    'using obtained symmetry operations'),
                    'type':
                    'boolean',
                    'default':
                    False
                }
            }
        }

    @classmethod
    def validate_settings(cls, settings_data):
        settings_dict = settings_data.get_dict()
        validate_against_schema(settings_dict, cls.get_settings_schema())

    def validate_inputs(self):

        self.ctx.new_structure = False

        if 'structure' in self.inputs:
            if 'cif' in self.inputs:
                return self.exit_codes.ERROR_INVALID_INPUT_RESOURCES
            self.ctx.structure = self.inputs.structure
        elif 'cif' in self.inputs:
            self.ctx.structure = cif_to_structure(self.inputs.cif)
            self.ctx.new_structure = True
        else:
            return self.exit_codes.ERROR_INVALID_INPUT_RESOURCES

        if not all(self.ctx.structure.pbc):
            return self.exit_codes.ERROR_NON_3D_STRUCTURE

        settings_dict = self.inputs.settings.get_dict()
        self.ctx.kind_names = settings_dict.get('kind_names', None)
        self.ctx.compute_primitive = settings_dict.get('compute_primitive', False)
        self.ctx.standardize_cell = settings_dict.get('standardize_cell', False)
        self.ctx.idealize_cell = settings_dict.get('idealize_cell', False)

        if self.ctx.idealize_cell and not self.ctx.standardize_cell:
            return self.exit_codes.ERROR_COMPUTE_OPTIONS

    def compute(self):

        structure = self.ctx.structure

        if self.ctx.kind_names is not None:
            try:
                structure = change_kind_names(structure, self.inputs.settings)
            except AssertionError as err:
                traceback.print_exc()
                self.logger.error('reset_kind_names: {}'.format(err))
                return self.exit_codes.ERROR_RESET_KIND_NAMES
            self.ctx.new_structure = True

        try:
            if self.ctx.standardize_cell:
                if self.ctx.compute_primitive and self.ctx.idealize_cell:
                    structure = standard_primitive_ideal_structure(structure, self.inputs.settings)
                    self.ctx.new_structure = True
                elif self.ctx.compute_primitive:
                    structure = standard_primitive_structure(structure, self.inputs.settings)
                    self.ctx.new_structure = True
                elif self.ctx.idealize_cell:
                    structure = standard_ideal_structure(structure, self.inputs.settings)
                    self.ctx.new_structure = True
                else:
                    structure = standard_structure(structure, self.inputs.settings)
                    self.ctx.new_structure = True
            elif self.ctx.compute_primitive:
                structure = primitive_structure(structure, self.inputs.settings)
                self.ctx.new_structure = True
        except Exception as err:
            traceback.print_exc()
            self.logger.error('structure creation: {}'.format(err))
            return self.exit_codes.ERROR_NEW_STRUCTURE

        if self.ctx.new_structure:
            self.out('structure', structure)

        try:
            symmetry = compute_symmetry(structure, self.inputs.settings)
        except Exception as err:
            traceback.print_exc()
            self.logger.error('symmetry computation: {}'.format(err))
            return self.exit_codes.ERROR_COMPUTING_SYMMETRY

        self.out('symmetry', symmetry)
