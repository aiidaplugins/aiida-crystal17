"""
Plugin to create a CRYSTAL17 output file from input files created via data nodes
"""
import os
import copy

from aiida.common.datastructures import (CalcInfo, CodeInfo)
from aiida.common.exceptions import (InputValidationError, ValidationError)
from aiida.common.utils import classproperty
from aiida.orm import DataFactory
from aiida.orm.calculation.job import JobCalculation
from aiida_crystal17.parsers import read_schema
from aiida_crystal17.parsers.geometry import create_gui_from_struct
from aiida_crystal17.utils import unflatten_dict
from jsonextended import edict

SinglefileData = DataFactory('singlefile')
StructureData = DataFactory('structure')
ParameterData = DataFactory('parameter')


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
        # TODO add validation of input_dict
        settings = {} if settings is None else settings
        if flattened:
            settings = unflatten_dict(settings)
        setting_dict = edict.merge(
            [cls._default_settings, settings], overwrite=True)
        create_gui_from_struct(structure, setting_dict)

        return ParameterData(dict=input_dict), ParameterData(dict=settings)

    @classproperty
    def _use_methods(cls):
        """
        Add use_* methods for calculations.

        Code below enables the usage
        my_calculation.use_parameters(my_parameters)

        """
        use_dict = JobCalculation._use_methods

        use_dict.update({
            "input_file": {
                'valid_types': SinglefileData,
                'additional_parameter': None,
                'linkname': 'input_file',
                'docstring': "the input .d12 file content."
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
        # we expect "code", "input_file" and "structure"
        # "settings" is optional

        try:
            code = inputdict.pop(self.get_linkname('code'))
        except KeyError:
            raise InputValidationError("No code specified for this "
                                       "calculation")

        try:
            infile = inputdict.pop(self.get_linkname('input_file'))
        except KeyError:
            raise InputValidationError("Missing input_file")
        if not isinstance(infile, SinglefileData):
            raise InputValidationError("input_file not of type SinglefileData")

        try:
            instruct = inputdict.pop(self.get_linkname('structure'))
        except KeyError:
            raise InputValidationError("Missing structure")
        if not isinstance(instruct, StructureData):
            raise InputValidationError("structure not of type StructureData")

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

        # create .gui external geometry file and place it in tempfolder
        try:
            gui_filecontent = create_gui_from_struct(instruct, setting_dict)
        except (ValueError, NotImplementedError) as err:
            raise InputValidationError(
                "an input file could not be created from the structure: {}".
                format(err))
        gui_filename = tempfolder.get_abs_path(self._DEFAULT_EXTERNAL_FILE)
        with open(gui_filename, 'w') as gfile:
            gfile.write(gui_filecontent)

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
        calcinfo.local_copy_list = [[
            infile.get_file_abs_path(), self._DEFAULT_INPUT_FILE
        ]]
        calcinfo.remote_copy_list = []
        calcinfo.retrieve_list = [
            self._DEFAULT_OUTPUT_FILE, self._DEFAULT_EXTERNAL_FILE
        ]
        calcinfo.retrieve_temporary_list = []

        # TODO set hpc options (i.e. calcinfo.num_machines, etc)? Doesn't seem required looking at aiida-quantumespresso
        # (see https://aiida-core.readthedocs.io/en/latest/_modules/aiida/common/datastructures.html)

        return calcinfo
