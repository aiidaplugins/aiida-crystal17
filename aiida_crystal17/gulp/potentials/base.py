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
from collections import namedtuple
import copy
import re

from aiida_crystal17.validation import validate_against_schema
from aiida_crystal17.gulp.potentials.common import filter_by_species

PotentialContent = namedtuple('PotentialContent', ['content', 'number_of_flags', 'number_flagged'])
"""used for returning the content creation for a potential

Parameters
----------
content: str
    the potential file content
number_of_flags: int
    number of potential flags for fitting
number_flagged: int
    number of variables flagged to fit

"""

RE_SYMBOL = '([A-Z][a-z]?)'
RE_SYMBOL_TYPE = '([A-Z][a-z]?)\\s+(\\bc\\b|\\bcore\\b|\\bs\\b|\\bshell\\b)'
# take from version 4.5.3
OPTION_TERMS = (
    '3coulomb', 'absdipolemoment', 'absolute_coordinates', 'accelerations', 'accuracy', 'ala_cutoff', 'ala_disp',
    'ala_processors', 'ala_shrink', 'and', 'anisotropic_pressure', 'ashift', 'atomab', 'aver', 'axilrod-teller',
    'bacoscross', 'bacross', 'bagcross', 'balcross', 'baskes', 'bbar', 'bcoscross', 'bcross', 'becke_johnson_c6',
    'best', 'blocksize', 'boattractive', 'bocharge', 'bocnswitch', 'bocntolerance', 'bocoordination', 'bondtype',
    'borepulsive', 'bornq', 'boselfenergy', 'both', 'botwobody', 'box', 'brenner', 'bsm', 'bspline', 'buck4',
    'buckingham', 'buffered_lj', 'bulk_modulus', 'cartesian', 'catomic_stress', 'caver', 'cell', 'cellstrain', 'centre',
    'cfaver', 'cfm_fermi', 'cfm_gaussian', 'cfm_harmonic', 'cfm_power', 'charge', 'chemshell_mode', 'cmm',
    'configurations', 'connect', 'constrain', 'contents', 'coordno', 'cosh-spring', 'cosmoframe', 'cosmoshape',
    'coulomb_subtract', 'covalent', 'covexp', 'crossover', 'current_time', 'cutd', 'cutmany', 'cutp', 'cuts', 'cv',
    'cvec', 'cwolf', 'damped_dispersion', 'default_weight', 'deflist', 'delay_field', 'delay_force', 'delf', 'delta',
    'dhkl', 'discrete', 'dispersion', 'ditto', 'dmaximum', 'dminimum', 'dump', 'eam_alloy', 'eam_density',
    'eam_functional', 'eam_potential_shift', 'edip_accuracy', 'edip_coordination', 'edip_threebody', 'edip_twobody',
    'edip_zmax', 'einstein', 'elastic', 'electronegativity', 'element', 'end_field', 'end_force', 'energy', 'ensemble',
    'entropy', 'epsilon/sigma', 'equatorial', 'equilibration', 'erferfc', 'erfpot', 'erongi', 'ewaldrealradius', 'exp2',
    'exponential_three_body', 'exppowers', 'external_force', 'external_potential', 'extracutoff', 'factor', 'fangle',
    'fbond', 'fc_supercell', 'fcartesian', 'fcell', 'fenergy', 'fermi-dirac', 'ffractional', 'field',
    'finite', 'fix_atom', 'forceconstant', 'fractional', 'frequency', 'frqtol', 'ftol', 'fvectors', 'g3coulomb',
    'gamma_angular_steps', 'gamma_direction_of_approach', 'gastdamping', 'gastiter', 'gastparam', 'gasttol',
    'gcmcexistingmolecules', 'gcmcmolecule', 'gcmcspecies', 'gcoulomb', 'gdcrit', 'general', 'genetic', 'gexp',
    'ghost_supercell', 'gmax', 'gradients', 'grid', 'grimme_c6', 'gtol', 'harmonic', 'hfdlc', 'hfrefractive_index',
    'high-fq', 'hydrogen-bond', 'igauss', 'ignore', 'impurity', 'include', 'index_k', 'initial_coordinates',
    'intconserved', 'integrator', 'inter', 'interstitial', 'intra', 'inversion', 'ionic', 'iterations', 'keyword',
    'kim_model', 'kpoints', 'lbfgs_order', 'lennard', 'library', 'lin3', 'line', 'ljbuffered', 'lorentzian_tolerance',
    'lowest_mode', 'manybody', 'marvin', 'mass', 'maths', 'matrix_format', 'maxcyc', 'maximise', 'maximum',
    'mcchemicalpotential', 'mccreate', 'mcdestroy', 'mclowest', 'mcmaxdisplacement', 'mcmaxrotation', 'mcmaxstrain',
    'mcmeans', 'mcmove', 'mcoutfreq', 'mcrotate', 'mcsample', 'mcstep', 'mcstrain', 'mcswap', 'mctrial', 'mcvolume',
    'mdarchive', 'mdmaxtemp', 'mdmaxvolume', 'meam_density', 'meam_functional', 'meam_rhotype', 'meam_screening',
    'mei-davenport', 'mincell', 'minimum', 'mm3angle', 'mm3buck', 'mm3stretch', 'mode', 'mode2a', 'momentum_correct',
    'monopoleq', 'morse', 'move_2a_to_1', 'murrell-mottram', 'mutation', 'name', 'nebiterations', 'nebrandom',
    'nebreplica', 'nebspring', 'nebtangent', 'nebtolerance', 'nmr', 'nobond', 'observables', 'odirection', 'omega',
    'omega_af', 'omega_damping', 'origin', 'outofplane', 'output', 'p_flexible', 'p_isotropic', 'parallel', 'pcell',
    'pdf', 'pfinite', 'pfractional', 'piezoelectric', 'plane_lj', 'plumed_input', 'plumed_log', 'pointsperatom',
    'poisson_ratio', 'polarisability', 'polynomial', 'potential', 'potential_interpolation', 'potgrid', 'potsites',
    'pressure', 'print', 'production', 'project_dos', 'pvector', 'qelectronegativity', 'qeqiter', 'qeqradius', 'qeqtol',
    'qerfc', 'qgrid', 'qincrement', 'qiterations', 'qmmm', 'qonsas', 'qoverr2', 'qreaxff', 'qsolver', 'qtaper', 'qwolf',
    'radial_force', 'random', 'rangeforsmooth', 'rbins', 'rcartesian', 'rcell', 'rcspatial', 'rdirection', 'reaction',
    'reaxff0_bond', 'reaxff0_lonepair', 'reaxff0_over', 'reaxff0_penalty', 'reaxff0_torsion', 'reaxff0_valence',
    'reaxff0_vdw', 'reaxff1_angle', 'reaxff1_include_under', 'reaxff1_lonepair', 'reaxff1_morse', 'reaxff1_over',
    'reaxff1_radii', 'reaxff1_under', 'reaxff1_valence', 'reaxff2_bo', 'reaxff2_bond', 'reaxff2_morse', 'reaxff2_over',
    'reaxff2_pen', 'reaxff3_angle', 'reaxff3_conjugation', 'reaxff3_hbond', 'reaxff3_pen', 'reaxff4_torsion',
    'reaxff_chi', 'reaxff_gamma', 'reaxff_mu', 'reaxff_q0', 'reaxff_qshell', 'reaxff_r12', 'reaxfftol', 'region_1',
    'reldef', 'reperfc', 'resetvectors', 'rfractional', 'rmax', 'rspeed', 'rtol', 'ryckaert', 'rydberg', 'sample',
    'sasexclude', 'sasparticles', 'sbulkenergy', 'scale', 'scan_cell', 'scell', 'scmaxsearch', 'sdlc', 'seed',
    'segmentsperatom', 'sfinite', 'sfractional', 'shear_modulus', 'shellmass', 'shift', 'shrink', 'siginc', 'size',
    'slater', 'slower', 'smelectronegativity', 'solventepsilon', 'solventradius', 'solventrmax', 'spacegroup',
    'species', 'spline', 'split', 'spring', 'sqomega', 'squaredharmonic', 'srefractive_index', 'sregion2', 'srglue',
    'sshift', 'start', 'static', 'stepmx', 'stop', 'strain_derivative', 'stress', 'supercell', 'svectors', 'sw2',
    'sw2jb', 'sw3', 'sw3jb', 'switch_minimiser', 'switch_stepmx', 'symbol', 'symmetry_cell', 'symmetry_number',
    'symmetry_operator', 'synciterations', 'syncsteps', 'synctolerance', 'tau_barostat', 'tau_thermostat',
    'td_external_force', 'td_field', 'temperature', 'terse', 'tether', 'three-body', 'threshold', 'time', 'timestep',
    'title', 'torangle', 'torcosangle', 'torexp', 'torharm', 'torsion', 'tortaper', 'totalenergy', 'tournament', 'tpxo',
    'translate', 'tscale', 'tsuneyuki', 'ttol', 'twist', 'uff1', 'uff3', 'uff4', 'uff_bondorder', 'uffoop', 'unfreeze',
    'unique', 'units', 'update', 'urey-bradley', 'vacancy', 'variables', 'vbo_twobody', 'vdw', 'vectors', 'velocities',
    'volume', 'weight', 'wmax', 'wmin', 'write', 'xangleangle', 'xcosangleangle', 'xoutofplane', 'xtol',
    'youngs_modulus', 'zbl')

