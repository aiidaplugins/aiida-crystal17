"""
a module for computing the symmetry of an AiiDA StructureData object.

NB: this module is not specific to CRYSTAL,
and may be move to a separate package at a later date
"""
import numpy as np
from ase import Atoms
from ase.symbols import symbols2numbers
import spglib

from aiida_crystal17 import __version__


def frac_to_cartesian(lattice, fcoords):
    """convert fractional coordinates to cartesian coordinates

    Parameters
    ----------
    lattice: list
        3x3 array of lattice vectors
    fcoords: list
        Nx3 array of fractional coordinate

    Returns
    -------
    list:
        Nx3 array of cartesian coordinate

    """
    ccoords = []
    for i in fcoords:
        x = i[0] * lattice[0][0] + i[1] * lattice[1][0] + i[2] * lattice[2][0]
        y = i[0] * lattice[0][1] + i[1] * lattice[1][1] + i[2] * lattice[2][1]
        z = i[0] * lattice[0][2] + i[1] * lattice[1][2] + i[2] * lattice[2][2]
        ccoords.append([x, y, z])
    return ccoords


def cartesian_to_frac(lattice, ccoords):
    """convert cartesian coordinates to fractional coordinates

    Parameters
    ----------
    lattice: list
        3x3 array of lattice vectors
    ccoords: list
        Nx3 array of cartesian coordinate

    Returns
    -------
    list:
        Nx3 array of fractional coordinate

    """
    det3 = np.linalg.det

    latt_tr = np.transpose(lattice)

    fcoords = []
    det_latt_tr = np.linalg.det(latt_tr)
    for i in ccoords:
        a = (det3([[i[0], latt_tr[0][1], latt_tr[0][2]],
                   [i[1], latt_tr[1][1], latt_tr[1][2]],
                   [i[2], latt_tr[2][1], latt_tr[2][2]]])) / det_latt_tr
        b = (det3([[latt_tr[0][0], i[0], latt_tr[0][2]],
                   [latt_tr[1][0], i[1], latt_tr[1][2]],
                   [latt_tr[2][0], i[2], latt_tr[2][2]]])) / det_latt_tr
        c = (det3([[latt_tr[0][0], latt_tr[0][1], i[0]],
                   [latt_tr[1][0], latt_tr[1][1], i[1]],
                   [latt_tr[2][0], latt_tr[2][1], i[2]]])) / det_latt_tr
        fcoords.append([a, b, c])
    return fcoords


def prepare_for_spglib(structure):
    """ prepare an AiiDa Structure for parsing to spglib

    Parameters
    ----------
    structure: aiida.StructureData

    Returns
    -------
    tuple: cell
        (lattice, fcoords, inequivalent)
    dict: int2kind_map
        maps integer values in inequivalent list to AiiDa Kind objects

    """
    structure = convert_structure(structure, "aiida")

    lattice = structure.cell
    ccoords = [s.position for s in structure.sites]
    fcoords = cartesian_to_frac(lattice, ccoords)
    kind2int_map = {name: i
                    for i, name in enumerate(structure.get_kind_names())}
    int2kind_map = {i: name for name, i in kind2int_map.items()}
    inequivalent = [kind2int_map[name]
                    for name in structure.get_site_kindnames()]

    return (lattice, fcoords, inequivalent), int2kind_map


def compute_symmetry_dataset(structure, symprec, angle_tolerance):
    """ compute the symmetry of a Structure, with
    periodic boundary conditions in all axes, using spglib

    Parameters
    ----------
    structure: aiida.StructureData
    symprec: float
        Symmetry search tolerance in the unit of length.
    angle_tolerance: float or None
        Symmetry search tolerance in the unit of angle degrees.
        If the value is negative or None, an internally optimized routine
        is used to judge symmetry.

    Returns
    -------
    dataset: dict
        spglib symmetry dataset

    """
    cell, int2kind_map = prepare_for_spglib(structure)

    dataset = spglib.get_symmetry_dataset(
        cell, symprec=symprec,
        angle_tolerance=-1 if angle_tolerance is None else angle_tolerance)

    return dataset


