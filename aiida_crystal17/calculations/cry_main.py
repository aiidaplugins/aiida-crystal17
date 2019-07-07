"""
Plugin to create a CRYSTAL17 output file,
from input files created via data nodes
"""
import os
import six

from aiida.common.exceptions import InputValidationError
from aiida.orm import Code, RemoteData, StructureData, TrajectoryData
from aiida.plugins import DataFactory

from aiida_crystal17.calculations.cry_abstract import CryAbstractCalculation
from aiida_crystal17.parsers.raw.gui_parse import gui_file_write
from aiida_crystal17.parsers.raw.inputd12_write import (
    write_input, create_atom_properties)


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
            'parameters', valid_type=DataFactory('crystal17.parameters'),
            required=True,
            serializer=lambda x: DataFactory('crystal17.parameters')(data=x),
            help='the input parameters to create the .d12 file content.')
        spec.input(
            'structure', valid_type=StructureData,
            required=True,
            help='structure used to construct the input fort.34 (gui) file')
        spec.input(
            'symmetry', valid_type=DataFactory('crystal17.symmetry'),
            required=False,
            help=('the symmetry of the structure, '
                  'used to construct the input .gui file (fort.34)'))
        spec.input(
            'kinds', valid_type=DataFactory('crystal17.kinds'),
            required=False,
            help=('additional structure kind specific data '
                  '(e.g. initial spin)'))
        spec.input_namespace(
            'basissets',
            valid_type=DataFactory('crystal17.basisset'), dynamic=True,
            help=("Use a node for the basis set of one of "
                  "the elements in the structure. You have to pass "
                  "an additional parameter ('element') specifying the "
                  "atomic element symbol for which you want to use this "
                  "basis set."))

        spec.input(
            'parent_folder', valid_type=RemoteData, required=False,
            help=('An optional working directory, '
                  'of a previously completed calculation to restart from'))

        spec.output(
            'optimisation',
            valid_type=TrajectoryData, required=False,
            help="atomic configurations, for each optimisation step")

    # pylint: disable=too-many-arguments
    @classmethod
    def create_builder(cls, parameters, structure, bases,
                       symmetry=None, kinds=None,
                       code=None, metadata=None, unflatten=False):
        """ prepare and validate the inputs to the calculation,
        and return a builder pre-populated with the calculation inputs

        Parameters
        ----------
        parameters: dict or CryInputParamsData
            input parameters to create the input .d12 file
        structure: aiida.orm.StructureData
            the structure node
        bases: str or dict
            string of the BasisSetFamily to use,
            or dict mapping {<symbol>: <BasisSetData>}
        symmetry: SymmetryData or None
            giving symmetry operations, etc
        metadata: dict
            the computation metadata, e.g.
            {"options": {"resources": {"num_machines": 1, "num_mpiprocs_per_machine": 1}}}
        unflatten: bool
            whether to unflatten the input parameters dictionary

        Returns
        -------
        aiida.engine.processes.ProcessBuilder

        """
        builder = cls.get_builder()
        param_cls = DataFactory('crystal17.parameters')
        if not isinstance(parameters, param_cls):
            parameters = param_cls(data=parameters, unflatten=unflatten)
        builder.parameters = parameters
        builder.structure = structure
        if symmetry is not None:
            builder.symmetry = symmetry
        if kinds is not None:
            builder.kinds = kinds
        if code is not None:
            if isinstance(code, six.string_types):
                code = Code.get_from_string(code)
            builder.code = code
        if metadata is not None:
            builder.metadata = metadata

        # validate parameters
        atom_props = create_atom_properties(structure, kinds)
        write_input(parameters.get_dict(), ["test_basis"], atom_props)

        # validate basis sets
        basis_cls = DataFactory('crystal17.basisset')
        if isinstance(bases, six.string_types):
            symbol_to_basis_map = basis_cls.get_basissets_from_structure(
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

        builder.basissets = symbol_to_basis_map

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

        # set the initial parameters
        parameters = self.inputs.parameters.get_dict()
        restart_fnames = []
        remote_copy_list = []

        # deal with restarts
        if "parent_folder" in self.inputs:
            restart_fnames, remote_copy_list = self._check_restart(
                self.inputs.parent_folder)
            parameters = self._modify_parameters(parameters, restart_fnames)

        # create fort.34 external geometry file and place it in tempfolder
        gui_content = gui_file_write(self.inputs.structure,
                                     self.inputs.get("symmetry", None))
        with tempfolder.open("fort.34", 'w') as f:
            f.write(six.u("\n".join(gui_content)))

        # create .d12 input file and place it in tempfolder
        atom_props = create_atom_properties(
            self.inputs.structure, self.inputs.get("kinds", None))
        try:
            d12_filecontent = write_input(
                parameters, list(self.inputs.basissets.values()), atom_props)
        except (ValueError, NotImplementedError) as err:
            raise InputValidationError(
                "an input file could not be created from the parameters: {}".
                format(err))
        with tempfolder.open(self.metadata.options.input_file_name, 'w') as f:
            f.write(d12_filecontent)

        # setup the calculation info
        return self.create_calc_info(
            tempfolder,
            remote_copy_list=remote_copy_list,
            retrieve_list=[
                self.metadata.options.output_main_file_name,
                "fort.34",
                "HESSOPT.DAT"
            ],
            retrieve_temporary_list=["opt[ac][0-9][0-9][0-9]"]
        )

    @staticmethod
    def _check_restart(parent_folder):
        """assess the parent folder, to decide what files should be copied

        Parameters
        ----------
        parent_folder : aiida.orm.nodes.data.remote.RemoteData

        Returns
        -------
        list: restart_fnames
        list: remote_copy_list

        Notes
        -----

        - fort.9 provides restart for SCF (with GUESSP),
          but is only output at the end of a successful run
        - HESSOPT.DAT can be used to initialise the hessian matrix (HESSOPT),
          and is updated after every optimisation step
        - OPTINFO.DAT is meant for geometry restarts (with RESTART) but,
          on both crystal and Pcrystal, a read file error is encountered.

        """
        # open a transport to the parent computer, and find viable restart files
        trans = parent_folder.get_authinfo().get_transport()
        restart_fnames = {}
        remote_copy_list = []
        # TODO this will fail if not connected to the remote path,
        # but if the calculation is part of a workflow this would be unwanted
        # (i.e. should be paused until connection is established)
        with trans:
            if not trans.isdir(parent_folder.get_remote_path()):
                raise IOError("the parent_folders remote path does not exist "
                              "on the remote computer")
            trans.chdir(parent_folder.get_remote_path())
            for fname in trans.listdir():
                if trans.isdir(fname):
                    continue
                if fname == "HESSOPT.DAT" and trans.get_attribute(fname).st_size > 0:
                    restart_fnames[fname] = fname
                elif fname == "fort.9" and trans.get_attribute(fname).st_size > 0:
                    restart_fnames["fort.20"] = "fort.9"

        for oname, iname in restart_fnames.items():
            remote_copy_list.append((
                parent_folder.computer.uuid,
                os.path.join(parent_folder.get_remote_path(), iname),
                oname))

        return restart_fnames, remote_copy_list

    @staticmethod
    def _modify_parameters(parameters, restart_fnames):
        """ modify the parameters,
        according to what restart files are available
        """
        if not restart_fnames:
            return parameters

        if "fort.20" in restart_fnames:
            parameters["scf"]["GUESSP"] = True

        if "HESSOPT.DAT" in restart_fnames:
            if parameters.get("geometry", {}).get("optimise", False):
                if isinstance(parameters["geometry"]["optimise"], bool):
                    parameters["geometry"]["optimise"] = {}
                parameters["geometry"]["optimise"]["hessian"] = "HESSOPT"

        # Note this is currently not used
        if "OPTINFO.DAT" in restart_fnames:
            if parameters.get("geometry", {}).get("optimise", False):
                if isinstance(parameters["geometry"]["optimise"], bool):
                    parameters["geometry"]["optimise"] = {}
                parameters["geometry"]["optimise"]["restart"] = True

        return parameters
