"""
Plugin to create a CRYSTAL17 output file from a supplied input file.
"""
import os

import six

from aiida.common.datastructures import (CalcInfo, CodeInfo)
from aiida.common.exceptions import (InputValidationError, ValidationError)
from aiida.common.utils import classproperty
from aiida.engine import CalcJob
from aiida.plugins import DataFactory
SinglefileData = DataFactory('singlefile')


class CryBasicCalculation(CalcJob):
    """
    AiiDA calculation plugin wrapping the runcry17 executable.

    """
    @classmethod
    def define(cls, spec):
        # yapf: disable
        super(CryBasicCalculation, cls).define(spec)

        spec.input('metadata.options.parser_name',
                   valid_type=six.string_types, default='crystal17.basic',
                   non_db=True)
        spec.input('metadata.options.default_input_file',
                   valid_type=six.string_types, default='main.d12',
                   non_db=True)
        spec.input('metadata.options.default_external_file',
                   valid_type=six.string_types, default='main.gui',
                   non_db=True)
        spec.input('metadata.options.default_output_file',
                   valid_type=six.string_types, default='main.out',
                   non_db=True)

        spec.input(
            'input_file', valid_type=SinglefileData, required=True,
            help='the input .d12 file content.')
        spec.input(
            'input_external', valid_type=SinglefileData, required=False,
            help=('optional input .gui (fort.34) file content '
                  '(for use with EXTERNAL keyword).'))

        # spec.output()

        # TODO retrieve .f9 / .f98 from remote folder (for GUESSP or RESTART)
        # spec.input(
        #     'parent_folder', valid_type=RemoteData, required=False,
        #     help=('Use a remote folder as parent folder (for '
        #           'restarts and similar.'))

    def prepare_for_submission(self, tempfolder):
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.

        :param tempfolder: an aiida.common.folders.Folder subclass 
                           where the plugin should put all its files.
        """
        # pylint: disable=too-many-locals,too-many-statements,too-many-branches
        code = self.inputs.code
        infile = self.inputs.input_file
        try:
            ingui = self.inputs.input_external
            external_geom = True
        except AttributeError:
            ingui = None
            external_geom = False

        # Prepare CodeInfo object for aiida, describes how a code has to be executed
        codeinfo = CodeInfo()
        codeinfo.code_uuid = code.uuid
        codeinfo.cmdline_params = [
            os.path.splitext(self.inputs.default_input_file)[0]
        ]
        codeinfo.withmpi = self.metadata.options.withmpi

        # Prepare CalcInfo object for aiida
        calcinfo = CalcInfo()
        calcinfo.uuid = self.uuid
        calcinfo.codes_info = [codeinfo]
        calcinfo.local_copy_list = [[
            infile.get_file_abs_path(), self.inputs.default_input_file
        ]]
        if external_geom:
            calcinfo.local_copy_list.append(
                [ingui.get_file_abs_path(), self.inputs.default_external_file])
        calcinfo.remote_copy_list = []
        calcinfo.retrieve_list = [self.inputs.default_output_file]
        # TODO .gui won't be available for scf runs, will the computation fail if it can't find a file in retrieve list?
        # calcinfo.retrieve_list.append(self._DEFAULT_EXTERNAL_FILE)
        calcinfo.retrieve_temporary_list = []

        # TODO set hpc options (i.e. calcinfo.num_machines, etc)? Doesn't seem required looking at aiida-quantumespresso
        # (see https://aiida-core.readthedocs.io/en/latest/_modules/aiida/common/datastructures.html)

        return calcinfo
