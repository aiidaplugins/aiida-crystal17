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
import copy

from plumpy.ports import PortNamespace
from six import PY2

from aiida import orm
from aiida.common import AttributeDict, LinkType
from aiida.engine import if_, ToContext, WorkChain
from aiida.manage.caching import disable_caching
from aiida.orm.nodes.data.base import to_aiida_type

from aiida_crystal17.data.input_params import CryInputParamsData
from aiida_crystal17.calculations.cry_main import CryMainCalculation
from aiida_crystal17.calculations.prop_doss import CryDossCalculation
from aiida_crystal17.calculations.prop_ech3 import CryEch3Calculation

if PY2:
    from collections import Mapping
else:
    from collections.abc import Mapping


def expose_ports(port, port_namespace, exclude):
    for sub_port_name, sub_port in port_namespace.items():
        if isinstance(sub_port, PortNamespace):
            sub_port_copy = copy.copy(sub_port)
            sub_port_copy._ports = {}
            # sub_port_copy.required = False
            sub_port_copy.populate_defaults = False
            port[sub_port_name] = sub_port_copy
            expose_ports(port[sub_port_name], sub_port, exclude)
        elif exclude is not None and sub_port_name in exclude:
            pass
        else:
            sub_port_copy = copy.deepcopy(sub_port)
            sub_port_copy.required = False
            port[sub_port_name] = sub_port_copy


def expose_optional_inputs(spec, namespace, process_class, exclude=None):
    spec.input_namespace(namespace, required=False)
    expose_ports(spec.inputs[namespace], process_class.spec().inputs, exclude)


def strip_empty_namespaces(data):
    """Create a dict, with no empty namespaces."""
    new_data = {}
    for name, value in data.items():
        if isinstance(value, Mapping):
            value = strip_empty_namespaces(value)
        if isinstance(value, Mapping) and len(value) == 0:
            pass
        else:
            new_data[name] = value
    return new_data


def get_builder_rerun_scf(calc_node):
    """Create a populated builder, from a previously run CryMainCalculation."""
    if not calc_node.is_finished_ok:
        raise ValueError('The previous calculation failed')
    builder = calc_node.get_builder_restart()
    # we only want to run a single-point calculation,
    # so can remove any geometry optimisation.
    params = builder.parameters.get_dict()
    params.get('geometry', {}).pop('optimise', None)
    params.setdefault('scf', {}).pop('GUESSP', None)
    builder.parameters = CryInputParamsData(data=params)
    # use the final structure (output if the previous calculation was an optimization)
    if 'structure' in calc_node.outputs:
        builder.structure = calc_node.outputs.structure
    # we want to use the final structure, so the input wavefunction will not apply
    if 'wf_folder' in builder:
        builder.pop('wf_folder')


