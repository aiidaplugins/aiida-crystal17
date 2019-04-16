"""
module to create inputs from existing CRYSTAL17 runs
"""
import os
import tempfile

import ase
from aiida.common.exceptions import OutputParsingError
from aiida_crystal17.parsers.inputd12_read import extract_data
from ejplugins.crystal import CrystalOutputPlugin


# pylint: disable=too-many-locals
def populate_builder(folder, input_name="main.d12", output_name="main.out", code=None):
    """ create ``crystal17.main`` input nodes from an existing run

    NB: none of the nodes are stored, also
    existing basis will be retrieved if availiable

    Parameters
    ----------
    inpath: str
        path to .d12 file
    outpath: str
        path to .out file

    Returns
    -------
    aiida.engine.processes.ProcessBuilder

    """
    from aiida.plugins import DataFactory, CalculationFactory
    calc_cls = CalculationFactory('crystal17.main')
    basis_cls = DataFactory('crystal17.basisset')
    struct_cls = DataFactory('structure')
    symmetry_cls = DataFactory('crystal17.symmetry')
    kind_cls = DataFactory('crystal17.kinds')

    with folder.open(input_name, mode='r') as f:
        d12content = f.read()

    output_dict, basis_sets, atom_props = extract_data(d12content)

    cryparse = CrystalOutputPlugin()
    with folder.open(output_name, mode='r') as f:
        try:
            data = cryparse.read_file(f, log_warnings=False)
        except IOError as err:
            raise OutputParsingError(
                "Error in CRYSTAL 17 run output: {}".format(err))

    # we retrieve the initial primitive geometry and symmetry
    atoms = _create_atoms(data)

    # convert fragment (i.e. unfixed) to fixed
    if "fragment" in atom_props:
        frag = atom_props.pop("fragment")
        atom_props["fixed"] = [
            i + 1 for i in range(atoms.get_number_of_atoms())
            if i + 1 not in frag
        ]

    atoms.set_tags(_create_tags(atom_props, atoms))

    structure = struct_cls(ase=atoms)

    if atom_props:
        kind_names = structure.get_kind_names()
        kinds_dict = {"kind_names": kind_names}
        for key, atom_indexes in atom_props.items():
            kv_map = {kn: i + 1 in atom_indexes
                      for i, kn in enumerate(structure.get_site_kindnames())}
            kinds_dict[key] = [kv_map[kn] for kn in kind_names]
        kinds = kind_cls(data=kinds_dict)
    else:
        kinds = None

    symmetry = symmetry_cls(data={
        "operations": data["initial"]["primitive_symmops"],
        "basis": "fractional",
        "hall_number": None
    })

    bases = {}
    for bset in basis_sets:

        bfile = tempfile.NamedTemporaryFile(delete=False)
        try:
            with open(bfile.name, "w") as f:
                f.write(bset)
            bdata, _ = basis_cls.get_or_create(
                bfile.name, use_first=False, store_basis=False)
            # TODO report if bases created or retrieved
        finally:
            os.remove(bfile.name)

        bases[bdata.element] = bdata

    builder = calc_cls.create_builder(
        output_dict, structure, bases,
        symmetry=symmetry, kinds=kinds, code=code)

    return builder


def _create_atoms(data, section="initial"):
    """create ase.Atoms from ejplugins parsed data"""
    cell_data = data[section]["primitive_cell"]
    cell_vectors = []
    for n in "a b c".split():
        assert cell_data["cell_vectors"][n]["units"] == "angstrom"
        cell_vectors.append(cell_data["cell_vectors"][n]["magnitude"])
    ccoords = cell_data["ccoords"]["magnitude"]
    atoms = ase.Atoms(
        cell=cell_vectors,
        pbc=cell_data["pbc"],
        symbols=cell_data["symbols"],
        positions=ccoords)
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
        signature = ".".join(signature)
        kinds[symbol][signature] = kinds[symbol].get(signature, []) + [i + 1]
    tags = []
    for i, symbol in enumerate(atoms.get_chemical_symbols()):
        for j, key in enumerate(sorted(kinds[symbol].keys())):
            if i + 1 in kinds[symbol][key]:
                tags.append(j)
    assert len(tags) == atoms.get_number_of_atoms()
    return tags
