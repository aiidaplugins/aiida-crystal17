from contextlib import contextmanager
import os
import sys
import distutils.spawn

from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO
import six


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


def get_or_create_local_computer(work_directory, name='localhost'):
    """Retrieve or setup a local computer

    Parameters
    ----------
    work_directory : str
        path to a local directory for running computations in
    name : str
        name of the computer

    Returns
    -------
    aiida.orm.computers.Computer

    """
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
            workdir=os.path.abspath(work_directory))
        computer.store()
        computer.configure()

    return computer


def get_or_create_code(entry_point, computer, executable, exec_path=None):
    """Setup code on localhost computer"""
    from aiida.orm import Code, Computer
    from aiida.common import NotExistent

    if isinstance(computer, six.string_types):
        computer = Computer.objects.get(name=computer)

    try:
        code = Code.objects.get(
            label='{}-{}@{}'.format(entry_point, executable, computer.name))
    except NotExistent:
        if exec_path is None:
            exec_path = get_path_to_executable(executable)
        code = Code(
            input_plugin_name=entry_point,
            remote_computer_exec=[computer, exec_path],
        )
        code.label = '{}-{}@{}'.format(
            entry_point, executable, computer.name)
        code.store()

    return code


def get_default_metadata(max_num_machines=1, max_wallclock_seconds=1800, with_mpi=False,
                         num_mpiprocs_per_machine=1, dry_run=False):
    """
    Return an instance of the metadata dictionary with the minimally required parameters
    for a CalcJob and set to default values unless overridden

    :param max_num_machines: set the number of nodes, default=1
    :param max_wallclock_seconds: set the maximum number of wallclock seconds, default=1800
    :param with_mpi: whether to run the calculation with MPI enabled
    :param num_mpiprocs_per_machine: set the number of cpus per node, default=1

    :rtype: dict
    """
    return {
        'options': {
            'resources': {
                'num_machines': int(max_num_machines),
                'num_mpiprocs_per_machine': int(num_mpiprocs_per_machine)
            },
            'max_wallclock_seconds': int(max_wallclock_seconds),
            'withmpi': with_mpi
        },
        'dry_run': dry_run}


def sanitize_calc_info(calc_info):
    """ convert a CalcInfo object to a regular dict,
    with no run specific data (i.e. uuids or folder paths)"""
    calc_info_dict = dict(calc_info)
    calc_info_dict.pop("uuid", None)
    code_info_dicts = [dict(c) for c in calc_info_dict.pop("codes_info")]
    [c.pop("code_uuid", None) for c in code_info_dicts]
    calc_info_dict = {
        k: sorted([v[-1] if isinstance(v, (tuple, list)) else v for v in vs])
        for k, vs in calc_info_dict.items()}
    return {
        "calc_info": calc_info_dict,
        "code_infos": code_info_dicts
    }