def compute_symmetry_dict(structure, symprec, angle_tolerance):
    """ compute the symmetry of a Structure, with
    periodic boundary conditions in all axes, using spglib

    Parameters
    ----------
    structure: aiida.StructureData
    symprec: float
        Symmetry search tolerance in the unit of length.
    angle_tolerance: float or None
        Symmetry search tolerance in the unit of angle degrees.
        If the value is negative or None, an internally optimized routine
        is used to judge symmetry.

    Returns
    -------
    dict:
        data required to create an AiiDA SymmetryData object

    """
    cell, int2kind_map = prepare_for_spglib(structure)

    dataset = spglib.get_symmetry_dataset(
        cell, symprec=symprec,
        angle_tolerance=-1 if angle_tolerance is None else angle_tolerance)

    operations = []
    for rotation, trans in zip(dataset["rotations"], dataset["translations"]):
        operations.append(rotation.flatten().tolist() + trans.tolist())

    data = {
        "hall_number": dataset["hall_number"],
        "basis": "fractional",
        "operations": operations,
        "computation": {
            "symmetry_program": "spglib",
            "symmetry_version": spglib.__version__,
            "computation_class": __name__,
            "computation_version": __version__,
            "symprec": symprec,
            "angle_tolerance": angle_tolerance
        }
    }
    return data


def get_hall_number_from_symmetry(operations, basis="fractional",
                                  lattice=None, symprec=1e-5):
    """obtain the Hall number from the symmetry operations

    Parameters
    ----------
    operations: list
        Nx12 flattened list of symmetry operations
    basis: str
        "fractional" or "cartesian"

    Returns
    -------
    int

    """
    if basis == "cartesian":
        operations = operations_cart_to_frac(operations, lattice)
    elif basis != "fractional":
        raise ValueError("basis should be cartesian or fractional")
    rotations = [[o[0:3], o[3:6], o[6:9]] for o in operations]
    translations = [o[9:12] for o in operations]
    return spglib.get_hall_number_from_symmetry(
        rotations, translations, symprec=symprec)


def find_primitive(structure, symprec, angle_tolerance):
    """ compute the primitive cell for an AiiDA structure

    Parameters
    ----------
    structure: aiida.StructureData
    symprec: float
        Symmetry search tolerance in the unit of length.
    angle_tolerance: float or None
        Symmetry search tolerance in the unit of angle degrees.
        If the value is negative, an internally optimized routine
        is used to judge symmetry.

    Returns
    -------
    aiida.StructureData

    """
    from aiida.orm.nodes.data.structure import Site
    structure = convert_structure(structure, "aiida")

    cell, int2kind_map = prepare_for_spglib(structure)

    new_cell = spglib.find_primitive(
        cell, symprec=symprec,
        angle_tolerance=-1 if angle_tolerance is None else angle_tolerance)
    if new_cell is None:
        raise ValueError("standardization of cell failed")

    new_structure = structure.clone()
    new_structure.clear_sites()
    new_structure.cell = new_cell[0].tolist()
    positions = frac_to_cartesian(new_structure.cell, new_cell[1])
    for position, eid in zip(positions, new_cell[2].tolist()):
        new_structure.append_site(
            Site(kind_name=int2kind_map[eid], position=position))

    return new_structure


def standardize_cell(structure, symprec, angle_tolerance,
                     to_primitive=False, no_idealize=False):
    """ compute the standardised cell for an AiiDA structure

    Parameters
    ----------
    structure: aiida.StructureData
    to_primitive: bool
        If True, the standardized primitive cell is created.
    no_idealize: bool
        If True, it is disabled to idealize lengths and angles of
        basis vectors and positions of atoms according to crystal symmetry.
    symprec: float
        Symmetry search tolerance in the unit of length.
    angle_tolerance: float or None
        Symmetry search tolerance in the unit of angle degrees.
        If the value is negative or None, an internally optimized routine
        is used to judge symmetry.

    Returns
    -------
    aiida.StructureData

    """
    from aiida.orm.nodes.data.structure import Site
    structure = convert_structure(structure, "aiida")

    cell, int2kind_map = prepare_for_spglib(structure)

    new_cell = spglib.standardize_cell(
        cell, to_primitive=to_primitive, no_idealize=no_idealize,
        symprec=symprec,
        angle_tolerance=-1 if angle_tolerance is None else angle_tolerance)
    if new_cell is None:
        raise ValueError("standardization of cell failed")

    new_structure = structure.clone()
    new_structure.clear_sites()
    new_structure.cell = new_cell[0].tolist()
    positions = frac_to_cartesian(new_structure.cell, new_cell[1])
    for position, eid in zip(positions, new_cell[2].tolist()):
        new_structure.append_site(
            Site(kind_name=int2kind_map[eid], position=position))

    return new_structure


