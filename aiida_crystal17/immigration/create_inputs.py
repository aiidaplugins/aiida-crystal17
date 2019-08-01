#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 Chris Sewell
#
# This file is part of aiida-crystal17.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms and conditions
# of version 3 of the GNU Lesser General Public License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
"""
module to create inputs from existing CRYSTAL17 runs
"""
import os
import tempfile

import ase
from aiida.common.exceptions import OutputParsingError
from aiida.common.folders import SandboxFolder
from aiida.plugins import DataFactory, CalculationFactory

from aiida_crystal17.parsers.raw.inputd12_read import extract_data
from aiida_crystal17.parsers.raw import crystal_stdout


# pylint: disable=too-many-locals
def populate_builder(remote_data, code=None, metadata=None):
    """ create ``crystal17.main`` input nodes from an existing run

    NB: none of the nodes are stored, also
    existing basis will be retrieved if availiable

    Parameters
    ----------
    folder: aiida.common.folders.Folder or str
        folder containing the input and output files
    remote_data: aiida.orm.RemoteData
        containing the input and output files required for parsing
    code: str or aiida.orm.nodes.data.code.Code or None
    metadata: dict or None
        calculation metadata

    Returns
    -------
    aiida.engine.processes.ProcessBuilder

    """
    calc_cls = CalculationFactory('crystal17.main')
    basis_cls = DataFactory('crystal17.basisset')
    struct_cls = DataFactory('structure')
    symmetry_cls = DataFactory('crystal17.symmetry')
    kind_cls = DataFactory('crystal17.kinds')

    # get files
    in_file_name = calc_cls.spec_options.get('input_file_name').default
    out_file_name = calc_cls.spec_options.get('output_main_file_name').default
    if metadata and 'options' in metadata:
        in_file_name = metadata['options'].get('input_file_name', in_file_name)
        out_file_name = metadata['options'].get('output_main_file_name', out_file_name)

    remote_files = remote_data.listdir()

    if in_file_name not in remote_files:
        raise IOError("The input file '{}' is not contained in the remote_data folder. "
                      'If it has a different name, change '
                      "metadata['options]['input_file_name']".format(in_file_name))
    if out_file_name not in remote_files:
        raise IOError("The output file '{}' is not contained in the remote_data folder. "
                      'If it has a different name, change '
                      "metadata['options]['output_main_file_name']".format(out_file_name))

    with SandboxFolder() as folder:
        remote_data.getfile(in_file_name, os.path.join(folder.abspath, in_file_name))

        with folder.open(in_file_name, mode='r') as handle:
            param_dict, basis_sets, atom_props = extract_data(handle.read())

        remote_data.getfile(out_file_name, os.path.join(folder.abspath, out_file_name))

        with folder.open(out_file_name, mode='r') as handle:
            try:
                data = crystal_stdout.read_crystal_stdout(handle.read())
            except IOError as err:
                raise OutputParsingError('Error in CRYSTAL 17 run output: {}'.format(err))

    # we retrieve the initial primitive geometry and symmetry
    atoms = _create_atoms(data, 'initial_geometry')

    # convert fragment (i.e. unfixed) to fixed
    if 'fragment' in atom_props:
        frag = atom_props.pop('fragment')
        atom_props['fixed'] = [i + 1 for i in range(atoms.get_number_of_atoms()) if i + 1 not in frag]

    atoms.set_tags(_create_tags(atom_props, atoms))

    structure = struct_cls(ase=atoms)

    if atom_props:
        kind_names = structure.get_kind_names()
        kinds_dict = {'kind_names': kind_names}
        for key, atom_indexes in atom_props.items():
            kv_map = {kn: i + 1 in atom_indexes for i, kn in enumerate(structure.get_site_kindnames())}
            kinds_dict[key] = [kv_map[kn] for kn in kind_names]
        kinds = kind_cls(data=kinds_dict)
    else:
        kinds = None

    symmetry = symmetry_cls(data={
        'operations': data['initial_geometry']['primitive_symmops'],
        'basis': 'fractional',
        'hall_number': None
    })

    bases = {}
    for bset in basis_sets:

        bfile = tempfile.NamedTemporaryFile(delete=False)
        try:
            with open(bfile.name, 'w') as f:
                f.write(bset)
            bdata, _ = basis_cls.get_or_create(bfile.name, use_first=False, store_basis=False)
            # TODO report if bases created or retrieved
        finally:
            os.remove(bfile.name)

        bases[bdata.element] = bdata

    builder = calc_cls.create_builder(
        param_dict, structure, bases, symmetry=symmetry, kinds=kinds, code=code, metadata=metadata)

    return builder


def _create_atoms(data, section):
    """create ase.Atoms from stdout parsed data"""
    cell_data = data[section]['primitive_cell']
    cell_vectors = []
    for n in 'a b c'.split():
        cell_vectors.append(cell_data['cell_vectors'][n])
    ccoords = cell_data['ccoords']
    atoms = ase.Atoms(cell=cell_vectors, pbc=cell_data['pbc'], symbols=cell_data['symbols'], positions=ccoords)
    return atoms


def _create_tags(atom_props, atoms):
    """create tags based on atom properties"""
    kinds = {}
    for i, symbol in enumerate(atoms.get_chemical_symbols()):
        signature = []
        kinds[symbol] = kinds.get(symbol, {})
        for key, val in atom_props.items():
            if i + 1 in val:
                signature.append(key)
        signature = '.'.join(signature)
        kinds[symbol][signature] = kinds[symbol].get(signature, []) + [i + 1]
    tags = []
    for i, symbol in enumerate(atoms.get_chemical_symbols()):
        for j, key in enumerate(sorted(kinds[symbol].keys())):
            if i + 1 in kinds[symbol][key]:
                tags.append(j)
    assert len(tags) == atoms.get_number_of_atoms()
    return tags
