"""
Plugin to create a CRYSTAL17 output file from a supplied input file.
"""
import os

import six

from aiida.common.datastructures import (CalcInfo, CodeInfo)
from aiida.engine import CalcJob
from aiida.plugins import DataFactory


class CryBasicCalculation(CalcJob):
    """
    AiiDA calculation plugin to run the runcry17 executable,
    by supplying a normal .d12 input file and (optional) .gui file
    """
    @classmethod
    def define(cls, spec):
        # yapf: disable
        super(CryBasicCalculation, cls).define(spec)

        spec.input('metadata.options.parser_name',
                   valid_type=six.string_types, default='crystal17.basic')
        spec.input('metadata.options.input_file_name',
                   valid_type=six.string_types, default='main.d12')
        spec.input('metadata.options.external_file_name',
                   valid_type=six.string_types, default='main.gui')
        spec.input('metadata.options.output_main_file_name',
                   valid_type=six.string_types, default='main.out')

        spec.input(
            'input_file', valid_type=DataFactory('singlefile'),
            required=True,
            help='the input .d12 file content.')
        spec.input(
            'input_external', valid_type=DataFactory('singlefile'),
            required=False,
            help=('optional input .gui (fort.34) file content '
                  '(for use with EXTERNAL keyword).'))

        spec.exit_code(
            30, 'ERROR_NO_RETRIEVED_FOLDER',
            message='The retrieved folder data node could not be accessed.')
        spec.exit_code(
            40, 'ERROR_OUTPUT_FILE_MISSING',
            message='the main output file was not found')

        spec.output('results', valid_type=DataFactory('dict'),
                    required=True,
                    help='the data extracted from the main output file')
        spec.output('structure', valid_type=DataFactory('structure'),
                    required=True,
                    help='the structure output from the calculation')
        spec.output('symmetry',
                    valid_type=DataFactory('crystal17.structsettings'),
                    required=True,
                    help='the symmetry data from the calculation')

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

        # Prepare CodeInfo object for aiida,
        # describes how a code has to be executed
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
        calcinfo.local_copy_list = [[
            infile.uuid, infile.filename,
            self.metadata.options.input_file_name
        ]]
        if external_geom:
            calcinfo.local_copy_list.append([
                ingui.uuid, ingui.filename,
                self.metadata.options.external_file_name])
        calcinfo.remote_copy_list = []
        calcinfo.retrieve_list = [
            self.metadata.options.output_main_file_name,
            self.metadata.options.external_file_name]
        calcinfo.retrieve_temporary_list = []

        return calcinfo