# TODO this can be removed once aiidateam/aiida-core#3061 is implemented
def parse_from_node(cls, node, store_provenance=True, retrieved_temporary_folder=None):
    """Parse the outputs directly from the `CalcJobNode`.

    If `store_provenance` is set to False, a `CalcFunctionNode` will still be generated, but it will not be stored.
    It's storing method will also be disabled, making it impossible to store, because storing it afterwards would
    not have the expected effect, as the outputs it produced will not be stored with it.

    This method is useful to test parsing in unit tests where a `CalcJobNode` can be mocked without actually having
    to run a `CalcJob`. It can also be useful to actually re-perform the parsing of a completed `CalcJob` with a
    different parser.

    :param node: a `CalcJobNode` instance
    :param store_provenance: bool, if True will store the parsing as a `CalcFunctionNode` in the provenance
    :return: a tuple of the parsed results and the `CalcFunctionNode` representing the process of parsing
    """
    from aiida.engine import calcfunction, Process
    from aiida.orm import Str

    parser = cls(node=node)

    @calcfunction
    def parse_calcfunction(**kwargs):
        """A wrapper function that will turn calling the `Parser.parse` method into a `CalcFunctionNode`.

        .. warning:: This implementation of a `calcfunction` uses the `Process.current` to circumvent the limitation
            of not being able to return both output nodes as well as an exit code. However, since this calculation
            function is supposed to emulate the parsing of a `CalcJob`, which *does* have that capability, I have
            to use this method. This method should however not be used in process functions, in other words:

                Do not try this at home!

        :param kwargs: keyword arguments that are passed to `Parser.parse` after it has been constructed
        """
        if "retrieved_temporary_folder" in kwargs:
            string = kwargs.pop("retrieved_temporary_folder").value
            kwargs["retrieved_temporary_folder"] = string

        exit_code = parser.parse(**kwargs)
        outputs = parser.outputs

        if exit_code and exit_code.status:
            # In the case that an exit code was returned, still attach all the registered outputs on the current
            # process as well, which should represent this `CalcFunctionNode`. Otherwise the caller of the
            # `parse_from_node` method will get an empty dictionary as a result, despite the `Parser.parse` method
            # having registered outputs.
            process = Process.current()
            process.out_many(outputs)
            return exit_code

        return dict(outputs)

    inputs = {'metadata': {'store_provenance': store_provenance}}
    inputs.update(parser.get_outputs_for_parsing())
    if retrieved_temporary_folder is not None:
        inputs["retrieved_temporary_folder"] = Str(retrieved_temporary_folder)

    return parse_calcfunction.run_get_node(**inputs)


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

    def get_or_create_computer(self, name='localhost'):
        """Setup localhost computer"""
        return get_or_create_local_computer(self.work_directory, name)

    def get_or_create_code(self, entry_point, computer_name='localhost'):
        """Setup code on localhost computer"""

        computer = self.get_or_create_computer(computer_name)

        try:
            executable = self._executables[entry_point]
        except KeyError:
            raise KeyError(
                "Entry point {} not recognized. Allowed values: {}".format(
                    entry_point, self._executables.keys()))

        return get_or_create_code(entry_point, computer, executable)

    @staticmethod
    def get_default_metadata(max_num_machines=1, max_wallclock_seconds=1800,
                             with_mpi=False, dry_run=False):
        return get_default_metadata(max_num_machines, max_wallclock_seconds,
                                    with_mpi, dry_run=dry_run)

    @staticmethod
    def parse_from_node(entry_point_name, node, retrieved_temporary_folder=None):
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
        return parse_from_node(
            ParserFactory(entry_point_name), node,
            retrieved_temporary_folder=retrieved_temporary_folder)

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

    def generate_calcjob_node(self, entry_point_name, retrieved=None,
                              computer_name='localhost',
                              options=None, mark_completed=False,
                              remote_path=None, input_nodes=None):
        """Fixture to generate a mock `CalcJobNode` for testing parsers.

        Parameters
        ----------
        entry_point_name : str
            entry point name of the calculation class
        retrieved : aiida.orm.FolderData
            containing the file(s) to be parsed
        computer_name : str
            used to get or create a ``Computer``, by default 'localhost'
        options : None or dict
            any additional metadata options to set on the node
        remote_path : str
            path to a folder on the computer
        mark_completed : bool
            if True, set the process state to finished, and the exit_status = 0
        input_nodes: dict
            mapping of link label to node

        Returns
        -------
        aiida.orm.CalcJobNode
            instance with the `retrieved` node linked as outgoing

        """
        from aiida.common.links import LinkType
        from aiida.engine import ProcessState, ExitCode
        from aiida.orm import Node, CalcJobNode, RemoteData
        from aiida.plugins.entry_point import format_entry_point_string

        process = self.get_calc_cls(entry_point_name)
        computer = self.get_or_create_computer(computer_name)
        entry_point = format_entry_point_string(
            'aiida.calculations', entry_point_name)

        calc_node = CalcJobNode(computer=computer, process_type=entry_point)
        spec_options = process.spec().inputs['metadata']['options']
        # TODO post v1.0.0b2, this can be replaced with process.spec_options
        calc_node.set_options({
            k: v.default for k, v in spec_options.items() if v.has_default()})
        calc_node.set_option('resources', {'num_machines': 1,
                                           'num_mpiprocs_per_machine': 1})
        calc_node.set_option('max_wallclock_seconds', 1800)

        if options:
            calc_node.set_options(options)

        if mark_completed:
            calc_node.set_process_state(ProcessState.FINISHED)
            calc_node.set_exit_status(ExitCode().status)

        if input_nodes is not None:
            for label, in_node in input_nodes.items():
                in_node_map = in_node
                if isinstance(in_node, Node):
                    in_node_map = {None: in_node_map}
                for sublabel, in_node in in_node_map.items():
                    in_node.store()
                    link_label = label if sublabel is None else "{}__{}".format(label, sublabel)
                    calc_node.add_incoming(
                        in_node, link_type=LinkType.INPUT_CALC, link_label=link_label)

        calc_node.store()

        if retrieved is not None:
            retrieved.add_incoming(
                calc_node, link_type=LinkType.CREATE, link_label='retrieved')
            retrieved.store()

        if remote_path is not None:
            remote = RemoteData(remote_path=remote_path,
                                computer=computer)
            remote.add_incoming(
                calc_node, link_type=LinkType.CREATE, link_label="remote_folder")
            remote.store()

        return calc_node

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
    def generate_context(wkchain_cls, inputs, outline_steps):
        """instantiate a WorkChain,
        call a list of methods (that should be part of `spec.outline`),
        then return a sanitized version of the workchain context for testing
        """
        import yaml
        from aiida.engine.utils import instantiate_process
        from aiida.common.extendeddicts import AttributeDict
        from aiida.manage.manager import get_manager
        from aiida.orm import Node

        class ContextDumper(yaml.Dumper):
            """Custom yaml dumper for a process context.
            """

            def represent_data(self, data):
                if isinstance(data, Node):
                    data = str(data.__class__)
                if isinstance(data, AttributeDict):
                    data = dict(data)

                return super(ContextDumper, self).represent_data(data)

        manager = get_manager()
        runner = manager.get_runner()

        wkchain = instantiate_process(runner, wkchain_cls, **inputs)
        step_outcomes = []
        for step in outline_steps:
            step_outcomes.append(getattr(wkchain, step)())

        context = yaml.dump(wkchain.ctx, Dumper=ContextDumper)
        return wkchain, step_outcomes, yaml.load(context)

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
