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
"""
parse the main output file and create the required output nodes
"""
from collections import Mapping
import traceback
from aiida_crystal17.symmetry import convert_structure
from aiida.plugins import DataFactory
from aiida_crystal17 import __version__
from aiida_crystal17.calculations.cry_main import CryMainCalculation
from aiida_crystal17.parsers.raw import crystal_stdout


class OutputNodes(Mapping):
    """
    a mapping of output nodes, with attribute access
    """

    def __init__(self):
        self._dict = {'results': None, 'structure': None, 'symmetry': None}

    def _get_results(self):
        return self._dict['results']

    def _set_results(self, value):
        assert isinstance(value, DataFactory('dict'))
        self._dict['results'] = value

    results = property(_get_results, _set_results)

    def _get_structure(self):
        return self._dict['structure']

    def _set_structure(self, value):
        assert isinstance(value, DataFactory('structure'))
        self._dict['structure'] = value

    structure = property(_get_structure, _set_structure)

    def _get_symmetry(self):
        return self._dict['symmetry']

    def _set_symmetry(self, value):
        assert isinstance(value, DataFactory('crystal17.symmetry'))
        self._dict['symmetry'] = value

    symmetry = property(_get_symmetry, _set_symmetry)

    def __getitem__(self, value):
        out = self._dict[value]
        if out is None:
            raise KeyError(value)
        return out

    def __iter__(self):
        for key, val in self._dict.items():
            if val is not None:
                yield key

    def __len__(self):
        len([k for k, v in self._dict.items() if v is not None])


class ParserResult(object):

    def __init__(self):
        self.exit_code = None
        self.nodes = OutputNodes()


# pylint: disable=too-many-locals,too-many-statements
def parse_main_out(fileobj, parser_class, init_struct=None, init_settings=None):
    """ parse the main output file and create the required output nodes

    :param fileobj: handle to main output file
    :param parser_class: a string denoting the parser class
    :param init_struct: input structure
    :param init_settings: input structure settings

    :return parse_result

    """
    parser_result = ParserResult()
    exit_codes = CryMainCalculation.exit_codes

    results_data = {
        'parser_version': str(__version__),
        'parser_class': str(parser_class),
        'parser_errors': [],
        'parser_warnings': [],
        'parser_exceptions': [],
        'errors': [],
        'warnings': []
    }

    try:
        data = crystal_stdout.read_crystal_stdout(fileobj.read())
    except IOError as err:
        # should never happen
        traceback.print_exc()
        parser_result.exit_code = exit_codes.ERROR_PARSING_STDOUT
        results_data['parser_exceptions'].append('Error parsing CRYSTAL 17 main output: {0}'.format(err))
        parser_result.nodes.results = DataFactory('dict')(dict=results_data)
        return parser_result

    # TODO could also read .gui file for definitive final (primitive) geometry,
    # with symmetries
    # TODO could also read .SCFLOG, to get scf output for each opt step
    # TODO could also read files in .optstory folder,
    # to get (primitive) geometries (+ symmetries) for each opt step
    # Note the above files are only available for optimisation runs

    results_data.update(data)

    # TODO handle errors
    try:
        final_info = crystal_stdout.extract_final_info(data)
    except ValueError:
        traceback.print_exc()
        final_info = {}

    results_data.pop('initial_geometry', None)
    initial_scf = results_data.pop('initial_scf', None)
    optimisation = results_data.pop('optimisation', None)
    results_data.pop('final_geometry', None)
    mulliken_analysis = results_data.pop('mulliken', None)
    stdout_exit_code = results_data.pop('exit_code')

    if initial_scf is not None:
        results_data['scf_iterations'] = len(initial_scf.get('cycles', []))
    if optimisation is not None:
        # the first optimisation step is the initial scf
        results_data['opt_iterations'] = len(optimisation) + 1

    # TODO read separate energy contributions
    results_data['energy'] = final_info.get('energy', None)
    # we include this for back compatibility
    results_data['energy_units'] = results_data.get('units', {}).get('energy', 'eV')

    # TODO read from fort.34 (initial and final) file and check consistency of final cell/symmops
    structure = _extract_structure(final_info, init_struct, results_data, parser_result, exit_codes)
    if structure is not None and (optimisation is not None or not init_struct):
        parser_result.nodes.structure = structure

    _extract_symmetry(final_info, init_settings, results_data, parser_result, exit_codes)

    if mulliken_analysis is not None:
        _extract_mulliken(mulliken_analysis, results_data)

    parser_result.nodes.results = DataFactory('dict')(dict=results_data)

    if stdout_exit_code:
        parser_result.exit_code = exit_codes[stdout_exit_code]

    return parser_result


