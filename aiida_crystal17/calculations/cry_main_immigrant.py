"""plugin to immigrate existing CRYSTAL17 calculation into AiiDa
"""
# TODO this won't work in AiiDa v1 see https://github.com/aiidateam/aiida_core/issues/1892
# and https://github.com/aiida-vasp/aiida-vasp/blob/develop/aiida_vasp/calcs/immigrant.py
import os

from aiida.common.datastructures import calc_states
from aiida.common.exceptions import InputValidationError, InvalidOperation
from aiida.common.folders import SandboxFolder
from aiida.common.links import LinkType
from aiida.orm.data.remote import RemoteData
from aiida_crystal17.calculations.cry_main import CryMainCalculation
from aiida_crystal17.parsers.migrate import create_inputs


class CryMainImmigrantCalculation(CryMainCalculation):
    """
    Create a CryMainCalculation object that can be used to import old jobs.

    This is a sublass of aiida_crystal17.calculations.cry_main.CryMainCalculation
    with slight modifications to some of the class variables and additional
    methods that

        a. parse the job's input file to create the calculation's input
           nodes that would exist if the calculation were submitted using AiiDa,
        b. bypass the functions of the daemon, and prepare the node's attributes
           such that all the processes (copying of the files to the repository,
           results parsing, ect.) can be performed

    .. note:: The keyword arguments of CryMainCalculation are also available.

    :param remote_workdir: Absolute path to the directory where the job was run.
        The transport of the computer you link ask input to the calculation is
        the transport that will be used to retrieve the calculation's files.
        Therefore, ``remote_workdir`` should be the absolute path to the job's
        directory on that computer.
    :type remote_workdir: str

    :param input_file_name: The file name of the job's input file.
    :type input_file_name: str

    :param output_file_name: The file name of the job's output file (i.e. the
        file containing the .out of CRYSTAL17).
    :type output_file_name: str
    """

    # TODO do we need to use/make a dummy self._DEFAULT_EXTERNAL_FILE (.gui) file

    def create_input_nodes(self,
                           open_transport,
                           input_file_name=None,
                           output_file_name=None,
                           remote_workdir=None):

        # Make sure the remote workdir and input + output file names were
        # provided either before or during the call to this method. If they
        # were just provided during this method call, store the values.
        if remote_workdir is not None:
            self.set_remote_workdir(remote_workdir)
        elif self.get_attr('remote_workdir', None) is None:
            raise InputValidationError(
                'The remote working directory has not been specified.\n'
                'Please specify it using one of the following...\n '
                '(a) pass as a keyword argument to create_input_nodes\n'
                '    [create_input_nodes(remote_workdir=your_remote_workdir)]\n'
                '(b) pass as a keyword argument when instantiating\n '
                '    [calc = PwCalculationImport(remote_workdir='
                'your_remote_workdir)]\n'
                '(c) use the set_remote_workdir method\n'
                '    [calc.set_remote_workdir(your_remote_workdir)]')
        if input_file_name is not None:
            self._DEFAULT_INPUT_FILE = input_file_name
        elif self._DEFAULT_INPUT_FILE is None:
            raise InputValidationError(
                'The input file_name has not been specified.\n'
                'Please specify it using one of the following...\n '
                '(a) pass as a keyword argument to create_input_nodes\n'
                '    [create_input_nodes(input_file_name=your_file_name)]\n'
                '(b) pass as a keyword argument when instantiating\n '
                '    [calc = PwCalculationImport(input_file_name='
                'your_file_name)]\n'
                '(c) use the set_input_file_name method\n'
                '    [calc.set_input_file_name(your_file_name)]')
        if output_file_name is not None:
            self._DEFAULT_OUTPUT_FILE = output_file_name
        elif self._DEFAULT_OUTPUT_FILE is None:
            raise InputValidationError(
                'The input file_name has not been specified.\n'
                'Please specify it using one of the following...\n '
                '(a) pass as a keyword argument to create_input_nodes\n'
                '    [create_input_nodes(output_file_name=your_file_name)]\n'
                '(b) pass as a keyword argument when instantiating\n '
                '    [calc = PwCalculationImport(output_file_name='
                'your_file_name)]\n'
                '(c) use the set_output_file_name method\n'
                '    [calc.set_output_file_name(your_file_name)]')

        # Check that open_transport is the correct transport type.
        if not isinstance(open_transport,
                          self.get_computer().get_transport_class()):
            raise InputValidationError(
                "The transport passed as the `open_transport` parameter is "
                "not the same transport type linked to the computer. Please "
                "obtain the correct transport class using the "
                "`get_transport_class` method of the calculation's computer. "
                "See the tutorial for more information.")

        # Check that open_transport is actually open.
        if not open_transport._is_open:  # pylint: disable=protected-access
            raise InvalidOperation(
                "The transport passed as the `open_transport` parameter is "
                "not open. Please execute the open the transport using it's "
                "`open` method, or execute the call to this method within a "
                "`with` statement context guard. See the tutorial for more "
                "information.")

        # Copy the input and output files to a temp folder for parsing.
        with SandboxFolder() as folder:

            # Copy the input file to the temp folder.
            remote_input_path = os.path.join(self._get_remote_workdir(),
                                             self._DEFAULT_INPUT_FILE)
            open_transport.get(remote_input_path, folder.abspath)
            local_input_path = os.path.join(folder.abspath,
                                            self._DEFAULT_INPUT_FILE)

            # Copy the input file to the temp folder.
            remote_output_path = os.path.join(self._get_remote_workdir(),
                                              self._DEFAULT_OUTPUT_FILE)
            open_transport.get(remote_output_path, folder.abspath)
            local_output_path = os.path.join(folder.abspath,
                                             self._DEFAULT_OUTPUT_FILE)

            # create inputs
            innodes = create_inputs(local_input_path, local_output_path)

        # create nodes
        self.use_parameters(innodes["parameters"])
        self.use_structure(innodes["structure"])
        self.use_settings(innodes["settings"])
        for key, node in innodes["basis"].items():
            self.use_basisset(node, key)

        self._set_attr('input_nodes_created', True)

    def _prepare_for_retrieval(self, open_transport):
        """
        Prepare the calculation for retrieval by daemon.

        :param open_transport: An open instance of the transport class of the
            calculation's computer.
        :type open_transport: aiida.transport.plugins.local.LocalTransport
            or aiida.transport.plugins.ssh.SshTransport

        Here, we

            * manually set the files to retrieve
            * store the calculation and all it's input nodes
            * copy the input file to the calculation's raw_input_folder in the
            * store the remote_workdir as a RemoteData output node

        """
        # Manually set the files that will be copied to the repository and that
        # the parser will extract the results from. This would normally be
        # performed in self._prepare_for_submission prior to submission.
        self._set_attr('retrieve_list', [self._DEFAULT_OUTPUT_FILE])
        self._set_attr('retrieve_singlefile_list', [])

        # Make sure the calculation and input links are stored.
        self.store_all()

        # Store the original input file in the calculation's repository folder.
        remote_input_path = os.path.join(self._get_remote_workdir(),
                                         self._DEFAULT_INPUT_FILE)
        open_transport.get(remote_input_path, self.folder.abspath)

        # Manually add the remote working directory as a RemoteData output
        # node.
        self._set_state(calc_states.SUBMITTING)
        remotedata = RemoteData(
            computer=self.get_computer(),
            remote_path=self._get_remote_workdir())
        remotedata.add_link_from(
            self, label='remote_folder', link_type=LinkType.CREATE)
        remotedata.store()

    def prepare_for_retrieval_and_parsing(self, open_transport):
        """
        Tell the daemon that the calculation is computed and ready to be parsed.

        :param open_transport: An open instance of the transport class of the
            calculation's computer. See the tutorial for more information.
        :type open_transport: aiida.transport.plugins.local.LocalTransport
            or aiida.transport.plugins.ssh.SshTransport

        The next time the daemon updates the status of calculations, it will
        see this job is in the 'COMPUTED' state and will retrieve its output
        files and parse the results.

        If the daemon is not currently running, nothing will happen until it is
        started again.

        This method also stores the calculation and all input nodes. It also
        copies the original input file to the calculation's repository folder.

        :raises aiida.common.exceptions.InputValidationError: if
            ``open_transport`` is a different type of transport than the
            computer's.
        :raises aiida.common.exceptions.InvalidOperation: if
            ``open_transport`` is not open.
        """
        # Check that the create_input_nodes method has run successfully.
        if not self.get_attr('input_nodes_created', False):
            raise InvalidOperation(
                "You must run the create_input_nodes method before calling "
                "prepare_for_retrieval_and_parsing!")

        # Check that open_transport is the correct transport type.
        if not isinstance(open_transport,
                          self.get_computer().get_transport_class()):
            raise InputValidationError(
                "The transport passed as the `open_transport` parameter is "
                "not the same transport type linked to the computer. Please "
                "obtain the correct transport class using the "
                "`get_transport_class` method of the calculation's computer. "
                "See the tutorial for more information.")

        # Check that open_transport is actually open.
        if not open_transport._is_open:  # pylint: disable=protected-access
            raise InvalidOperation(
                "The transport passed as the `open_transport` parameter is "
                "not open. Please execute the open the transport using it's "
                "`open` method, or execute the call to this method within a "
                "`with` statement context guard. See the tutorial for more "
                "information.")

        # Prepare the calculation for retrieval
        self._prepare_for_retrieval(open_transport)

        # Manually set the state of the calculation to "COMPUTED", so that it
        # will be retrieved and parsed the next time the daemon updates the
        # status of calculations.
        self._set_state(calc_states.COMPUTED)

    def set_remote_workdir(self, remote_workdir):
        """
        Set the job's remote working directory.

        :param remote_workdir: Absolute path of the job's remote working
            directory.
        :type remote_workdir: str
        """
        # This is the functionality as self._set_remote_workir, but it bypasses
        # the need to have the calculation state set as SUBMITTING.
        self._set_attr('remote_workdir', remote_workdir)

    def set_input_file_name(self, input_file_name):
        """
        Set the file name of the job's input file (e.g. ``'main.d12'``).

        :param input_file_name: The file name of the job's input file.
        :type input_file_name: str
        """
        self._DEFAULT_INPUT_FILE = input_file_name

    def set_output_file_name(self, output_file_name):
        """Set the file name of the job's output file (e.g. ``'pw.out'``).

        :param output_file_name: The file name of file containing the job's
            stdout.
        :type output_file_name: str
        """
        self._DEFAULT_OUTPUT_FILE = output_file_name

    # These value are set as class attributes in the parent class,
    # BasePwInputGenerator, but they will be different for a job that wasn't
    # run using aiida, and they will likely vary from job to job. Therefore,
    # we override the parent class's attributes using properties, whose
    # setter methods store the values as db attributes, and whose getter
    # methods retrieve the stored values from the db.

    @property
    def _DEFAULT_INPUT_FILE(self):
        return self.get_attr('input_file_name', None)

    @_DEFAULT_INPUT_FILE.setter
    def _DEFAULT_INPUT_FILE(self, value):
        self._set_attr('input_file_name', value)

    @property
    def _DEFAULT_OUTPUT_FILE(self):
        return self.get_attr('output_file_name', None)

    @_DEFAULT_OUTPUT_FILE.setter
    def _DEFAULT_OUTPUT_FILE(self, value):
        self._set_attr('output_file_name', value)
