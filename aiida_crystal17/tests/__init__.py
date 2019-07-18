""" tests for the plugin that does not pollute your profiles/databases.
"""
import os

TEST_FILES = os.path.join(os.path.dirname(os.path.realpath(__file__)), "raw_files")


def get_test_structure(name):
    """ return an aiida.StructureData for testing """
    from aiida.plugins import DataFactory
    from ase.spacegroup import crystal
    from aiida_crystal17.symmetry import convert_structure
    structure_data_cls = DataFactory('structure')
    if name == "MgO":
        atoms = crystal(
            symbols=[12, 8],
            basis=[[0, 0, 0], [0.5, 0.5, 0.5]],
            spacegroup=225,
            cellpar=[4.21, 4.21, 4.21, 90, 90, 90])
        return structure_data_cls(ase=atoms)
    elif name == "NiO_afm":
        atoms = crystal(
            symbols=[28, 8],
            basis=[[0, 0, 0], [0.5, 0.5, 0.5]],
            spacegroup=225,
            cellpar=[4.164, 4.164, 4.164, 90, 90, 90])
        atoms.set_tags([1, 1, 2, 2, 0, 0, 0, 0])
        return structure_data_cls(ase=atoms)
    elif name == "pyrite":
        structure_data = {
            "lattice": [[5.38, 0.000000, 0.000000],
                        [0.000000, 5.38, 0.000000],
                        [0.000000, 0.000000, 5.38]],
            "fcoords": [[0.0, 0.0, 0.0], [0.5, 0.0, 0.5], [0.0, 0.5, 0.5],
                        [0.5, 0.5, 0.0], [0.338, 0.338, 0.338],
                        [0.662, 0.662, 0.662], [0.162, 0.662, 0.838],
                        [0.838, 0.338, 0.162], [0.662, 0.838, 0.162],
                        [0.338, 0.162, 0.838], [0.838, 0.162, 0.662],
                        [0.162, 0.838, 0.338]],
            "symbols": ['Fe'] * 4 + ['S'] * 8,
            "pbc": [True, True, True]
        }
        return convert_structure(structure_data, "aiida")
    elif name == "marcasite":
        structure_data = {
            "lattice": [[3.37, 0.000000, 0.000000],
                        [0.000000, 4.44, 0.000000],
                        [0.000000, 0.000000, 5.39]],
            "ccoords": [[0.0, 0.0, 0.0],
                        [1.685000,    2.220000,    2.695000],
                        [0.000000,    0.901320,    2.021250],
                        [0.000000,    3.538680,    3.368750],
                        [1.685000,    1.318680,    4.716250],
                        [1.685000,    3.121320,    0.673750]],
            "symbols": ['Fe'] * 2 + ['S'] * 4,
            "pbc": [True, True, True]
        }
        return convert_structure(structure_data, "aiida")
    elif name == "zincblende":
        structure_data = {
            'pbc': [True, True, True],
            'atomic_numbers': [26, 26, 26, 26, 16, 16, 16, 16],
            'ccoords': [[0.0, 0.0, 0.0],
                        [2.71, 2.71, 0.0],
                        [0.0, 2.71, 2.71],
                        [2.71, 0.0, 2.71],
                        [1.355, 1.355, 1.355],
                        [4.065, 4.065, 1.355],
                        [1.355, 4.065, 4.065],
                        [4.065, 1.355, 4.065]],
            'lattice': [[5.42, 0.0, 0.0],
                        [0.0, 5.42, 0.0],
                        [0.0, 0.0, 5.42]],
            'equivalent': [0, 0, 0, 0, 0, 0, 0, 0]}
        return convert_structure(structure_data, "aiida")
    elif name == "s2_molecule":
        structure_data = {
            'pbc': [True, False, False],
            'atomic_numbers': [16, 16],
            'ccoords': [[0.0, 0.0, 0.0],
                        [1.89, 0.0, 0.0]],
            'lattice': [[10.0, 0.0, 0.0],
                        [0.0, 10.0, 0.0],
                        [0.0, 0.0, 10.0]],
            'equivalent': [0, 0]}
        return convert_structure(structure_data, "aiida")
    raise ValueError(name)


def get_test_structure_and_symm(name, symprec=0.01, primitive=True):
    """ return an aiida.StructureData
    and related aiida_crystal17.SymmetryData (computed by the `crystal17.sym3d` WorkChain)
    for testing """
    from aiida.engine import run_get_node
    from aiida.orm import Dict
    from aiida.plugins import WorkflowFactory
    instruct = get_test_structure(name)
    sym_calc = run_get_node(
        WorkflowFactory("crystal17.sym3d"), structure=instruct,
        settings=Dict(dict={"symprec": symprec, "compute_primitive": primitive})
    ).node
    return sym_calc.outputs.structure, sym_calc.outputs.symmetry
