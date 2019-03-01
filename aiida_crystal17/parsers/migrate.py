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
def create_inputs(inpath, outpath):
    """ create ``crystal17.main`` input nodes from an existing run

    NB: none of the nodes are stored, also
    existing basis will be retrieved if availiable

    :param inpath: path to .d12 file
    :param outpath: path to .out file
    :return: dictionary of inputs, with keys 'structure', 'parameters', 'settings', 'structure', 'basis'
    """
    from aiida.plugins import DataFactory, CalculationFactory
    calc_cls = CalculationFactory('crystal17.main')
    basis_cls = DataFactory('crystal17.basisset')
    struct_cls = DataFactory('structure')
    structsettings_cls = DataFactory('crystal17.structsettings')

    inputs = {}

    with open(inpath) as f:
        d12content = f.read()

    output_dict, basis_sets, atom_props = extract_data(d12content)

    cryparse = CrystalOutputPlugin()
    if not os.path.exists(outpath):
        raise OutputParsingError(
            "The raw data file does not exist: {}".format(outpath))
    with open(outpath) as f:
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
    inputs['structure'] = structure

    settings_dict = {"kinds": {}}
    for key, vals in atom_props.items():
        settings_dict["kinds"][key] = [
            structure.sites[i - 1].kind_name for i in vals
        ]

    settings_dict["operations"] = data["initial"]["primitive_symmops"]
    # TODO retrieve centering code, crystal system and spacegroup
    settings_dict["space_group"] = 1
    settings_dict["crystal_type"] = 1
    settings_dict["centring_code"] = 1
    settings = structsettings_cls(data=settings_dict)

    parameters = calc_cls.prepare_and_validate(output_dict, structure,
                                               settings)
    inputs['parameters'] = parameters
    inputs['settings'] = settings

    inputs["basis"] = {}
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

        inputs["basis"][bdata.element] = bdata

    return inputs


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
