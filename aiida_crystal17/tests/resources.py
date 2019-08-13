"""Retrieval of test resources."""
from contextlib import contextmanager
import shutil
import tempfile

import importlib_resources
import pytest

from aiida_crystal17.tests import raw_files as resource_module

try:
    import pathlib
except ImportError:
    import pathlib2 as pathlib  # noqa: F401

# __package__ returns None in python 2.7
RESOURCE_MODULE = resource_module.__package__ or 'aiida_crystal17.tests.raw_files'


@contextmanager
def resource_context(*path, **kwargs):
    """Provide a context manager that yields a pathlib.Path object to a resource file or directory.

    If the resource does not already exist on its own on the file system,
    a temporary directory/file will be created. If the directory/file was created, it
    will be deleted upon exiting the context manager (no exception is
    raised if the directory was deleted prior to the context manager
    exiting).
    """
    if len(path) == 0:
        raise TypeError('must provide a path')
    final_name = path[-1]
    package = '.'.join([RESOURCE_MODULE] + list(path[:-1]))
    ignore = kwargs.pop('ignore', ('.DS_Store', '__init__.py'))

    if importlib_resources.is_resource(package, final_name):
        # the resource is a file
        with importlib_resources.path(package, final_name) as path:
            yield path.absolute()
    else:
        # the resource is a directory
        package = package + '.' + final_name
        # TODO if the package folder exists on the file system it would be ideal to just return that
        # but importlib_resources doesn't provide a public API for that
        resources = [
            c for c in importlib_resources.contents(package)
            if importlib_resources.is_resource(package, c) and c not in ignore
        ]
        folder_path = pathlib.Path(tempfile.mkdtemp())
        try:
            for resource in resources:
                with (folder_path / resource).open('wb') as handle:
                    handle.write(importlib_resources.read_binary(package, resource))
            yield folder_path
        finally:
            if folder_path.exists():
                shutil.rmtree(str(folder_path))


def read_resource_text(*path, **kwargs):  # Note: can't use encoding=None in python 2.7
    """Return the decoded string of the resource.

    The decoding-related arguments have the same semantics as those of
    bytes.decode().
    """
    if len(path) == 0:
        raise TypeError('must provide a path')
    file_name = path[-1]
    package = '.'.join([RESOURCE_MODULE] + list(path[:-1]))
    encoding = kwargs.pop('encoding', 'utf-8')
    return importlib_resources.read_text(package, file_name, encoding)


def read_resource_binary(*path):
    """Return the binary contents of the resource."""
    if len(path) == 0:
        raise TypeError('must provide a path')
    file_name = path[-1]
    package = '.'.join([RESOURCE_MODULE] + list(path[:-1]))
    return importlib_resources.read_binary(package, file_name)


def open_resource_text(*path, **kwargs):  # Note: can't use encoding=None in python 2.7
    """Return a file-like object opened for text reading of the resource.

    If the resource does not already exist on its own on the file system,
    a temporary file will be created. If the file was created, it
    will be deleted upon exiting the context manager (no exception is
    raised if the directory was deleted prior to the context manager
    exiting).
    """
    if len(path) == 0:
        raise TypeError('must provide a path')
    file_name = path[-1]
    package = '.'.join([RESOURCE_MODULE] + list(path[:-1]))
    encoding = kwargs.pop('encoding', 'utf-8')
    return importlib_resources.open_text(package, file_name, encoding)


def open_resource_binary(*path):
    """Return a file-like object opened for binary reading of the resource.

    If the resource does not already exist on its own on the file system,
    a temporary file will be created. If the file was created, it
    will be deleted upon exiting the context manager (no exception is
    raised if the directory was deleted prior to the context manager
    exiting).
    """
    if len(path) == 0:
        raise TypeError('must provide a path')
    file_name = path[-1]
    package = '.'.join([RESOURCE_MODULE] + list(path[:-1]))
    return importlib_resources.open_binary(package, file_name)


