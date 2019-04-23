"""
Plugin to create a CRYSTAL17 output file,
from input files created via data nodes
"""
import os

import six
from aiida.common.datastructures import (CalcInfo, CodeInfo)
from aiida.common.exceptions import InputValidationError
from aiida.plugins import DataFactory
from aiida_crystal17.calculations.cry_abstract import CryAbstractCalculation
from aiida_crystal17.parsers.gui_parse import gui_file_write
from aiida_crystal17.parsers.inputd12_write import (
    write_input, create_atom_properties)


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
            'parameters', valid_type=DataFactory('crystal17.parameters'),
            required=True,
            help='the input parameters to create the .d12 file content.')
        spec.input(
            'structure', valid_type=DataFactory('structure'),
            required=True,
            help=('the structure used to construct the input .gui file '
                  '(fort.34)'))
        spec.input(
            'symmetry', valid_type=DataFactory('crystal17.symmetry'),
            required=False,
            help=('the symmetry of the structure, '
                  'used to construct the input .gui file (fort.34)'))
        spec.input(
            'kinds', valid_type=DataFactory('crystal17.kinds'),
            required=False,
            help=('additional structure kind specific data '
                  '(e.g. initial spin)'))
        spec.input_namespace(
            'basissets',
            valid_type=DataFactory('crystal17.basisset'), dynamic=True,
            help=("Use a node for the basis set of one of "
                  "the elements in the structure. You have to pass "
                  "an additional parameter ('element') specifying the "
                  "atomic element symbol for which you want to use this "
                  "basis set."))

    # pylint: disable=too-many-arguments
    @classmethod
    def create_builder(cls, parameters, structure, bases,
                       symmetry=None, kinds=None,
                       code=None, options=None, unflatten=False):
        """ prepare and validate the inputs to the calculation,
        and return a builder pre-populated with the calculation inputs

        Parameters
        ----------
        parameters: dict or CryInputParamsData
            input parameters to create the input .d12 file
        structure: aiida.orm.StructureData
            the structure node
        bases: str or dict
            string of the BasisSetFamily to use,
            or dict mapping {<symbol>: <BasisSetData>}
        symmetry: SymmetryData or None
            giving symmetry operations, etc
        options: dict
            the computation option, e.g.
            {"resources": {"num_machines": 1, "num_mpiprocs_per_machine": 1}}
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
            builder.code = code
        if options is not None:
            builder.metadata.options = options

        # validate parameters
        atom_props = create_atom_properties(structure, kinds)
        write_input(parameters.get_dict(), ["test_basis"], atom_props)

        # validate basis sets
        basis_cls = DataFactory('crystal17.basisset')
        if isinstance(bases, six.string_types):
            symbol_to_basis_map = basis_cls.get_basissets_from_structure(
                structure, bases, by_kind=False)
        else:
            elements_required = set([kind.symbol for kind in structure.kinds])
            if set(bases.keys()) != elements_required:
                err_msg = (
                    "Mismatch between the defined basissets and the list of "
                    "elements of the structure. Basissets: {}; elements: {}".
                    format(set(bases.keys()), elements_required))
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
            raise InputValidationError(
                'Mismatch between the defined basissets '
                'and the list of symbols of the structure.\n'
                'Basissets: {};\nSymbols: {}'.format(
                    ', '.join(self.inputs.basissets.keys()),
                    ', '.join(list(symbols))))

        self._create_input_files(
            self.inputs.basissets,
            self.inputs.structure,
            self.inputs.parameters,
            tempfolder,
            self.inputs.get("symmetry", None),
            self.inputs.get("kinds", None)
        )

        # Prepare CodeInfo object for aiida,
        # describes how a code has to be executed
        code = self.inputs.code
        codeinfo = CodeInfo()
        codeinfo.code_uuid = code.uuid
        codeinfo.cmdline_params = [
            os.path.splitext(self.metadata.options.input_file_name)[0]
        ]
        codeinfo.withmpi = self.metadata.options.withmpi

        # Prepare CalcInfo object for aiida
        calcinfo = CalcInfo()
        calcinfo.uuid = self.uuid
        calcinfo.codes_info = [codeinfo]
        calcinfo.local_copy_list = []
        calcinfo.remote_copy_list = []
        calcinfo.retrieve_list = [
            self.metadata.options.output_main_file_name,
            self.metadata.options.external_file_name
        ]
        calcinfo.retrieve_temporary_list = []

        return calcinfo

    # pylint: disable=too-many-arguments
    def _create_input_files(self, basissets, structure, parameters,
                            tempfolder, symmetry=None, kinds=None):
        """ create input files in temporary folder

        :param basissets:
        :param structure:
        :param parameters:
        :param setting:
        :param tempfolder:

        """
        # create .gui external geometry file and place it in tempfolder
        gui_content = gui_file_write(structure, symmetry)
        with tempfolder.open(self.metadata.options.external_file_name, 'w') as f:
            f.write(six.u("\n".join(gui_content)))

        atom_props = create_atom_properties(structure, kinds)

        # create .d12 input file and place it in tempfolder
        try:
            d12_filecontent = write_input(parameters.get_dict(),
                                          list(basissets.values()), atom_props)
        except (ValueError, NotImplementedError) as err:
            raise InputValidationError(
                "an input file could not be created from the parameters: {}".
                format(err))

        with tempfolder.open(self.metadata.options.input_file_name, 'w') as f:
            f.write(d12_filecontent)

        return True