def get_crystal_system_name(sg_number):
    """Get the crystal system for the structure from the space group number

    Parameters
    ----------
    sg_number: int
        the spacegroup number

    Returns
    -------
    crystal_system: str
        Crystal system for structure
    """

    def in_range(i, j):
        return i <= sg_number <= j

    cs = {
        "triclinic": (1, 2),
        "monoclinic": (3, 15),
        "orthorhombic": (16, 74),
        "tetragonal": (75, 142),
        "trigonal": (143, 167),
        "hexagonal": (168, 194),
        "cubic": (195, 230)
    }

    crystal_system = None

    for name, (min_group, max_group) in cs.items():
        if in_range(min_group, max_group):
            crystal_system = name
            break

    if crystal_system is None:
        raise ValueError(
            "could not find crystal system of space group number: {}".format(
                sg_number))

    return crystal_system


def get_lattice_type_name(sg_number):
    """Get the lattice type for the structure from the space group

    This is the same as crystal system name,
    with the exception of the trigonal -> hexagonal or rhombohedral

    Parameters
    ----------
    sg_number: int
        the spacegroup number

    Returns
    -------
    lattice_type: str
        Crystal lattice for the structure

    """
    system = get_crystal_system_name(sg_number)
    if sg_number in [146, 148, 155, 160, 161, 166, 167]:
        return "rhombohedral"
    elif system == "trigonal":
        return "hexagonal"

    return system


def operation_frac_to_cart(lattice, rotation, translation):
    """convert a single symmetry operation from fractional to cartesian

    Parameters
    ----------
    lattice: list
        3x3 matrix of lattice vectors (a, b, c)
    rotation: list
        3x3 rotation matrix
    translation: list
        3x1 translation vector

    Returns
    -------
    rotation: list
        3x3 rotation matrix
    translation: list
        3x1 translation vector

    """
    lattice_tr = np.transpose(lattice)
    lattice_tr_inv = np.linalg.inv(lattice_tr)
    rotation = np.dot(lattice_tr, np.dot(rotation, lattice_tr_inv)).tolist()
    translation = np.dot(translation, lattice).tolist()
    return rotation, translation


def operations_frac_to_cart(operations, lattice):
    """convert a list of fractional symmetry operations to cartesian

    Parameters
    ----------
    operations: list
        Nx9 array, representing each symmetry operation as a flattened list;
        (r00, r01, r02, r10, r11, r12, r20, r21, r22, t0, t1, t2)
    lattice: list
        3x3 matrix (a, b, c)

    Returns
    -------
    list:
        Nx9 array of operations

    """
    cart_ops = []
    for op in operations:
        rot = [op[0:3], op[3:6], op[6:9]]
        trans = op[9:12]
        rot, trans = operation_frac_to_cart(lattice, rot, trans)
        cart_ops.append(rot[0] + rot[1] + rot[2] + trans)
    return cart_ops


def operation_cart_to_frac(lattice, rotation, translation):
    """convert a single symmetry operation from cartesian to fractional

    Parameters
    ----------
    lattice: list
        3x3 matrix of lattice vectors (a, b, c)
    rotation: list
        3x3 rotation matrix
    translation: list
        3x1 translation vector

    Returns
    -------
    rotation: list
        3x3 rotation matrix
    translation: list
        3x1 translation vector

    """
    lattice_tr = np.transpose(lattice)
    lattice_tr_inv = np.linalg.inv(lattice_tr)
    rot = np.dot(lattice_tr_inv, np.dot(rotation, lattice_tr)).tolist()
    trans = np.dot(translation, np.linalg.inv(lattice)).tolist()

    return rot, trans


