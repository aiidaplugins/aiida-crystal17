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
from aiida.common import AttributeDict, LinkType
from aiida.engine import if_, ToContext, WorkChain
from aiida.manage.caching import disable_caching
from aiida.orm import Bool, CalcJobNode
from aiida.orm.nodes.data.base import to_aiida_type
from aiida.plugins import CalculationFactory

from aiida_crystal17.data.input_params import CryInputParamsData
CryDossCalculation = CalculationFactory('crystal17.doss')
CryCalculation = CalculationFactory('crystal17.main')


class CryPropertiesWorkChain(WorkChain):
    """a WorkChain to compute properties of a structure, using CRYSTAL

    A RemoteData node should be supplied that was created by a previous `CryMainCalculation`.
    If the remote folder no longer exists or does not contain the wavefunction file
    (usually fort.9 or designated by `inputs.doss.metadata.options.input_wf_name`),
    the previous calculations inputs/outputs will be used to run an SCF calculation first.

    Currently this work chain is only set up to run a DOSS calculation,
    but in the future it would be intended to run a selection of property calculations.

    """
    _doss_namespace = 'doss'
    _calc_namespace = 'cry'

    @classmethod
    def define(cls, spec):
        # yapf: disable
        # pylint: disable=bad-continuation
        super(CryPropertiesWorkChain, cls).define(spec)

        spec.expose_inputs(CryDossCalculation, include=['wf_folder'])
        spec.expose_inputs(CryDossCalculation, namespace=cls._doss_namespace, exclude=('wf_folder',))
        spec.input('{}.metadata.options.resources'.format(cls._doss_namespace), valid_type=dict, required=False)
        spec.input('{}.meta_options'.format(cls._calc_namespace),
                   valid_type=dict, required=False, non_db=True,
                   help='if supplied will update the original CryMainCalculations `metadata.options')
        spec.input('clean_workdir', valid_type=Bool,
                   serializer=to_aiida_type, required=False,
                   help='If `True`, work directories of all called calculation will be cleaned at the end of execution.')
        spec.input('test_run', valid_type=Bool, required=False, serializer=to_aiida_type,
                   help='break off the workchain before submitting a calculation')

        spec.outline(
            if_(cls.check_remote_folder)(
                cls.submit_scf_calculation,
                cls.check_scf_calculation
            ),
            cls.submit_doss_calculation,
            cls.check_doss_calculation
        )

        spec.expose_outputs(CryDossCalculation, namespace=cls._doss_namespace)

        spec.exit_code(
            200, 'END_OF_TEST_RUN',
            message=('Workchain ended before submitting calculation'))
        spec.exit_code(
            201, 'ERROR_NO_INCOMING_CALC',
            message=('The wf_folder does not contain a wavefunction file, '
                     'and was not created by a CryMainCalculation.'))
        spec.exit_code(
            202, 'ERROR_FAILED_INCOMING_CALC',
            message=('The CryMainCalculation that created the wf_folder failed.'))
        spec.exit_code(
            203, 'ERROR_INCOMPLETE_INCOMING_CALC',
            message=('The CryMainCalculation that created the wf_folder can not be used to restart a calculation.'))
        spec.exit_code(
            204, 'ERROR_SCF_CALC_FAILED',
            message=('The SCF calculation failed.'))
        spec.exit_code(
            205, 'ERROR_DOSS_CALC_FAILED',
            message=('The DOSS calculation failed'))

    def check_remote_folder(self):
        """ check that the remote folder contains the wavefunction file
        """
        self.ctx.wf_folder = self.inputs.wf_folder
        wf_filename = self.inputs.doss.metadata.options.input_wf_name
        # TODO this should use the exponential backoff mechanism
        if not self.inputs.wf_folder.is_empty:
            content = self.inputs.wf_folder.listdir()
            if wf_filename in content:
                self.ctx.run_calc = False
                return False

        self.report("Remote folder {} does not contain '{}', attempting to rerun SCF calculation".format(
            self.inputs.wf_folder, wf_filename))
        self.ctx.run_calc = True
        # TODO if re-running we should reset self.inputs.doss.metadata.options.input_wf_name
        return True

    def submit_scf_calculation(self):
        """Create and submit an SCF calculation,
        created from the previous calculations inputs (and output structure if present).
        Checks are made that the previous calculation was successful
        """
        incoming = self.inputs.wf_folder.get_incoming(
            node_class=CryCalculation, link_type=LinkType.CREATE).all_nodes()
        if not incoming:
            self.report('{} was not created by a CryMainCalculation'.format(self.inputs.wf_folder))
            return self.exit_codes.ERROR_NO_INCOMING_CALC

        previous_calc = incoming[0]
        if not previous_calc.is_finished_ok:
            self.report('{} did not finish ok: {}'.format(previous_calc, previous_calc.exit_status))
            return self.exit_codes.ERROR_FAILED_INCOMING_CALC

        # create a restart calculation
        previous_calc = incoming[0]
        builder = incoming[0].get_builder_restart()
        # we only want to run a single-point calculation, so can remove any geometry optimisation
        try:
            params = builder.parameters.get_dict()
            params.get('geometry', {}).pop('optimise', None)
        except AttributeError:
            self.report('{} has no `parameters` intput'.format(previous_calc))
            return self.exit_codes.ERROR_INCOMPLETE_INCOMING_CALC

        self.ctx.calc_params = params

        try:
            self.ctx.calc_options = builder.metadata.options
        except AttributeError:
            self.report('{} has no `metadata.options` set'.format(previous_calc))
            return self.exit_codes.ERROR_INCOMPLETE_INCOMING_CALC

        # if new metadata options have been supplied then use them
        if 'meta_options' in self.inputs.cry:
            self.report('replacing metadata of calculation')
            self.ctx.calc_options.update(self.inputs.cry['meta_options'])

        # use the final structure (output if the previous calculation was an optimization)
        if 'structure' in previous_calc.outputs:
            self.report('using optimised structure')
            builder.structure = previous_calc.outputs.structure

        # we want to use the final structure, so the input wavefunction will not apply
        if 'wf_folder' in builder:
            builder.pop('wf_folder')
        # TODO add a `remove_restarts` function to CryMainCalculation,
        # to remove e.g. GUESSP, HESSOPT, RESTART keywords
        self.ctx.calc_params.setdefault('scf', {}).pop('GUESSP', None)

        builder.parameters = CryInputParamsData(data=params)
        builder.metadata.options = self.ctx.calc_options

        if 'test_run' in self.inputs and self.inputs.test_run.value:
            self.report('`test_run` specified, stopping before submitting scf calculation')
            return self.exit_codes.END_OF_TEST_RUN

        # TODO could submit CryMainBaseWorkChain
        builder.metadata.call_link_label = 'scf_calc'
        try:
            with disable_caching():
                calculation = self.submit(builder)
        except Exception as err:
            self.report('{} submission failed: {}'.format(previous_calc, err))
            return self.exit_codes.ERROR_INCOMPLETE_INCOMING_CALC

        self.report('launching SCF calculation {}'.format(calculation))

        return ToContext(calc_scf=calculation)

    def check_scf_calculation(self):

        if not self.ctx.calc_scf.is_finished_ok:
            self.report('{} failed with exit code: {}'.format(self.ctx.calc_scf, self.ctx.calc_scf.exit_status))
            return self.exit_codes.ERROR_SCF_CALC_FAILED
        self.report('{} finished successfully'.format(self.ctx.calc_scf))
        self.ctx.wf_folder = self.ctx.calc_scf.outputs.remote_folder

    def submit_doss_calculation(self):
        if 'test_run' in self.inputs and self.inputs.test_run.value:
            self.report('`test_run` specified, stopping before submitting doss calculation')
            return self.exit_codes.END_OF_TEST_RUN

        inputs = AttributeDict(self.exposed_inputs(CryDossCalculation, self._doss_namespace))
        inputs.wf_folder = self.ctx.wf_folder
        inputs['metadata']['call_link_label'] = 'doss_calc'
        calculation = self.submit(CryDossCalculation, **inputs)
        self.report('launching DOSS calculation {}'.format(calculation))
        return ToContext(calc_doss=calculation)

    def check_doss_calculation(self):

        if not self.ctx.calc_doss.is_finished_ok:
            self.report('{} failed with exit code: {}'.format(
                self.ctx.calc_doss, self.ctx.calc_doss.exit_status))
            return self.exit_codes.ERROR_DOSS_CALC_FAILED

        self.report('{} finished successfully'.format(self.ctx.calc_doss))

        namespace_separator = self.spec().namespace_separator
        for link_triple in self.ctx.calc_doss.get_outgoing(link_type=LinkType.CREATE).link_triples:
            self.out(self._doss_namespace + namespace_separator + link_triple.link_label, link_triple.node)

    def on_terminated(self):
        """Clean the working directories of all child calculations if `clean_workdir=True` in the inputs."""
        super(CryPropertiesWorkChain, self).on_terminated()

        if 'clean_workdir' not in self.inputs or self.inputs.clean_workdir.value is False:
            self.report('remote folders will not be cleaned')
            return

        cleaned_calcs = []

        for called_descendant in self.node.called_descendants:
            if isinstance(called_descendant, CalcJobNode):
                try:
                    called_descendant.outputs.remote_folder._clean()  # pylint: disable=protected-access
                    cleaned_calcs.append(str(called_descendant.pk))
                except (IOError, OSError, KeyError):
                    pass

        if cleaned_calcs:
            self.report('cleaned remote folders of calculations: {}'.format(
                ' '.join(cleaned_calcs)))