def _extract_symmetry(final_data, init_settings, param_data, parser_result, exit_codes):
    """extract symmetry operations"""

    if 'primitive_symmops' not in final_data:
        param_data['parser_errors'].append('primitive symmops were not found in the output file')
        parser_result.exit_code = exit_codes.ERROR_SYMMETRY_NOT_FOUND
        return

    if init_settings:
        if init_settings.num_symops != len(final_data['primitive_symmops']):
            param_data['parser_errors'].append('number of symops different')
            parser_result.exit_code = exit_codes.ERROR_SYMMETRY_INCONSISTENCY
        # differences = init_settings.compare_operations(
        #     final_data["primitive_symmops"])
        # if differences:
        #     param_data["parser_errors"].append(
        #         "output symmetry operations were not the same as "
        #         "those input: {}".format(differences))
        #     parser_result.success = False
    else:
        from aiida.plugins import DataFactory
        symmetry_data_cls = DataFactory('crystal17.symmetry')
        data_dict = {'operations': final_data['primitive_symmops'], 'basis': 'fractional', 'hall_number': None}
        parser_result.nodes.symmetry = symmetry_data_cls(data=data_dict)


def _extract_structure(final_data, init_struct, results_data, parser_result, exit_codes):
    """create a StructureData object of the final configuration"""
    if 'primitive_cell' not in final_data:
        results_data['parser_errors'].append('final primitive cell was not found in the output file')
        parser_result.exit_code = exit_codes.ERROR_PARSING_STDOUT
        return None

    cell_data = final_data['primitive_cell']

    results_data['number_of_atoms'] = len(cell_data['atomic_numbers'])
    results_data['number_of_assymetric'] = sum(cell_data['assymetric'])

    cell_vectors = []
    for n in 'a b c'.split():
        cell_vectors.append(cell_data['cell_vectors'][n])

    # we want to reuse the kinds from the input structure, if available
    if not init_struct:
        results_data['parser_warnings'].append('no initial structure available, creating new kinds for atoms')
        kinds = None
    else:
        kinds = [init_struct.get_kind(n) for n in init_struct.get_site_kindnames()]
    structure = convert_structure({
        'lattice': cell_vectors,
        'pbc': cell_data['pbc'],
        'symbols': cell_data['symbols'],
        'ccoords': cell_data['ccoords'],
        'kinds': kinds
    }, 'aiida')
    results_data['volume'] = structure.get_cell_volume()
    return structure


def _extract_mulliken(data, param_data):
    """extract mulliken electronic charge partition data"""
    if 'alpha+beta_electrons' in data:
        electrons = data['alpha+beta_electrons']['charges']
        anum = data['alpha+beta_electrons']['atomic_numbers']
        param_data['mulliken_electrons'] = electrons
        param_data['mulliken_charges'] = [a - e for a, e in zip(anum, electrons)]
    if 'alpha-beta_electrons' in data:
        param_data['mulliken_spins'] = data['alpha-beta_electrons']['charges']
        param_data['mulliken_spin_total'] = sum(param_data['mulliken_spins'])