# Note: 'static' should actually be 'static dielectric', and 'high-fq' 'high-fq dielectric'


class PotentialWriterAbstract(object):
    """abstract class for creating gulp inter-atomic potential inputs,
    from a data dictionary.

    sub-classes should override the
    ``get_description``, ``get_schema``, ``_make_string`` and ``read_exising`` methods

    """
    _schema = None
    _fitting_schema = None

    @classmethod
    def get_description(cls):
        """return description of the potential type"""
        return ''

    @classmethod
    def get_schema(cls):
        """return the schema to validate input data

        Returns
        -------
        dict

        """
        # only load it once
        if cls._schema is None:
            cls._schema = cls._get_schema()
        return copy.deepcopy(cls._schema)

    @classmethod
    def _get_schema(cls):
        """return the schema to validate input data
        should be overridden by subclass

        Returns
        -------
        dict

        """
        raise NotImplementedError

    @classmethod
    def get_fitting_schema(cls):
        """return the schema to validate input data

        Returns
        -------
        dict

        """
        # only load it once
        if cls._fitting_schema is None:
            cls._fitting_schema = cls._get_fitting_schema()
        return copy.deepcopy(cls._fitting_schema)

    @classmethod
    def _get_fitting_schema(cls):
        """return the schema to validate input data
        should be overridden by subclass

        Returns
        -------
        dict

        """
        raise NotImplementedError

    def _make_string(self, data, fitting_data=None):
        """create string for inter-atomic potential section for main.gin file

        Parameters
        ----------
        data : dict
            dictionary of data
        species_filter : list[str] or None
            list of atomic symbols to filter by

        Returns
        -------
        PotentialContent

        """
        raise NotImplementedError

    def create_content(self, data, species_filter=None, fitting_data=None):
        """create string for inter-atomic potential section for main.gin file

        Parameters
        ----------
        data : dict
            dictionary of data required to create potential
        species_filter : list[str] or None
            list of atomic symbols to filter by
        fitting_data: dict or None
            a dictionary specifying which variables to flag for optimisation,
            of the form; {<type>: {<index>: [variable1, ...]}}
            if None, no flags will be added

        Returns
        -------
        PotentialContent

        """
        # validate data
        schema = self.get_schema()
        validate_against_schema(data, schema)
        # test that e.g. '1-2' and '2-1' aren't present
        if '2body' in data:
            bonds = []
            for indices in data['2body']:
                index_set = set(indices.split('-'))
                if index_set in bonds:
                    raise AssertionError('both {0}-{1} and {1}-{0} 2body keys exist in the data'.format(*index_set))
                bonds.append(index_set)
        # test that e.g. '1-2-3' and '3-2-1' aren't present (2 is the pivot atom)
        if '3body' in data:
            angles = []
            for indices in data['3body']:
                i1, i2, i3 = indices.split('-')
                if (i1, i2, i3) in angles:
                    raise AssertionError('both {0}-{1}-{2} and {2}-{1}-{0} 3body keys exist in the data'.format(
                        i1, i2, i3))
                angles.append((i1, i2, i3))
                angles.append((i3, i2, i1))

        if species_filter is not None:
            data = filter_by_species(data, species_filter)

        # validate fitting data
        if fitting_data is not None:
            fit_schema = self.get_fitting_schema()
            validate_against_schema(fitting_data, fit_schema)
            if species_filter is not None:
                fitting_data = filter_by_species(fitting_data, species_filter)
            if fitting_data['species'] != data['species']:
                raise AssertionError('the fitting data species ({}) must be equal to the data species ({})'.format(
                    fitting_data['species'], data['species']))
            # TODO same checks as main data and possibly switch 2body/3body indices to line up with those for main data

        return self._make_string(data, fitting_data=fitting_data)

    def read_exising(self, lines):
        """read an existing potential file

        NOTE: this should be overriden by the subclass

        Parameters
        ----------
        lines : list[str]

        Returns
        -------
        dict
            the potential data

        Raises
        ------
        IOError
            on parsing failure

        """
        raise NotImplementedError

    @staticmethod
    def read_atom_section(lines, lineno, number_atoms, global_args=None):
        """read a section of a potential file, e.g.

        ::

            H core  He shell 1.00000000E+00 2.00000000E+00 12.00000 0 1
            H B 3.00000000E+00 4.00000000E+00 0.00 12.00000 1 0

        Parameters
        ----------
        lines : list[str]
            the lines in the file
        lineno : int
            the current line number, should be the line below the option line
        number_atoms : int
            the number of interacting atoms expected
        global_args : dict
            additional arguments to add to the result of each line

        Returns
        -------
        int: lineno
            the final line of the section
        set: species_set
            a set of species identified in the section
        dict: results
            {tuple[species]: {"values": str, "global": global_args}}

        Raises
        ------
        IOError
            If a parsing error occurs

        """
        results = {}
        symbol_set = set()

        while lineno < len(lines):
            line = lines[lineno]
            first_term = line.strip().split()[0]
            # ignore comment lines
            if first_term == '#':
                lineno += 1
                continue
            # break if we find the next section
            if first_term in OPTION_TERMS:
                break

            # TODO ignore comments at end of line

            # check for breaking lines
            if line.strip().endswith(' &'):
                lineno += 1
                line = line.strip()[:-2] + ' ' + lines[lineno].strip()
            # check for lines containing both atom symbols and types (core/shell)
            match_sym_type = re.findall(
                '^{}\\s+(.+)\\s*$'.format('\\s+'.join([RE_SYMBOL_TYPE for _ in range(number_atoms)])), line.strip())
            # check for lines containing only atom symbols (assume types to be core)
            match_sym = re.findall('^{}\\s+(.+)\\s*$'.format('\\s+'.join([RE_SYMBOL for _ in range(number_atoms)])),
                                   line.strip())
            # TODO also match atomic numbers (and mixed type / no type)
            if match_sym_type:
                result = list(match_sym_type[0])
                index = []
                for _ in range(number_atoms):
                    symbol = result[0]
                    stype = {'c': 'core', 's': 'shell'}[result[1][0]]
                    index.append('{} {}'.format(symbol, stype))
                    result = result[2:]
                results[tuple(index)] = {'values': result[0], 'global': global_args}
                symbol_set.update(index)
            elif match_sym:
                result = list(match_sym[0])
                index = []
                for _ in range(number_atoms):
                    symbol = result[0]
                    index.append('{} {}'.format(symbol, 'core'))
                    result = result[1:]
                results[tuple(index)] = {'values': result[0], 'global': global_args}
                symbol_set.update(index)
            else:
                raise IOError('expected line to be of form '
                              "'symbol1 <type> symbol2 <type> ... variables': {}".format(line))

            lineno += 1
        return lineno - 1, symbol_set, results
