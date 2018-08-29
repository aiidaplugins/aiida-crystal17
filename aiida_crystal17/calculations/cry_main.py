"""
Plugin to create a CRYSTAL17 output file from input files created via data nodes
"""
import os

from aiida.common.datastructures import (CalcInfo, CodeInfo)
from aiida.common.exceptions import (InputValidationError, ValidationError)
from aiida.common.utils import classproperty
from aiida.orm import DataFactory
from aiida.orm.calculation.job import JobCalculation

SinglefileData = DataFactory('singlefile')
StructureData = DataFactory('structure')
ParameterData = DataFactory('parameter')


class CryMainCalculation(JobCalculation):
    """
    AiiDA calculation plugin wrapping the runcry17 executable.

    """

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
                'valid_types': ParameterData,
                'additional_parameter': None,
                'linkname': 'settings',
                'docstring': "Use an additional node for special settings",
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
            settings_dict = {}
        else:
            if not isinstance(settings, ParameterData):
                raise InputValidationError(
                    "settings, if specified, must be of "
                    "type ParameterData")

        if inputdict:
            raise ValidationError(
                "Unknown additional inputs: {}".format(inputdict))

        # create .gui external geometry file and place it in tempfolder
        gui_filecontent = ""  # TODO create .gui content
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
