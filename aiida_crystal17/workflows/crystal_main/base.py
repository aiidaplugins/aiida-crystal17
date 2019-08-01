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
from aiida import orm
from aiida.common import AttributeDict
from aiida.common.exceptions import InputValidationError
from aiida.engine import while_
from aiida.orm.nodes.data.base import to_aiida_type
from aiida.plugins import CalculationFactory, DataFactory

from aiida_crystal17.workflows.common.restart import BaseRestartWorkChain, ErrorHandlerReport, register_error_handler
from aiida_crystal17.common.kpoints import create_kpoints_from_distance

CryCalculation = CalculationFactory('crystal17.main')
CryInputParamsData = DataFactory('crystal17.parameters')
BasisSetsData = DataFactory('crystal17.basisset')


def _validate_kpoint_distance(float_data):
    if float_data and not float_data.value > 0:
        raise InputValidationError('kpoints_distance must be greater than 0')


class CryMainBaseWorkChain(BaseRestartWorkChain):
    """Workchain to run a standard CRYSTAL17 calculation with automated error handling and restarts."""

    _calculation_class = CryCalculation
    _error_handler_entry_point = 'aiida_crystal17.workflow_error_handlers.main.base'

    _calc_namespace = 'cry'

    defaults = AttributeDict({'fmixing': 30, 'delta_factor_fmixing': 0.8})

    @classmethod
    def define(cls, spec):
        # yapf: disable
        super(CryMainBaseWorkChain, cls).define(spec)
        spec.expose_inputs(CryCalculation, namespace=cls._calc_namespace, exclude=())
        spec.input('{}.metadata.options.resources'.format(cls._calc_namespace), valid_type=dict, required=False)
        spec.input('basis_family', valid_type=orm.Str, required=False, serializer=to_aiida_type,
                   help=(
                       'An alternative to specifying the basis sets manually: one can specify the name '
                       'of an existing basis set family and the work chain will generate the basis sets automatically '
                       'based on the input structure.'))
        spec.input('kpoints_distance', valid_type=orm.Float, required=False, serializer=to_aiida_type,
                   validator=_validate_kpoint_distance,
                   help=(
                       'The minimum desired distance in 1/Å between k-points in reciprocal space. '
                       'The explicit k-points will be generated automatically by the input structure, and '
                       'will replace the SHRINK IS value in the input parameters.'
                       'Note: This methods assumes the PRIMITIVE unit cell is provided'))
        spec.input('kpoints_force_parity', valid_type=orm.Bool, required=False, serializer=to_aiida_type,
                   help=(
                       'Optional input when constructing the k-points based on a desired `kpoints_distance`. '
                       'Setting this to `True` will force the k-point mesh to have an even number of points '
                       'along each lattice vector except for any non-periodic directions.'))

        # TODO include option for symmetry calculation
        spec.outline(
            cls.setup,
            cls.validate_parameters,
            cls.validate_basis_sets,
            cls.validate_resources,
            while_(cls.should_run_calculation)(
                cls.prepare_calculation,
                cls.run_calculation,
                cls.inspect_calculation,
            ),
            cls.results,
        )

        spec.expose_outputs(CryCalculation, exclude=('retrieved', 'optimisation'))

        spec.exit_code(201, 'ERROR_INVALID_INPUT_PARAMETERS',
                       message=('The parameters could not be validated against the jsonschema.'))
        spec.exit_code(202, 'ERROR_INVALID_INPUT_BASIS_SETS',
                       message=('The explicit `basis_sets` or `basis_family` '
                                'could not be used to get the necessary basis sets.'))
        spec.exit_code(204, 'ERROR_INVALID_INPUT_RESOURCES_UNDERSPECIFIED',
                       message=('The `metadata.options` did not specify both '
                                '`resources.num_machines` and `max_wallclock_seconds`.'))
        spec.exit_code(300, 'ERROR_UNRECOVERABLE_FAILURE',
                       message='The calculation failed with an unrecoverable error.')
        spec.exit_code(320, 'ERROR_INITIALIZATION_CALCULATION_FAILED',
                       message='The initialization calculation failed.')

    def setup(self):
        """Call the `setup` of the `BaseRestartWorkChain` and then create the inputs dictionary in `self.ctx.inputs`.

        This `self.ctx.inputs` dictionary will be used by the `BaseRestartWorkChain` to submit the calculations in the
        internal loop.
        """
        super(CryMainBaseWorkChain, self).setup()
        self.ctx.inputs = AttributeDict(self.exposed_inputs(CryCalculation, self._calc_namespace))
        self.ctx.use_fort9_restart = False

    def validate_parameters(self):
        """Validate inputs that might depend on each other and cannot be validated by the spec.

        Also define dictionary `inputs` in the context, that will contain the inputs for the calculation that will be
        launched in the `run_calculation` step.
        """
        self.ctx.inputs.parameters = self.ctx.inputs.parameters.get_dict()
        try:
            CryInputParamsData.validate_parameters(self.ctx.inputs.parameters)
        except Exception as exception:
            self.report('{}'.format(exception))
            return self.exit_codes.ERROR_INVALID_INPUT_PARAMETERS

        # check if the run is an optimisation and store in context
        optimise = self.ctx.inputs.parameters.get('geometry', {}).get('optimise', False)
        self.ctx.is_optimisation = True if optimise else False

        if 'kpoints_distance' in self.inputs:
            force_parity = self.inputs.get('kpoints_force_parity', orm.Bool(False)).value
            kpoints = create_kpoints_from_distance(
                self.ctx.inputs.structure, self.inputs.kpoints_distance.value, force_parity)
            # TODO check / deal with non-zero offsets
            is_value = kpoints.get_kpoints_mesh()[0]
            isp_value = int(max(is_value) * 2)
            if is_value[0] == is_value[1] == is_value[2]:
                is_value = is_value[0]

            curr_kpoints = list(self.ctx.inputs.parameters['scf']['k_points'])
            if curr_kpoints != [is_value, isp_value]:
                self.report('changing the intput kpoints ({0}) to the computed kpoints ({1})'.format(
                    curr_kpoints, [is_value, isp_value]
                ))
                self.ctx.inputs.parameters['scf']['k_points'] = [is_value, isp_value]

    def validate_basis_sets(self):
        """Validate the inputs related to basis sets.

        Either the basis sets should be defined explicitly in the `basissets` namespace, or alternatively, a family
        can be defined in `basis_family` that will be used together with the input `StructureData` to generate the
        required mapping.
        """
        structure = self.ctx.inputs.structure
        basissets = self.ctx.inputs.get('basissets', None)
        basis_family = self.inputs.get('basis_family', None)

        try:
            self.ctx.inputs.basissets = BasisSetsData.prepare_and_validate_inputs(structure, basissets, basis_family)
        except ValueError as exception:
            self.report('{}'.format(exception))
            return self.exit_codes.ERROR_INVALID_INPUT_BASIS_SETS

    def validate_resources(self):
        """Validate the inputs related to the resources.

        One can omit the normally required `options.resources` input for the `PwCalculation`, as long as the input
        `automatic_parallelization` is specified. If this is not the case, the `metadata.options` should at least
        contain the options `resources` and `max_wallclock_seconds`, where `resources` should define the `num_machines`.
        """
        num_machines = self.ctx.inputs.metadata.options.get('resources', {}).get('num_machines', None)
        max_wallclock_seconds = self.ctx.inputs.metadata.options.get('max_wallclock_seconds', None)

        if num_machines is None or max_wallclock_seconds is None:
            return self.exit_codes.ERROR_INVALID_INPUT_RESOURCES_UNDERSPECIFIED

    def prepare_calculation(self):
        """Prepare the inputs for the next calculation.

        If a `restart_calc` has been set in the context, its `remote_folder` will be used as the `wf_folder` input
        for the next calculation.
        """
        if self.ctx.restart_calc:

            self.ctx.inputs.pop('wf_folder', None)

            if 'optimisation' in self.ctx.restart_calc.outputs:
                # use the last recorded structure of an optimisation
                self.ctx.inputs.structure = self.ctx.restart_calc.outputs.optimisation.get_step_structure(
                    -1, custom_kinds=self.ctx.inputs.structure.kinds)
                # TODO could also use HESSOPT.DAT

            if self.ctx.use_fort9_restart:
                # TODO it would be good to check if the fort.9 is present & non-empty
                # but should use the exponential-backoff / pause functionality, to connect to the remote
                # or, at least test for a crystal read failure, and restart without it
                # the failure looks like: 'io error\nRead_int_1d', which isn't particularly helpful
                self.ctx.inputs.wf_folder = self.ctx.restart_calc.outputs.remote_folder
                self.ctx.use_fort9_restart = False

    def report_error_handled(self, calculation, action):
        """Report an action taken for a calculation that has failed.

        This should be called in a registered error handler if its condition is met and an action was taken.

        :param calculation: the failed calculation node
        :param action: a string message with the action taken
        """
        arguments = [calculation.process_label, calculation.pk, calculation.exit_status, calculation.exit_message]
        self.report('{}<{}> failed with exit status {}: {}'.format(*arguments))
        self.report('Action taken: {}'.format(action))


