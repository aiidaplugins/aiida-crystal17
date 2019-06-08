from contextlib import contextmanager
import os
import sys
import distutils.spawn

from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO


class AiidaTestApp(object):
    def __init__(self, work_directory, executable_map, environment=None):
        """a class providing methods for testing purposes

        Parameters
        ----------
        work_directory : str
            path to a local work directory (used when creating computers)
        executable_map : dict
            mapping of computation entry points to the executable name
        environment : None or aiida.manage.fixtures.FixtureManager
            manager of a temporary AiiDA environment

        """
        self._environment = environment
        self._work_directory = work_directory
        self._executables = executable_map

    @property
    def work_directory(self):
        """return path to the work directory"""
        return self._work_directory

    @property
    def environment(self):
        """return manager of a temporary AiiDA environment"""
        return self._environment

    @staticmethod
    def get_path_to_executable(executable):
        """ Get path to local executable.

        :param executable: Name of executable in the $PATH variable
        :type executable: str

        :return: path to executable
        :rtype: str

        """
        path = None

        # issue with distutils finding scripts within the python path
        # (i.e. those created by pip install)
        script_path = os.path.join(os.path.dirname(sys.executable), executable)
        if os.path.exists(script_path):
            path = script_path
        if path is None:
            path = distutils.spawn.find_executable(executable)
        if path is None:
            raise ValueError(
                "{} executable not found in PATH.".format(executable))

        return os.path.abspath(path)

    def get_or_create_computer(self, name='localhost'):
        """Setup localhost computer"""
        from aiida.orm import Computer
        from aiida.common import NotExistent

        try:
            computer = Computer.objects.get(name=name)
        except NotExistent:

            computer = Computer(
                name=name,
                hostname='localhost',
                description=('localhost computer, '
                             'set up by aiida_crystal17 tests'),
                transport_type='local',
                scheduler_type='direct',
                workdir=self.work_directory)
            computer.store()
            computer.configure()

        return computer

    def get_or_create_code(self, entry_point, computer_name='localhost'):
        """Setup code on localhost computer"""
        from aiida.orm import Code
        from aiida.common import NotExistent

        computer = self.get_or_create_computer(computer_name)

        try:
            executable = self._executables[entry_point]
        except KeyError:
            raise KeyError(
                "Entry point {} not recognized. Allowed values: {}".format(
                    entry_point, self._executables.keys()))

        try:
            code = Code.objects.get(
                label='{}-{}@{}'.format(entry_point, executable,
                                        computer_name))
        except NotExistent:
            path = self.get_path_to_executable(executable)
            code = Code(
                input_plugin_name=entry_point,
                remote_computer_exec=[computer, path],
            )
            code.label = '{}-{}@{}'.format(
                entry_point, executable, computer_name)
            code.store()

        return code

    @staticmethod
    def get_parser_cls(entry_point_name):
        """load a parser class

        Parameters
        ----------
        entry_point_name : str
            entry point name of the parser class

        Returns
        -------
        aiida.parsers.parser.Parser

        """
        from aiida.plugins import ParserFactory
        return ParserFactory(entry_point_name)

    @staticmethod
    def get_data_node(entry_point_name, **kwargs):
        """load a data node instance

        Parameters
        ----------
        entry_point_name : str
            entry point name of the data node class

        Returns
        -------
        aiida.orm.nodes.data.Data

        """
        from aiida.plugins import DataFactory
        return DataFactory(entry_point_name)(**kwargs)

    @staticmethod
    def get_calc_cls(entry_point_name):
        """load a data node class

        Parameters
        ----------
        entry_point_name : str
            entry point name of the data node class

        """
        from aiida.plugins import CalculationFactory
        return CalculationFactory(entry_point_name)

    def generate_calcjob_node(self, entry_point_name, retrieved,
                              computer_name='localhost', attributes=None):
        """Fixture to generate a mock `CalcJobNode` for testing parsers.

        Parameters
        ----------
        entry_point_name : str
            entry point name of the calculation class
        retrieved : aiida.orm.FolderData
            containing the file(s) to be parsed
        computer_name : str
            used to get or create a ``Computer``, by default 'localhost'
        attributes : None or dict
            any additional attributes to set on the node

        Returns
        -------
        aiida.orm.CalcJobNode
            instance with the `retrieved` node linked as outgoing

        """
        from aiida.common.links import LinkType
        from aiida.orm import CalcJobNode
        from aiida.plugins.entry_point import format_entry_point_string

        process = self.get_calc_cls(entry_point_name)
        computer = self.get_or_create_computer(computer_name)
        entry_point = format_entry_point_string(
            'aiida.calculations', entry_point_name)

        node = CalcJobNode(computer=computer, process_type=entry_point)
        spec_options = process.spec().inputs['metadata']['options']
        # TODO post v1.0.0b2, this can be replaced with process.spec_options
        node.set_options({
            k: v.default for k, v in spec_options.items() if v.has_default()})
        node.set_option('resources', {'num_machines': 1,
                                      'num_mpiprocs_per_machine': 1})
        node.set_option('max_wallclock_seconds', 1800)

        if attributes:
            node.set_attributes(attributes)

        node.store()

        retrieved.add_incoming(
            node, link_type=LinkType.CREATE, link_label='retrieved')
        retrieved.store()

        return node

    @contextmanager
    def sandbox_folder(self):
        """AiiDA folder object context.

        Yields
        ------
        aiida.common.folders.SandboxFolder

        """
        from aiida.common.folders import SandboxFolder
        with SandboxFolder() as folder:
            yield folder

    @staticmethod
    def generate_calcinfo(entry_point_name, folder, inputs=None):
        """generate a `CalcInfo` instance for testing calculation jobs.

        A new `CalcJob` process instance is instantiated,
        and `prepare_for_submission` is called to populate the supplied folder,
        with raw inputs.

        Parameters
        ----------
        entry_point_name: str
        folder: aiida.common.folders.Folder
        inputs: dict or None

        """
        from aiida.engine.utils import instantiate_process
        from aiida.manage.manager import get_manager
        from aiida.plugins import CalculationFactory

        manager = get_manager()
        runner = manager.get_runner()

        process_class = CalculationFactory(entry_point_name)
        process = instantiate_process(runner, process_class, **inputs)

        calc_info = process.prepare_for_submission(folder)

        return calc_info

    @staticmethod
    def check_calculation(
            calc_node, expected_outgoing_labels,
            error_include=(("results", "errors"),
                           ("results", "parser_errors"))):
        """ check a calculation has completed successfully """
        from aiida.cmdline.utils.common import get_calcjob_report
        exit_status = calc_node.get_attribute("exit_status")
        proc_state = calc_node.get_attribute("process_state")
        if exit_status != 0 or proc_state != "finished":
            yaml = YAML()
            stream = StringIO()
            yaml.dump(calc_node.attributes, stream=stream)
            message = (
                "Process Failed:\n{}".format(stream.getvalue()))
            out_link_manager = calc_node.get_outgoing()
            out_links = out_link_manager.all_link_labels()
            message += "\noutgoing_nodes: {}".format(out_links)
            for name, attribute in error_include:
                if name not in out_links:
                    continue
                value = out_link_manager.get_node_by_label(
                    name).get_attribute(attribute, None)
                if value is None:
                    continue
                message += "\n{}.{}: {}".format(name, attribute, value)
            message += "\n\nReport:\n{}".format(get_calcjob_report(calc_node))
            raise AssertionError(message)

        link_labels = calc_node.get_outgoing().all_link_labels()
        for outgoing in expected_outgoing_labels:
            if outgoing not in link_labels:
                raise AssertionError(
                    "missing outgoing node link '{}': {}".format(
                        outgoing, link_labels))