def operations_cart_to_frac(operations, lattice):
    """convert a list of cartesian symmetry operations to fractional

    Parameters
    ----------
    operations: list
        Nx9 array, representing each symmetry operation as a flattened list;
        (r00, r01, r02, r10, r11, r12, r20, r21, r22, t0, t1, t2)
    lattice: list
        3x3 matrix (a, b, c)

    Returns
    -------
    list:
        Nx9 array of operations

    """
    frac_ops = []
    for op in operations:
        rot = [op[0:3], op[3:6], op[6:9]]
        trans = op[9:12]
        rot, trans = operation_cart_to_frac(lattice, rot, trans)
        frac_ops.append(rot[0] + rot[1] + rot[2] + trans)
    return frac_ops


def operation_to_affine(operation):
    """ create a 4x4 affine transformation matrix,
    from a flattened symmetry operation

    Parameters
    ----------
    operation: list
        representing symmetry operation as a flattened list;
        (r00, r01, r02, r10, r11, r12, r20, r21, r22, t0, t1, t2)

    Returns
    -------
    list:
        4x4 array

    """
    if not len(operation) == 12:
        raise ValueError("operation should be of length 12")
    affine_matrix = np.eye(4)
    affine_matrix[0:3][:, 0:3] = [
        operation[0:3], operation[3:6], operation[6:9]]
    affine_matrix[0:3][:, 3] = operation[9:12]
    return affine_matrix


def affine_to_operation(affine_matrix):
    """ create a flattened symmetry operation,
    from a 4x4 affine transformation matrix

    Parameters
    ----------
    affine_matrix: list
        4x4 affine transformation

    Returns
    -------
    list:
        representing symmetry operation as a flattened list;
        (r00, r01, r02, r10, r11, r12, r20, r21, r22, t0, t1, t2)

    """
    affine_matrix = np.array(affine_matrix)
    rotation = affine_matrix[0:3][:, 0:3].flatten().tolist()
    translation = affine_matrix[0:3][:, 3].tolist()
    return rotation + translation


def generate_full_symmops(operations, tolerance=0.3):
    """Recursive algorithm to permute through all possible combinations of the
    initially supplied symmetry operations to arrive at a complete set of
    operations mapping a single atom to all other equivalent atoms in the
    point group.  This assumes that the initial number already uniquely
    identifies all operations.

    adapted from pymatgen.symmetry.analyzer.generate_full_symmops

    Parameters
    ----------
    operations: list
        Nx9 representing symmetry operation as a flattened list;
        (r00, r01, r02, r10, r11, r12, r20, r21, r22, t0, t1, t2)
    tolerance : float
        Distance tolerance to consider sites as symmetrically equivalent

    Parameters
    ----------
    list
        Nx9 representing symmetry operation as a flattened list;
        (r00, r01, r02, r10, r11, r12, r20, r21, r22, t0, t1, t2)

    """
    unitary = np.eye(4)
    generators = [operation_to_affine(op) for op in operations
                  if not np.allclose(operation_to_affine(op), unitary)]
    if not generators:
        # C1 symmetry breaks assumptions in the algorithm afterwards
        return operations
    else:
        full = list(generators)

        for g in full:
            for s in generators:
                op = np.dot(g, s)
                d = np.abs(full - op) < tolerance
                if not np.any(np.all(np.all(d, axis=2), axis=1)):
                    full.append(op)

        d = np.abs(full - unitary) < tolerance
        if not np.any(np.all(np.all(d, axis=2), axis=1)):
            full.append(unitary)

        return [affine_to_operation(op2) for op2 in full]