@register_error_handler(CryMainBaseWorkChain, 500)
def _handle_unrecoverable_failure(self, calculation):
    """Calculations with an exit status below 400 are unrecoverable, so abort the work chain."""
    if calculation.exit_status < 400:
        self.report_error_handled(calculation, 'unrecoverable error, aborting...')
        return ErrorHandlerReport(True, True, self.exit_codes.ERROR_UNRECOVERABLE_FAILURE)


@register_error_handler(CryMainBaseWorkChain, 420)
def _handle_out_of_walltime(self, calculation):
    """In the case of `ERROR_OUT_OF_WALLTIME`, restart from the last recorded configuration."""
    if calculation.exit_status == CryCalculation.spec().exit_codes.ERROR_OUT_OF_WALLTIME.status:
        if not self.ctx.is_optimisation:
            self.report_error_handled(
                calculation, 'there is currently no restart facility for a killed scf calculation')
            return ErrorHandlerReport(True, True, self.exit_codes.ERROR_UNRECOVERABLE_FAILURE)
        self.ctx.restart_calc = calculation
        self.ctx.use_fort9_restart = False  # the fort.9 is wiped in-between SCF
        self.report_error_handled(calculation, 'simply restart from the last calculation')
        return ErrorHandlerReport(True, True)


@register_error_handler(CryMainBaseWorkChain, 410)
def _handle_electronic_convergence_not_achieved(self, calculation):
    """In the case of `UNCONVERGED_SCF`,
    decrease the function mixing and restart from the last recorded configuration."""
    if calculation.exit_status == CryCalculation.spec().exit_codes.UNCONVERGED_SCF.status:
        factor = self.defaults.delta_factor_fmixing
        fmixing = self.ctx.inputs.parameters['scf'].get('numerical', {}).get('FMIXING', self.defaults.fmixing)
        fmixing_new = int(fmixing * factor)

        self.ctx.restart_calc = calculation
        self.ctx.use_fort9_restart = True
        self.ctx.inputs.parameters['scf'].setdefault('numerical', {})['FMIXING'] = fmixing_new

        action = 'reduced fmixing from {} to {} and restarting from last calculation'.format(fmixing, fmixing_new)
        self.report_error_handled(calculation, action)
        return ErrorHandlerReport(True, True)


@register_error_handler(CryMainBaseWorkChain, 400)
def _handle_geometric_convergence_not_achieved(self, calculation):
    """In the case of `UNCONVERGED_GEOMETRY`, restart from the last recorded configuration."""
    if calculation.exit_status == CryCalculation.spec().exit_codes.UNCONVERGED_GEOMETRY.status:
        self.ctx.restart_calc = calculation
        self.ctx.use_fort9_restart = True
        self.report_error_handled(calculation, 'simply restart from the last calculation')
        return ErrorHandlerReport(True, True)