class CryPropertiesWorkChain(WorkChain):
    """A WorkChain to compute properties of a structure, using CRYSTAL.

    Either a pre-computed wavefunction (fort.9) file, or inputs for a CryMainCalculation,
    should be supplied.
    Inputs for property calculations can then be added (currently available; doss, ech3).

    """

    _wf_fname = 'fort.9'
    _scf_name = 'scf'
    _scf_class = CryMainCalculation
    _cry_props = {'doss': CryDossCalculation, 'ech3': CryEch3Calculation}

    def __init__(self, **kwargs):
        """Initialize inputs.

        Here we strip any empty workspaces from the inputs.
        This is because, as of v1.0.0b6, supplying a builder object to submit/run
        will include empty namespaces,
        e.g. ``{'scf': {'metadata': {'options': {}}, 'basissets': {}}}``.
        This is an issue for non-required namespaces, which have required ports,
        and will fail validation if these empty namespaces are present.

        """
        # TODO raise an issue on aiida-core
        if kwargs.get('inputs', None):
            kwargs['inputs'] = strip_empty_namespaces(kwargs['inputs'])
        super(CryPropertiesWorkChain, self).__init__(**kwargs)

    @classmethod
    def define(cls, spec):
        # yapf: disable
        super(CryPropertiesWorkChain, cls).define(spec)

        # Input requires either a pre-computed wavefunction (fort.9) file,
        # or inputs for a Crystal Calculation
        spec.input('wf_folder',
                   valid_type=(orm.FolderData, orm.RemoteData, orm.SinglefileData),
                   required=False,
                   help='the folder containing the wavefunction fort.9 file')
        # expose_optional_inputs(spec, cls._scf_namespace, CryMainCalculation)
        spec.expose_inputs(cls._scf_class, namespace=cls._scf_name,
                           namespace_options={'required': False, 'populate_defaults': False})

        # available property computations
        for pname, process_class in cls._cry_props.items():
            spec.expose_inputs(process_class, namespace=pname, exclude=['wf_folder'],
                               namespace_options={'required': False, 'populate_defaults': False})
            spec.expose_outputs(process_class, namespace=pname,
                                namespace_options={'required': False})

        # additional input parameters
        spec.input(
            'check_remote',
            valid_type=orm.Bool,
            serializer=to_aiida_type,
            required=False,
            help=('If a RemoteData wf_folder is input, check it contains the wavefunction file, '
                  'before launching calculations. '
                  'Note, this will fail if the remote computer is not immediately available'))
        spec.input(
            'clean_workdir',
            valid_type=orm.Bool,
            serializer=to_aiida_type,
            required=False,
            help='If `True`, work directories of all called calculation will be cleaned at the end of execution.')
        spec.input(
            'test_run',
            valid_type=orm.Bool,
            required=False,
            serializer=to_aiida_type,
            help='break off the workchain before submitting a calculation')

        spec.outline(
            cls.check_inputs,
            if_(cls.check_wf_folder)(
                cls.submit_scf_calculation,
                cls.check_scf_calculation
                ),
            cls.submit_prop_calculations,
            cls.check_prop_calculations
        )

        spec.exit_code(200, 'END_OF_TEST_RUN', message=('Workchain ended before submitting calculation.'))
        spec.exit_code(201, 'ERROR_NO_WF_INPUT', message=('Neither a wf_folder nor scf calculation was supplied.'))
        spec.exit_code(202, 'ERROR_NO_PROP_INPUT', message=('No property calculation inputs were supplied.'))
        spec.exit_code(203, 'ERROR_WF_FOLDER', message=('The supplied folder does contain the wavefunction file.'))

        spec.exit_code(210, 'ERROR_SCF_SUBMISSION_FAILED', message=('The SCF calculation submission failed.'))

        spec.exit_code(301, 'ERROR_SCF_CALC_FAILED', message=('The SCF calculation failed.'))
        spec.exit_code(302, 'ERROR_PROP_CALC_FAILED', message=('One or more property calculations failed.'))

    def check_inputs(self):
        """Check that necessary inputs have been supplied."""
        if 'wf_folder' not in self.inputs and 'scf' not in self.inputs:
            return self.exit_codes.ERROR_NO_WF_INPUT
        prop_calc = False
        for prop_name in self._cry_props:
            if prop_name in self.inputs:
                prop_calc = True
        if not prop_calc:
            return self.exit_codes.ERROR_NO_PROP_INPUT

    def check_wf_folder(self):
        """Check whether a wavefunction file has been supplied."""
        if 'wf_folder' not in self.inputs:
            self.report("No 'wf_folder' supplied, running SCF Calculation...")
            self.ctx.wf_folder = None
            return True

        # check the supplied folder contains the wavefunction file
        if isinstance(self.inputs.wf_folder, orm.FolderData):
            if self._wf_fname not in self.inputs.wf_folder.list_object_names():
                return self.exit_codes.ERROR_WF_FOLDER
        elif isinstance(self.inputs.wf_folder, orm.RemoteData):
            if 'check_remote' in self.inputs and self.inputs.check_remote.value:
                # TODO this should use the exponential backoff mechanism
                if self.inputs.wf_folder.is_empty:
                    return self.exit_codes.ERROR_WF_FOLDER
                if self._wf_fname not in self.inputs.wf_folder.listdir():
                    return self.exit_codes.ERROR_WF_FOLDER

        self.report("Using supplied 'wf_folder'")
        self.ctx.wf_folder = self.inputs.wf_folder
        return False

    def submit_scf_calculation(self):
        """Create and submit an SCF calculation."""
        if 'test_run' in self.inputs and self.inputs.test_run.value:
            self.report('`test_run` specified, stopping before submitting scf calculation')
            return self.exit_codes.END_OF_TEST_RUN

        inputs = AttributeDict(self.exposed_inputs(self._scf_class, self._scf_name))
        inputs['metadata']['call_link_label'] = 'calc_{}'.format(self._scf_name)
        try:
            with disable_caching():
                # even if the calculation has already been run, the remote folder may not be available
                future = self.submit(self._scf_class, **inputs)
        except Exception as err:
            self.report('SCF submission failed: {}'.format(err))
            return self.exit_codes.ERROR_SCF_SUBMISSION_FAILED

        self.report('launched SCF calculation: {}'.format(future))
        return ToContext(calc_scf=future)

    def check_scf_calculation(self):
        """Check that the SCF calculation finished successfully, and add the remote folder to the context."""
        if not self.ctx.calc_scf.is_finished_ok:
            self.report('{} failed with exit code: {}'.format(self.ctx.calc_scf, self.ctx.calc_scf.exit_status))
            return self.exit_codes.ERROR_SCF_CALC_FAILED
        self.report('{} finished successfully'.format(self.ctx.calc_scf))
        self.ctx.wf_folder = self.ctx.calc_scf.outputs.remote_folder

    def submit_prop_calculations(self):
        """Create and submit all property calculations."""
        if 'test_run' in self.inputs and self.inputs.test_run.value:
            self.report('`test_run` specified, stopping before submitting property calculations')
            return self.exit_codes.END_OF_TEST_RUN

        for pname, process_class in self._cry_props.items():
            if pname not in self.inputs:
                continue
            inputs = AttributeDict(self.exposed_inputs(process_class, pname))
            inputs.wf_folder = self.ctx.wf_folder
            link_label = 'calc_{}'.format(pname)
            inputs['metadata']['call_link_label'] = link_label
            inputs['metadata']['options']['input_wf_name'] = self._wf_fname
            future = self.submit(process_class, **inputs)
            self.report('launched {} calculation {}'.format(pname, future))
            self.to_context(**{link_label: future})

    def check_prop_calculations(self):
        """Check that the property calculations finished successfully."""
        all_successful = True

        for pname, process_class in self._cry_props.items():
            link_label = 'calc_{}'.format(pname)
            if link_label not in self.ctx:
                continue
            calc_node = self.ctx[link_label]
            if not calc_node.is_finished_ok:
                self.report('{}; {} failed with exit code: {}'.format(link_label, calc_node, calc_node.exit_status))
                all_successful = False
                continue
            self.report('{}; {} finished successfully'.format(link_label, calc_node))

            # TODO exposed_outputs for CalcJobs is fixed in aiida-core v1.0.0b6
            # self.out_many(self.exposed_outputs(calc_node, process_class, namespace=pname))
            namespace_separator = self.spec().namespace_separator
            for link_triple in calc_node.get_outgoing(link_type=LinkType.CREATE).link_triples:
                self.out(pname + namespace_separator + link_triple.link_label, link_triple.node)

        if not all_successful:
            return self.exit_codes.ERROR_PROP_CALC_FAILED

    def on_terminated(self):
        """Clean the working directories of all child calculations if `clean_workdir=True` in the inputs."""
        super(CryPropertiesWorkChain, self).on_terminated()

        if 'clean_workdir' not in self.inputs or self.inputs.clean_workdir.value is False:
            self.report('remote folders will not be cleaned')
            return

        cleaned_calcs = []

        for called_descendant in self.node.called_descendants:
            if isinstance(called_descendant, orm.CalcJobNode):
                try:
                    called_descendant.outputs.remote_folder._clean()  # pylint: disable=protected-access
                    cleaned_calcs.append(str(called_descendant.pk))
                except (IOError, OSError, KeyError):
                    pass

        if cleaned_calcs:
            self.report('cleaned remote folders of calculations: {}'.format(' '.join(cleaned_calcs)))