def convert_structure(structure, out_type):
    """convert an AiiDA, ASE or dict object to another type

    Parameters
    ----------
    structure: aiida.StructureData or dict or ase.Atoms
    out_type: str
        one of: 'dict', 'ase' or 'aiida

    """
    from aiida.plugins import DataFactory
    from aiida.orm.nodes.data.structure import Site, Kind
    structure_data_cls = DataFactory('structure')

    if isinstance(structure, dict):
        if "symbols" in structure and "atomic_numbers" not in structure:
            structure["atomic_numbers"] = symbols2numbers(structure["symbols"])
        if ("fcoords" in structure and "lattice" in structure and "ccoords" not in structure):
            structure["ccoords"] = frac_to_cartesian(
                structure["lattice"], structure["fcoords"])
        required_keys = ["pbc", "lattice", "ccoords", "atomic_numbers"]
        if not set(structure.keys()).issuperset(required_keys):
            raise AssertionError(
                "dict keys are not a superset of: {}".format(required_keys))

    if out_type == "dict":
        if isinstance(structure, dict):
            return structure
        if isinstance(structure, structure_data_cls):
            return structure_to_dict(structure)
        if isinstance(structure, Atoms):
            return {
                "pbc": structure.pbc.tolist(),
                "atomic_numbers": structure.get_atomic_numbers().tolist(),
                "ccoords": structure.positions.tolist(),
                "lattice": structure.cell.tolist(),
                "equivalent": structure.get_tags().tolist()
            }
        raise TypeError("structure: {}".format(structure))
    elif out_type == "ase":
        if isinstance(structure, Atoms):
            return structure
        if isinstance(structure, structure_data_cls):
            return structure.get_ase()
        if isinstance(structure, dict):
            return Atoms(
                numbers=structure["atomic_numbers"],
                cell=structure["lattice"],
                positions=structure["ccoords"],
                pbc=structure["pbc"],
                tags=structure.get("equivalent", None))
        raise TypeError("structure: {}".format(structure))
    elif out_type == "aiida":
        if isinstance(structure, structure_data_cls):
            return structure
        if isinstance(structure, Atoms):
            return structure_data_cls(ase=structure)
        if isinstance(structure, dict):
            if structure.get("kinds") is not None:
                struct = structure_data_cls(cell=structure['lattice'])
                struct.set_pbc(structure["pbc"])
                for kind, ccoord in zip(structure["kinds"],
                                        structure['ccoords']):
                    if not isinstance(kind, Kind):
                        kind = Kind(raw=kind)
                    if kind.name not in struct.get_site_kindnames():
                        struct.append_kind(kind)
                    struct.append_site(Site(
                        position=ccoord, kind_name=kind.name))
                return struct
            else:
                atoms = Atoms(
                    numbers=structure["atomic_numbers"],
                    cell=structure["lattice"],
                    positions=structure["ccoords"],
                    pbc=structure["pbc"],
                    tags=structure.get("equivalent", None))
                return structure_data_cls(ase=atoms)
    raise ValueError("out_type: {}".format(out_type))


def structure_to_dict(structure):
    """create a dictionary of structure properties per atom

    Parameters
    ----------
    structure: aiida.StructureData
        the input structure

    Returns
    -------
    dict:
        dictionary containing;
        lattice, atomic_numbers, ccoords, pbc, kinds, equivalent

    """
    from aiida.common.exceptions import InputValidationError

    for kind in structure.kinds:
        if kind.is_alloy:
            raise InputValidationError(
                "Kind '{}' is an alloy. This is not allowed for CRYSTAL input structures."
                "".format(kind.name))
        if kind.has_vacancies:
            raise InputValidationError(
                "Kind '{}' has vacancies. This is not allowed for CRYSTAL input structures."
                "".format(kind.name))

    kindname_symbol_map = {
        kind.name: kind.symbols[0]
        for kind in structure.kinds
    }
    kindname_id_map = {kind.name: i for i, kind in enumerate(structure.kinds)}
    id_kind_map = {i: kind for i, kind in enumerate(structure.kinds)}
    kind_names = [site.kind_name for site in structure.sites]
    symbols = [kindname_symbol_map[name] for name in kind_names]
    equivalent = [kindname_id_map[name] for name in kind_names]
    kinds = [id_kind_map[e] for e in equivalent]

    sdata = {
        "lattice": structure.cell,
        "atomic_numbers": symbols2numbers(symbols),
        "ccoords": [site.position for site in structure.sites],
        "pbc": structure.pbc,
        "equivalent": equivalent,
        "kinds": kinds,
    }

    return sdata
