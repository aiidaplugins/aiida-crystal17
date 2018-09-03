"""
Plugin to create a CRYSTAL17 output file from input files created via data nodes
"""
import os
import copy

import six
from aiida.common.datastructures import (CalcInfo, CodeInfo)
from aiida.common.exceptions import (InputValidationError, ValidationError)
from aiida.common.utils import classproperty
from aiida.orm import DataFactory
from aiida.orm.calculation.job import JobCalculation
from aiida_crystal17.data.basis_set import get_basissets_from_structure
from aiida_crystal17.parsers import read_schema
from aiida_crystal17.parsers.geometry import create_gui_from_struct
from aiida_crystal17.parsers.inputd12 import write_input
from aiida_crystal17.utils import unflatten_dict
from jsonextended import edict

StructureData = DataFactory('structure')
ParameterData = DataFactory('parameter')
BasisSetData = DataFactory('crystal17.basisset')


class CryMainCalculation(JobCalculation):
    """
    AiiDA calculation plugin wrapping the runcry17 executable.

    """

    _default_settings = {
        "crystal": {
            "system": "triclinic",
            "transform": None,
        },
        "symmetry": {
            "symprec": 0.01,
            "angletol": None,
            "operations": None
        },
        "kinds": {
            "basis_per": "atomic_number"
        },
        "3d": {
            "standardize": True,
            "primitive": True,
            "idealize": False
        }
    }

    def _init_internal_params(self):  # pylint: disable=useless-super-delegation
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
    def default_settings(cls):
        """get a copy of the default settings"""
        return copy.deepcopy(cls._default_settings)

    # default_settings = property(
    #     _get_default_settings, doc="the default calculation settings")

    @classproperty
    def settings_schema(cls):
        """get a copy of the settings schema"""
        return read_schema("settings")

    @classproperty
    def input_schema(cls):
        """get a copy of the settings schema"""
        return read_schema("inputd12")

    @classmethod
    def prepare_inputs(cls,
                       input_dict,
                       structure,
                       settings=None,
                       flattened=False):
        """ prepare and validate the inputs to the calculation

        :param input: dict giving data to create the input .d12 file
        :param structure: the StructureData
        :param settings: ParameterData giving
        :param flattened: whether the input (and settings) dictionary are flattened
        :return:
        """
        settings = {} if settings is None else settings
        if flattened:
            input_dict = unflatten_dict(input_dict)
            settings = unflatten_dict(settings)
        write_input(input_dict, ["test"])
        setting_dict = edict.merge(
            [cls._default_settings, settings], overwrite=True)
        create_gui_from_struct(structure, setting_dict)

        return ParameterData(dict=input_dict), ParameterData(dict=settings)

    @classmethod
    def _get_linkname_basisset_prefix(cls):
        """
        The prefix for the name of the link used for each pseudo before the kind name
        """
        return "basis_"

    @classmethod
    def _get_linkname_basisset(cls, kind):
        """
        The name of the link used for the basis set for kind 'kind'.
        It appends the pseudo name to the basisset_prefix, as returned by the
        _get_linkname_basisset_prefix() method.

        :note: if a list of strings is given, the elements are appended
          in the same order, separated by underscores

        :param kind: a string (or list of strings) for the atomic kind(s) for
            which we want to get the link name
        """
        # If it is a list of strings, and not a single string: join them
        # by underscore
        if isinstance(kind, (tuple, list)):
            suffix_string = "_".join(kind)
        elif isinstance(kind, six.string_types):
            suffix_string = kind
        else:
            raise TypeError(
                "The parameter 'kind' of _get_linkname_basisset can "
                "only be a string or a list of strings")
        return "{}{}".format(cls._get_linkname_basisset_prefix(),
                             suffix_string)

    @classproperty
    def _use_methods(cls):
        """
        Add use_* methods for calculations.

        Code below enables the usage
        my_calculation.use_parameters(my_parameters)

        """
        use_dict = JobCalculation._use_methods

        use_dict.update({
            "parameters": {
                'valid_types':
                ParameterData,
                'additional_parameter':
                None,
                'linkname':
                'input_file',
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
                ParameterData,
                'additional_parameter':
                None,
                'linkname':
                'settings',
                'docstring':
                "Settings for initial manipulation of structures "
                "and conversion to .gui (fort.34) input file",
            },
            "basisset": {
                'valid_types':
                BasisSetData,
                'additional_parameter':
                "kind",
                'linkname':
                cls._get_linkname_basisset,
                'docstring':
                ("Use a node for the basis set of one of "
                 "the elements in the structure. You have to pass "
                 "an additional parameter ('kind') specifying the "
                 "name of the structure kind (i.e., the name of "
                 "the species) for which you want to use this "
                 "basis set. You can pass either a string, or a "
                 "list of strings if more than one kind uses the "
                 "same basis set"),
            },
            # TODO retrieve .f9 / .f98 from remote folder (for GUESSP or RESTART)
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
        Set the basis set to use for all atomic kinds, picking basis sets from the
        family with name family_name.

        :note: The structure must already be set.

        :param family_name: the name of the group containing the basis sets
        """
        from collections import defaultdict

        try:
            structure = self._get_reference_structure()
        except AttributeError:
            raise ValueError(
                "Structure is not set yet! Therefore, the method "
                "use_basisset_from_family cannot automatically set "
                "the basis sets")

        # A dict {kind_name: basisset_object}
        kind_basis_dict = get_basissets_from_structure(structure, family_name)

        # We have to group the species by basis, I use the basis PK
        # basis_dict will just map PK->basis_object
        basis_dict = {}
        # Will contain a list of all species of the basis with given PK
        basis_species = defaultdict(list)

        for kindname, basis in kind_basis_dict.iteritems():
            basis_dict[basis.pk] = basis
            basis_species[basis.pk].append(kindname)

        for basis_pk in basis_dict:
            basis = basis_dict[basis_pk]
            kinds = basis_species[basis_pk]
            # I set the basis for all species, sorting alphabetically
            self.use_basis(basis, sorted(kinds))

    def _get_reference_structure(self):
        """
        Used to get the reference structure to obtain which
        basis sets to use from a given family using
        use_basiss_from_family.

        :note: this method can be redefined in a given subclass
               to specify which is the reference structure to consider.
        """
        return self.get_inputs_dict()[self.get_linkname('structure')]

    def _retrieve_basis_sets(self, inputdict, instruct):
        """ retrieve BasisSetData objects from the inputdict, associate them with a kind
        and validate a 1-to-1 mapping between the two

        :param inputdict: dictionary of inputs
        :param instruct: input StructureData
        :return: basissets dict {kind: BasisSetData}
        """
        basissets = {}
        # I create here a dictionary that associates each kind name to a basisset
        for link in inputdict.keys():
            if link.startswith(self._get_linkname_basisset_prefix()):
                kindstring = link[len(self._get_linkname_basisset_prefix()):]
                kinds = kindstring.split('_')
                the_basisset = inputdict.pop(link)
                if not isinstance(the_basisset, BasisSetData):
                    raise InputValidationError(
                        "basisset for kind(s) {} is not of "
                        "type BasisSetData".format(",".join(kinds)))
                for kind in kinds:
                    if kind in basissets:
                        raise InputValidationError(
                            "basisset for kind {} passed "
                            "more than one time".format(kind))
                    basissets[kind] = the_basisset

        # Check structure, get species, check basissets
        kindnames = [k.name for k in instruct.kinds]
        if set(kindnames) != set(basissets.keys()):
            err_msg = (
                "Mismatch between the defined basissets and the list of "
                "kinds of the structure. Basissets: {}; kinds: {}".format(
                    ",".join(basissets.keys()), ",".join(list(kindnames))))
            raise InputValidationError(err_msg)

        return basissets

    # pylint: disable=too-many-arguments
    def _create_input_files(self, basissets, instruct, parameters,
                            setting_dict, tempfolder):
        """ create input files in temporary folder

        :param basissets:
        :param instruct:
        :param parameters:
        :param setting_dict:
        :param tempfolder:
        :return:
        """
        # create .gui external geometry file and place it in tempfolder
        try:
            gui_filecontent = create_gui_from_struct(instruct, setting_dict)
        except (ValueError, NotImplementedError) as err:
            raise InputValidationError(
                "an input geometry file could not be created from the structure: {}".
                format(err))
        gui_filename = tempfolder.get_abs_path(self._DEFAULT_EXTERNAL_FILE)
        with open(gui_filename, 'w') as gfile:
            gfile.write(gui_filecontent)

        # create .d12 input file and place it in tempfolder
        try:
            d12_filecontent = write_input(parameters.get_dict(),
                                          list(basissets.values()))
        except (ValueError, NotImplementedError) as err:
            raise InputValidationError(
                "an input file could not be created from the parameters: {}".
                format(err))
        d12_filename = tempfolder.get_abs_path(self._DEFAULT_INPUT_FILE)
        with open(d12_filename, 'w') as dfile:
            dfile.write(d12_filecontent)

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
        # we expect "code", "parameters", "structure" and "basis_" (one for each basis)
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
        if not isinstance(parameters, ParameterData):
            raise InputValidationError("input_file not of type ParameterData")

        try:
            instruct = inputdict.pop(self.get_linkname('structure'))
        except KeyError:
            raise InputValidationError("Missing structure")
        if not isinstance(instruct, StructureData):
            raise InputValidationError("structure not of type StructureData")

        basissets = self._retrieve_basis_sets(inputdict, instruct)

        # Settings can be undefined, and defaults to an empty dictionary
        settings = inputdict.pop(self.get_linkname('settings'), None)
        if settings is None:
            input_settings = {}
        else:
            if not isinstance(settings, ParameterData):
                raise InputValidationError(
                    "settings, if specified, must be of "
                    "type ParameterData")
            input_settings = settings.get_dict()

        if inputdict:
            raise ValidationError(
                "Unknown additional inputs: {}".format(inputdict))

        # update default settings
        setting_dict = edict.merge(
            [self._default_settings, input_settings], overwrite=True)

        self._create_input_files(basissets, instruct, parameters, setting_dict,
                                 tempfolder)

        # Prepare CodeInfo object for aiida, describes how a code has to be executed
        codeinfo = CodeInfo()
        codeinfo.code_uuid = code.uuid
        codeinfo.cmdline_params = [
            os.path.splitext(self._DEFAULT_INPUT_FILE)[0]
        ]
        # codeinfo.stdout_name = self._DEFAULT_OUTPUT_FILE  # this file doesn't actually come from stdout
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

        # TODO set hpc options (i.e. calcinfo.num_machines, etc)? Doesn't seem required looking at aiida-quantumespresso
        # (see https://aiida-core.readthedocs.io/en/latest/_modules/aiida/common/datastructures.html)

        return calcinfo