def get_test_structure(name):
    """Return an aiida.StructureData for testing."""
    from aiida.plugins import DataFactory
    from ase.spacegroup import crystal
    from aiida_crystal17.symmetry import convert_structure
    structure_data_cls = DataFactory('structure')
    if name == 'MgO':
        atoms = crystal(symbols=[12, 8],
                        basis=[[0, 0, 0], [0.5, 0.5, 0.5]],
                        spacegroup=225,
                        cellpar=[4.21, 4.21, 4.21, 90, 90, 90])
        return structure_data_cls(ase=atoms)
    elif name == 'NiO_afm':
        atoms = crystal(symbols=[28, 8],
                        basis=[[0, 0, 0], [0.5, 0.5, 0.5]],
                        spacegroup=225,
                        cellpar=[4.164, 4.164, 4.164, 90, 90, 90])
        atoms.set_tags([1, 1, 2, 2, 0, 0, 0, 0])
        return structure_data_cls(ase=atoms)
    elif name == 'pyrite':
        structure_data = {
            'lattice': [[5.38, 0.000000, 0.000000], [0.000000, 5.38, 0.000000], [0.000000, 0.000000, 5.38]],
            'fcoords': [[0.0, 0.0, 0.0], [0.5, 0.0, 0.5], [0.0, 0.5, 0.5], [0.5, 0.5, 0.0], [0.338, 0.338, 0.338],
                        [0.662, 0.662, 0.662], [0.162, 0.662, 0.838], [0.838, 0.338, 0.162], [0.662, 0.838, 0.162],
                        [0.338, 0.162, 0.838], [0.838, 0.162, 0.662], [0.162, 0.838, 0.338]],
            'symbols': ['Fe'] * 4 + ['S'] * 8,
            'pbc': [True, True, True]
        }
        return convert_structure(structure_data, 'aiida')
    elif name == 'marcasite':
        structure_data = {
            'lattice': [[3.37, 0.000000, 0.000000], [0.000000, 4.44, 0.000000], [0.000000, 0.000000, 5.39]],
            'ccoords': [[0.0, 0.0, 0.0], [1.685000, 2.220000, 2.695000], [0.000000, 0.901320, 2.021250],
                        [0.000000, 3.538680, 3.368750], [1.685000, 1.318680, 4.716250], [1.685000, 3.121320, 0.673750]],
            'symbols': ['Fe'] * 2 + ['S'] * 4,
            'pbc': [True, True, True]
        }
        return convert_structure(structure_data, 'aiida')
    elif name == 'zincblende':
        structure_data = {
            'pbc': [True, True, True],
            'atomic_numbers': [26, 26, 26, 26, 16, 16, 16, 16],
            'ccoords': [[0.0, 0.0, 0.0], [2.71, 2.71, 0.0], [0.0, 2.71, 2.71], [2.71, 0.0, 2.71], [1.355, 1.355, 1.355],
                        [4.065, 4.065, 1.355], [1.355, 4.065, 4.065], [4.065, 1.355, 4.065]],
            'lattice': [[5.42, 0.0, 0.0], [0.0, 5.42, 0.0], [0.0, 0.0, 5.42]],
            'equivalent': [0, 0, 0, 0, 0, 0, 0, 0]
        }
        return convert_structure(structure_data, 'aiida')
    elif name == 's2_molecule':
        structure_data = {
            'pbc': [True, False, False],
            'atomic_numbers': [16, 16],
            'ccoords': [[0.0, 0.0, 0.0], [1.89, 0.0, 0.0]],
            'lattice': [[10.0, 0.0, 0.0], [0.0, 10.0, 0.0], [0.0, 0.0, 10.0]],
            'equivalent': [0, 0]
        }
        return convert_structure(structure_data, 'aiida')
    raise ValueError(name)


@pytest.mark.cry17_calls_executable
def get_test_structure_and_symm(name, symprec=0.01, primitive=True):
    """Return an aiida.StructureData and related aiida_crystal17.SymmetryData for testing.

    SymmetryData is computed by the `crystal17.sym3d` WorkChain.
    """
    from aiida.engine import run_get_node
    from aiida.orm import Dict
    from aiida.plugins import WorkflowFactory
    instruct = get_test_structure(name)
    sym_calc = run_get_node(WorkflowFactory('crystal17.sym3d'),
                            structure=instruct,
                            settings=Dict(dict={
                                'symprec': symprec,
                                'compute_primitive': primitive
                            })).node
    return sym_calc.outputs.structure, sym_calc.outputs.symmetry
