"""
Plugin to create a CRYSTAL17 output file,
from input files created via data nodes
"""
import os

import six
from aiida.common.datastructures import (CalcInfo, CodeInfo)
from aiida.common.exceptions import InputValidationError
from aiida.common.utils import classproperty
from aiida.plugins import DataFactory
from aiida_crystal17.calculations.cry_abstract import CryAbstractCalculation
from aiida_crystal17.data.basis_set import get_basissets_from_structure
from aiida_crystal17.validation import read_schema
from aiida_crystal17.parsers.geometry import (
    crystal17_gui_string, structure_to_dict)
from aiida_crystal17.parsers.inputd12_write import write_input
from aiida_crystal17.utils import unflatten_dict


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
            'parameters', valid_type=DataFactory('dict'),
            required=True,
            help='the input parameters to create the .d12 file content.')
        spec.input(
            'structure', valid_type=DataFactory('structure'),
            required=True,
            help=('the structure used to construct the input .gui file '
                  '(fort.34)'))
        spec.input(
            'symmetry', valid_type=DataFactory('crystal17.structsettings'),
            required=True,
            help=('the symmetry of the structure, '
                  'used to construct the input .gui file (fort.34)'))
        spec.input_namespace(
            'basissets',
            valid_type=DataFactory('crystal17.basisset'), dynamic=True,
            help=("Use a node for the basis set of one of "
                  "the elements in the structure. You have to pass "
                  "an additional parameter ('element') specifying the "
                  "atomic element symbol for which you want to use this "
                  "basis set."))

    @classproperty
    def settings_schema(cls):
        """get a copy of the settings schema"""
        return read_schema("settings")

    @classproperty
    def input_schema(cls):
        """get a copy of the settings schema"""
        return read_schema("inputd12")

    # pylint: disable=too-many-arguments
    @classmethod
    def create_builder(cls, param_dict, structure, settings, bases,
                       code=None, options=None, flattened=False):
        """ prepare and validate the inputs to the calculation,
        and return a builder pre-populated with the calculation inputs

        :param input: dict giving data to create the input .d12 file
        :param structure: the StructureData
        :param settings: StructSettingsData giving symmetry operations, etc
        :param bases: string of the BasisSetFamily to use
        or dict of {<symbol>: <basisset>}
        :param flattened: whether the input dictionary is flattened
        :return: CalcJobBuilder
        """
        if flattened:
            param_dict = unflatten_dict(param_dict)
        # validate structure and settings
        struct_dict = structure_to_dict(structure)
        # validate parameters
        atom_props = cls._create_atom_props(struct_dict["kinds"],
                                            settings.data)
        write_input(param_dict, ["test_basis"], atom_props)
        # validate basis sets
        if isinstance(bases, six.string_types):
            symbol_to_basis_map = get_basissets_from_structure(
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

        builder = cls.get_builder()

        builder.parameters = DataFactory('dict')(dict=param_dict)
        builder.structure = structure
        builder.symmetry = settings
        builder.basissets = symbol_to_basis_map
        if code is not None:
            builder.code = code
        if options is not None:
            builder.metadata.options = options

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
            self.inputs.symmetry,
            tempfolder)

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
    def _create_input_files(self, basissets, instruct, parameters,
                            settings, tempfolder):
        """ create input files in temporary folder

        :param basissets:
        :param instruct:
        :param parameters:
        :param setting:
        :param tempfolder:
        :return: atomid_kind_map
        """
        # create .gui external geometry file and place it in tempfolder
        struct_dict = structure_to_dict(instruct)

        gui_content = crystal17_gui_string(struct_dict, settings.data)
        with tempfolder.open(self.metadata.options.external_file_name, 'w') as f:
            f.write(gui_content)

        atom_props = self._create_atom_props(struct_dict["kinds"],
                                             settings.data)

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

    @staticmethod
    def _create_atom_props(atom_kinds, setting_dict):
        """ create dict of properties for each atom

        :param atom_kinds: atom kind for each atom
        :param setting_dict: setting_dict
        :return:
        """
        atom_props = {
            "spin_alpha": [],
            "spin_beta": [],
            "fixed": [],
            "unfixed": [],
            "ghosts": []
        }

        if "kinds" in setting_dict:
            for i, kind in enumerate(atom_kinds):
                if kind.name in setting_dict["kinds"].get("spin_alpha", []):
                    atom_props["spin_alpha"].append(i + 1)
                if kind.name in setting_dict["kinds"].get("spin_beta", []):
                    atom_props["spin_beta"].append(i + 1)
                if kind.name in setting_dict["kinds"].get("fixed", []):
                    atom_props["fixed"].append(i + 1)
                if kind.name not in setting_dict["kinds"].get("fixed", []):
                    atom_props["unfixed"].append(i + 1)
                if kind.name in setting_dict["kinds"].get("ghosts", []):
                    atom_props["ghosts"].append(i + 1)

        # we only need unfixed if there are fixed
        if not atom_props.pop("fixed"):
            atom_props.pop("unfixed")

        return atom_props
