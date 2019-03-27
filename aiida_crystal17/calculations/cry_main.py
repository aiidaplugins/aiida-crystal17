"""
Plugin to create a CRYSTAL17 output file, 
from input files created via data nodes
"""
import os

import six
from aiida.common.datastructures import (CalcInfo, CodeInfo)
from aiida.common.exceptions import (InputValidationError, ValidationError)
from aiida.common.utils import classproperty
from aiida.plugins import DataFactory
from aiida.engine import CalcJob
from aiida_crystal17.data.basis_set import get_basissets_from_structure
from aiida_crystal17.validation import read_schema
from aiida_crystal17.parsers.geometry import (
    crystal17_gui_string, structure_to_dict)
from aiida_crystal17.parsers.inputd12_write import write_input
from aiida_crystal17.utils import unflatten_dict, ATOMIC_NUM2SYMBOL

StructureData = DataFactory('structure')
DictData = DataFactory('dict')
BasisSetData = DataFactory('crystal17.basisset')
StructSettingsData = DataFactory('crystal17.structsettings')


class CryMainCalculation(CalcJob):
    """
    AiiDA calculation plugin wrapping the runcry17 executable.

    """

    def _init_internal_params(self):
        """
        Init internal parameters at class load time
        """
        # reuse base class function
        super(CryMainCalculation, self)._init_internal_params()

        # default input and output files
        self._DEFAULT_INPUT_FILE = 'main.d12'
        self._DEFAULT_EXTERNAL_FILE = 'main.gui'
        self._DEFAULT_OUTPUT_FILE = 'main.out'

        # parser entry point defined in setup.json
        self._default_parser = 'crystal17.basic'

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
    def prepare_and_validate(cls,
                             param_dict,
                             structure,
                             settings,
                             basis_family=None,
                             flattened=False):
        """ prepare and validate the inputs to the calculation

        :param input: dict giving data to create the input .d12 file
        :param structure: the StructureData
        :param settings: StructSettingsData giving symmetry operations, etc
        :param basis_family: string of the BasisSetFamily to use
        :param flattened: whether the input dictionary is flattened
        :return: parameters
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
        if basis_family:
            get_basissets_from_structure(
                structure, basis_family, by_kind=False)

        return DictData(dict=param_dict)

    @classmethod
    def _get_linkname_basisset_prefix(cls):
        """The prefix for the name of the link used
        for each pseudo before the kind name
        """
        return "basis_"

    @classmethod
    def get_linkname_basisset(cls, element):
        """The name of the link used for the basis set 
        for atomic element 'element'.
        It appends the basis name to the basisset_prefix, as returned by the
        _get_linkname_basisset_prefix() method.

        :param element: a string for the atomic element 
                        for which we want to get the link name
        """
        if not isinstance(element, six.string_types):
            raise TypeError(
                "The parameter 'element' of _get_linkname_basisset can "
                "only be an string: {}".format(element))
        if element not in ATOMIC_NUM2SYMBOL.values():
            raise TypeError(
                "The parameter 'symbol' of _get_linkname_basisset can "
                "must be a known atomic element: {}".format(element))

        return "{}{}".format(cls._get_linkname_basisset_prefix(), element)

    @classproperty
    def _use_methods(cls):
        """
        Add use_* methods for calculations.

        Code below enables the usage
        my_calculation.use_parameters(my_parameters)

        """
        use_dict = CalcJob._use_methods

        use_dict.update({
            "parameters": {
                'valid_types':
                DictData,
                'additional_parameter':
                None,
                'linkname':
                'parameters',
                'docstring':
                "the input parameters to create the .d12 file content."
            },
            "structure": {
                'valid_types': StructureData,
                'additional_parameter': None,
                'linkname': 'structure',
                'docstring': "structure to use."
            },
            "settings": {
                'valid_types':
                StructSettingsData,
                'additional_parameter':
                None,
                'linkname':
                'settings',
                'docstring':
                "Structure settings for conversion to .gui (fort.34) input "
                "file defining symmetry operations and kind specific data",
            },
            "basisset": {
                'valid_types':
                BasisSetData,
                'additional_parameter':
                "element",
                'linkname':
                cls.get_linkname_basisset,
                'docstring':
                ("Use a node for the basis set of one of "
                 "the elements in the structure. You have to pass "
                 "an additional parameter ('element') specifying the "
                 "atomic element symbol for which you want to use this "
                 "basis set."),
            },
            # TODO retrieve .f9 / .f98 from remote folder (for GUESSP/RESTART)
            # "parent_folder": {
            #     'valid_types': RemoteData,
            #     'additional_parameter': None,
            #     'linkname': 'parent_calc_folder',
            #     'docstring': ("Use a remote folder as parent folder (for "
            #                   "restarts and similar"),
            # },
        })

        return use_dict

    def use_basisset_from_family(self, family_name):
        """
        Set the basis set to use for all atomic types, picking basis sets from 
        the family with name family_name.

        :note: The structure must already be set.

        :param family_name: the name of the group containing the basis sets
        """
        try:
            structure = self._get_reference_structure()
        except AttributeError:
            raise ValueError(
                "Structure is not set yet! Therefore, the method "
                "use_basisset_from_family cannot automatically set "
                "the basis sets")

        # A dict {element: basisset_object}
        element_basis_dict = get_basissets_from_structure(
            structure, family_name, by_kind=False)

        for element, basis in element_basis_dict.items():
            self.use_basisset(basis, element)

    def _get_reference_structure(self):
        """
        Used to get the reference structure to obtain which
        basis sets to use from a given family using
        use_basisset_from_family.

        :note: this method can be redefined in a given subclass
               to specify which is the reference structure to consider.
        """
        return self.get_incoming()[self.get_linkname('structure')]

    def _retrieve_basis_sets(self, inputdict, instruct):
        """ retrieve BasisSetData objects from the inputdict, 
        associate them with an atomic element
        and validate a 1-to-1 mapping between the two

        :param inputdict: dictionary of inputs
        :param instruct: input StructureData
        :return: basissets dict {element: BasisSetData}
        """
        basissets = {}
        # I create here a dictionary that 
        # associates each kind name to a basisset
        for link in list(inputdict.keys()):
            if link.startswith(self._get_linkname_basisset_prefix()):
                element = link[len(self._get_linkname_basisset_prefix()):]
                the_basisset = inputdict.pop(link)
                if not isinstance(the_basisset, BasisSetData):
                    raise InputValidationError(
                        "basisset for element '{}' is not of "
                        "type BasisSetData".format(element))
                basissets[element] = the_basisset

        # Check retrieved elements match the required elements
        elements_required = [k.symbol for k in instruct.kinds]
        if set(elements_required) != set(basissets.keys()):
            err_msg = (
                "Mismatch between the defined basissets and the list of "
                "elements of the structure. Basissets: {}; elements: {}".
                format(",".join(basissets.keys()), ",".join(
                    list(elements_required))))
            raise InputValidationError(err_msg)

        return basissets

    # pylint: disable=too-many-arguments
    def _create_input_files(self, basissets, instruct, parameters,
                            settings_dict, tempfolder):
        """ create input files in temporary folder

        :param basissets:
        :param instruct:
        :param parameters:
        :param setting_dict:
        :param tempfolder:
        :return: atomid_kind_map
        """
        # create .gui external geometry file and place it in tempfolder
        struct_dict = structure_to_dict(instruct)

        gui_content = crystal17_gui_string(struct_dict, settings_dict)
        with open(tempfolder.get_abs_path(self._DEFAULT_EXTERNAL_FILE),
                  'w') as f:
            f.write(gui_content)

        atom_props = self._create_atom_props(struct_dict["kinds"],
                                             settings_dict)

        # create .d12 input file and place it in tempfolder
        try:
            d12_filecontent = write_input(parameters.get_dict(),
                                          list(basissets.values()), atom_props)
        except (ValueError, NotImplementedError) as err:
            raise InputValidationError(
                "an input file could not be created from the parameters: {}".
                format(err))

        with open(tempfolder.get_abs_path(self._DEFAULT_INPUT_FILE), 'w') as f:
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

    def _prepare_for_submission(self, tempfolder, inputdict):
        """
        Create input files.

            :param tempfolder: aiida.common.folders.Folder subclass where
                the plugin should put all its files.
            :param inputdict: dictionary of the input nodes as they would
                be returned by get_inputs_dict

        See https://aiida-core.readthedocs.io/en/latest/
        developer_guide/devel_tutorial/code_plugin_qe.html#step-3-prepare-a-text-input
        for a description of its function and inputs
        """
        # read inputs
        # we expect "code", "parameters", "structure" and "basis_" 
        # (one for each basis)
        # "settings" is optional

        try:
            code = inputdict.pop(self.get_linkname('code'))
        except KeyError:
            raise InputValidationError("No code specified for this "
                                       "calculation")

        try:
            parameters = inputdict.pop(self.get_linkname('parameters'))
        except KeyError:
            raise InputValidationError("Missing parameters")
        if not isinstance(parameters, DictData):
            raise InputValidationError("parameters not of type DictData")

        try:
            instruct = inputdict.pop(self.get_linkname('structure'))
        except KeyError:
            raise InputValidationError("Missing structure")
        if not isinstance(instruct, StructureData):
            raise InputValidationError("structure not of type StructureData")

        try:
            settings = inputdict.pop(self.get_linkname('settings'))
        except KeyError:
            raise InputValidationError("Missing settings")
        if not isinstance(settings, StructSettingsData):
            raise InputValidationError(
                "settings not of type StructSettingsData")

        basissets = self._retrieve_basis_sets(inputdict, instruct)

        if inputdict:
            raise ValidationError(
                "Unknown additional inputs: {}".format(inputdict))

        self._create_input_files(basissets, instruct, parameters,
                                 settings.data, tempfolder)

        # Prepare CodeInfo object for aiida, 
        # describes how a code has to be executed
        codeinfo = CodeInfo()
        codeinfo.code_uuid = code.uuid
        codeinfo.cmdline_params = [
            os.path.splitext(self._DEFAULT_INPUT_FILE)[0]
        ]
        # codeinfo.stdout_name = self._DEFAULT_OUTPUT_FILE  
        # # this file doesn't actually come from stdout
        codeinfo.withmpi = self.get_withmpi()

        # Prepare CalcInfo object for aiida
        calcinfo = CalcInfo()
        calcinfo.uuid = self.uuid
        calcinfo.codes_info = [codeinfo]
        calcinfo.local_copy_list = []
        calcinfo.remote_copy_list = []
        calcinfo.retrieve_list = [
            self._DEFAULT_OUTPUT_FILE, self._DEFAULT_EXTERNAL_FILE
        ]
        calcinfo.retrieve_temporary_list = []

        return calcinfo
