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
Plugin to create a CRYSTAL17 output file,
from input files created via data nodes
"""
import os
import six

from aiida.common.exceptions import InputValidationError
from aiida.orm import Code, RemoteData, StructureData, TrajectoryData
from aiida.plugins import DataFactory

from aiida_crystal17.calculations.cry_abstract import CryAbstractCalculation
from aiida_crystal17.parsers.raw.parse_fort34 import gui_file_write
from aiida_crystal17.parsers.raw.inputd12_write import (write_input, create_atom_properties)


class CryMainCalculation(CryAbstractCalculation):
    """
    AiiDA calculation plugin to run the runcry17 executable,
    by supplying aiida nodes, with data sufficient to create the
    .d12 input file and .gui file
    """

    @classmethod
    def define(cls, spec):

        super(CryMainCalculation, cls).define(spec)

        spec.input(
            'parameters',
            valid_type=DataFactory('crystal17.parameters'),
            required=True,
            serializer=lambda x: DataFactory('crystal17.parameters')(data=x),
            help='the input parameters to create the .d12 file content.')
        spec.input(
            'structure',
            valid_type=StructureData,
            required=True,
            help='structure used to construct the input fort.34 (gui) file')
        spec.input(
            'symmetry',
            valid_type=DataFactory('crystal17.symmetry'),
            required=False,
            help=('the symmetry of the structure, '
                  'used to construct the input .gui file (fort.34)'))
        spec.input(
            'kinds',
            valid_type=DataFactory('crystal17.kinds'),
            required=False,
            help=('additional structure kind specific data '
                  '(e.g. initial spin)'))
        spec.input_namespace(
            'basissets',
            valid_type=DataFactory('crystal17.basisset'),
            dynamic=True,
            help=('Use a node for the basis set of one of '
                  'the elements in the structure. You have to pass '
                  "an additional parameter ('element') specifying the "
                  'atomic element symbol for which you want to use this '
                  'basis set.'))

        spec.input(
            'wf_folder',
            valid_type=RemoteData,
            required=False,
            help=('An optional working directory, '
                  'of a previously completed calculation, '
                  'containing a fort.9 wavefunction file to restart from'))

        # TODO allow for input of HESSOPT.DAT file

        # Note: OPTINFO.DAT is also meant for geometry restarts (with RESTART),
        #       but on both crystal and Pcrystal, a read file error is encountered trying to use it.

        spec.output(
            'optimisation',
            valid_type=TrajectoryData,
            required=False,
            help='atomic configurations, for each optimisation step')

    # pylint: disable=too-many-arguments
    @classmethod
    def create_builder(cls,
                       parameters,
                       structure,
                       bases,
                       symmetry=None,
                       kinds=None,
                       code=None,
                       metadata=None,
                       unflatten=False):
        """ prepare and validate the inputs to the calculation,
        and return a builder pre-populated with the calculation inputs

        Parameters
        ----------
        parameters: dict or CryInputParamsData
            input parameters to create the input .d12 file
        structure: aiida.StructureData
            the structure node
        bases: str or dict
            string of the BasisSetFamily to use,
            or dict mapping {<symbol>: <BasisSetData>}
        symmetry: SymmetryData or None
            giving symmetry operations, etc
        metadata: dict
            the computation metadata, e.g.
            {"options": {"resources": {"num_machines": 1, "num_mpiprocs_per_machine": 1}}}
        unflatten: bool
            whether to unflatten the input parameters dictionary

        Returns
        -------
        aiida.engine.processes.ProcessBuilder

        """
        builder = cls.get_builder()
        param_cls = DataFactory('crystal17.parameters')
        if not isinstance(parameters, param_cls):
            parameters = param_cls(data=parameters, unflatten=unflatten)
        builder.parameters = parameters
        builder.structure = structure
        if symmetry is not None:
            builder.symmetry = symmetry
        if kinds is not None:
            builder.kinds = kinds
        if code is not None:
            if isinstance(code, six.string_types):
                code = Code.get_from_string(code)
            builder.code = code
        if metadata is not None:
            builder.metadata = metadata

        # validate parameters
        atom_props = create_atom_properties(structure, kinds)
        write_input(parameters.get_dict(), ['test_basis'], atom_props)

        # validate basis sets
        basis_cls = DataFactory('crystal17.basisset')
        if isinstance(bases, six.string_types):
            symbol_to_basis_map = basis_cls.get_basissets_from_structure(structure, bases, by_kind=False)
        else:
            elements_required = set([kind.symbol for kind in structure.kinds])
            if set(bases.keys()) != elements_required:
                err_msg = ('Mismatch between the defined basissets and the list of '
                           'elements of the structure. Basissets: {}; elements: {}'.format(
                               set(bases.keys()), elements_required))
                raise InputValidationError(err_msg)
            symbol_to_basis_map = bases

        builder.basissets = symbol_to_basis_map

        return builder

    def prepare_for_submission(self, tempfolder):
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.

        :param tempfolder: an aiida.common.folders.Folder subclass
                           where the plugin should put all its files.
        """
        # Check that a basis set was specified
        # for each symbol present in the `StructureData`
        symbols = [kind.symbol for kind in self.inputs.structure.kinds]
        if set(symbols) != set(self.inputs.basissets.keys()):
            raise InputValidationError('Mismatch between the defined basissets '
                                       'and the list of symbols of the structure.\n'
                                       'Basissets: {};\nSymbols: {}'.format(', '.join(self.inputs.basissets.keys()),
                                                                            ', '.join(list(symbols))))

        # set the initial parameters
        parameters = self.inputs.parameters.get_dict()
        restart_fnames = []
        remote_copy_list = []

        # deal with scf restarts
        if 'wf_folder' in self.inputs:
            # TODO it would be good to check if the fort.9 exists and is not empty
            # (fort.9 is present but empty if crystal is killed by SIGTERM (e.g. when walltime reached))
            # but this would involve connecting to the remote computer, which could fail
            # Ideally would want to use the process exponential backoff & pause functionality
            remote_copy_list.append((self.inputs.wf_folder.computer.uuid,
                                     os.path.join(self.inputs.wf_folder.get_remote_path(), 'fort.9'), 'fort.20'))
            restart_fnames.append('fort.20')

        # modify parameters to use restart files
        parameters = self._modify_parameters(parameters, restart_fnames)

        # create fort.34 external geometry file and place it in tempfolder
        gui_content = gui_file_write(self.inputs.structure, self.inputs.get('symmetry', None))
        with tempfolder.open('fort.34', 'w') as f:
            f.write(six.u('\n'.join(gui_content)))

        # create .d12 input file and place it in tempfolder
        atom_props = create_atom_properties(self.inputs.structure, self.inputs.get('kinds', None))
        try:
            d12_filecontent = write_input(
                parameters, [self.inputs.basissets[k] for k in sorted(self.inputs.basissets.keys())], atom_props)
        except (ValueError, NotImplementedError) as err:
            raise InputValidationError('an input file could not be created from the parameters: {}'.format(err))
        with tempfolder.open(self.metadata.options.input_file_name, 'w') as f:
            f.write(d12_filecontent)

        # setup the calculation info
        return self.create_calc_info(
            tempfolder,
            remote_copy_list=remote_copy_list,
            retrieve_list=[self.metadata.options.output_main_file_name, 'fort.34', 'HESSOPT.DAT'],
            retrieve_temporary_list=['opt[ac][0-9][0-9][0-9]'])

    @staticmethod
    def _modify_parameters(parameters, restart_fnames):
        """ modify the parameters,
        according to what restart files are available
        """
        if not restart_fnames:
            return parameters

        if 'fort.20' in restart_fnames:
            parameters['scf']['GUESSP'] = True

        if 'HESSOPT.DAT' in restart_fnames:
            if parameters.get('geometry', {}).get('optimise', False):
                if isinstance(parameters['geometry']['optimise'], bool):
                    parameters['geometry']['optimise'] = {}
                parameters['geometry']['optimise']['hessian'] = 'HESSOPT'

        if 'OPTINFO.DAT' in restart_fnames:
            if parameters.get('geometry', {}).get('optimise', False):
                if isinstance(parameters['geometry']['optimise'], bool):
                    parameters['geometry']['optimise'] = {}
                parameters['geometry']['optimise']['restart'] = True

        return parameters

    @staticmethod
    def _check_remote(remote_folder, file_names):
        """tests if files are present and note empty on a remote folder

        Parameters
        ----------
        remote_folder : aiida.orm.nodes.data.remote.RemoteData
        file_names: list[str]

        Returns
        -------
        result: dict
            {<file_name>: bool, ...}

        Raises
        ------
        IOError
            if the remote_folder's path does not exist on the remote computer

        """
        result = {}
        # open a transport to the parent computer, and find viable restart files
        # TODO this will fail if not connected to the remote path,
        # but if the calculation is part of a workflow this would be unwanted
        # (i.e. should be paused until connection is established)
        trans = remote_folder.get_authinfo().get_transport()
        with trans:
            if not trans.isdir(remote_folder.get_remote_path()):
                raise IOError("the remote_folder's path does not exist on the remote computer")
            trans.chdir(remote_folder.get_remote_path())
            remote_fnames = trans.listdir()
            for file_name in file_names:
                if file_name not in remote_fnames:
                    result[file_name] = False
                elif trans.isdir(file_name):
                    result[file_name] = False
                elif trans.get_attribute(file_name).st_size <= 0:
                    result[file_name] = False
                else:
                    result[file_name] = True

        return result
