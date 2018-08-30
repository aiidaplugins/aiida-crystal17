"""
This module deals with reading/creating .gui files
for use with the EXTERNAL keyword

File Format:

dimesionality origin_setting crystal_type energy(optional)
    a_x a_y a_z
    b_x b_y b_z
    c_x c_y c_z
num_symm_ops (in cartesian coordinates)
    op1_rot_00 op1_rot_01 op1_rot_02
    op1_rot_10 op1_rot_11 op1_rot_12
    op1_rot_20 op1_rot_21 op1_rot_22
    op1_trans_0 op1_trans_1 op1_trans_2
    ...
num_atoms (if cryversion<17 irreducible atoms only)
    atomic_number x y z (in cartesian coordinates)
    ...
space_group_int_num num_symm_ops

"""
import numpy as np
from spglib import spglib

# python 3 to 2 compatibility
try:
    import pathlib
except ImportError:
    import pathlib2 as pathlib

_CRYSTAL_TYPE = {
    1: 'triclinic',
    2: 'monoclinic',
    3: 'orthorhombic',
    4: 'tetragonal',
    5: 'hexagonal',
    6: 'cubic'
}
_DIMENSIONALITY = {
    0: [False, False, False],
    1: [True, False, False],
    2: [True, True, False],
    3: [True, True, True]
}
_CENTERING_MATRICES = {
    2: [[1.0000, 0.0000, 0.0000], [0.0000, 1.0000, 1.0000],
        [0.0000, -1.0000, 1.0000]],  # P_A
    4: [[1.0000, 1.0000, 0.0000], [-1.0000, 1.0000, 0.0000],
        [0.0000, 0.0000, 1.0000]],  # modified P_C
    5: [[-1.0000, 1.0000, 1.0000], [1.0000, -1.0000, 1.0000],
        [1.0000, 1.0000, -1.0000]],  # P_F
    6: [[0, 1.0000, 1.0000], [1.0000, 0.0000, 1.0000],
        [1.0000, 1.0000, 0.0000]],  # P_I
}  # primitive to crystallographic, invert for other way round

# relate to: CENTRING CODE x/y, not sure what y relates to?
# see https://atztogo.github.io/spglib/definition.html#conventions-of-standardized-unit-cell


# pylint: disable=too-many-locals
def read_gui_file(fpath, cryversion=17):
    """read CRYSTAL geometry (.gui) file

    :param fpath: path to file
    :type fpath: str or pathlib.Path
    :param cryversion: version of CRYSTAL
    :type cryversion: int
    :return:
    """
    if cryversion != 17:
        raise NotImplementedError("CRYSTAL versions other than 17")

    structdata = {}
    path = pathlib.Path(fpath)
    with path.open() as f:
        lines = f.read().splitlines()
        init_data = lines[0].split()
        dimensionality = int(init_data[0])
        if dimensionality not in _DIMENSIONALITY:
            raise ValueError(
                "dimensionality was not between 0 and 3: {}".format(
                    dimensionality))
        structdata["pbc"] = _DIMENSIONALITY[dimensionality]
        structdata["origin_setting"] = int(init_data[1])
        crystal_type = int(init_data[2])
        if crystal_type not in _CRYSTAL_TYPE:
            raise ValueError("crystal_type was not between 1 and 6: {}".format(
                dimensionality))
        structdata["crystal_type"] = _CRYSTAL_TYPE[crystal_type]
        structdata["lattice"] = [[float(num) for num in l.split()]
                                 for l in lines[1:4]]
        structdata["nsymops"] = nsymops = int(lines[4])
        symops = []
        for i in range(nsymops):
            symop = []
            for j in range(4):
                line_num = 5 + i * 4 + j
                values = lines[line_num].split()
                if not len(values) == 3:
                    raise IOError(
                        "expected symop x, y and z coordinate on line {0}: {1}".
                        format(line_num, lines[line_num]))
                symop.extend(
                    [float(values[0]),
                     float(values[1]),
                     float(values[2])])
            symops.append(symop)
        structdata["symops"] = symops
        structdata["natoms"] = natoms = int(lines[5 + nsymops * 4])
        structdata["atomic_numbers"] = [
            int(l.split()[0])
            for l in lines[6 + nsymops * 4:6 + nsymops * 4 + natoms]
        ]
        structdata["ccoords"] = [[
            float(num) for num in l.split()[1:4]
        ] for l in lines[6 + nsymops * 4:6 + nsymops * 4 + natoms]]

    return structdata


def get_crystal_system(sg_number, as_number=False):
    """
    Get the crystal system for the structure, e.g., (triclinic,
    orthorhombic, cubic, etc.) from the space group number

    Returns:
        (str): Crystal system for structure or None if system cannot be detected.
    """
    f = lambda i, j: i <= sg_number <= j
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

    for k, v in cs.items():
        if f(*v):
            crystal_system = k
            break

    if crystal_system is None:
        raise ValueError(
            "could not find crystal system of space group number: {}".format(
                sg_number))

    if as_number:
        crystal_system = {v: k
                          for k, v in _CRYSTAL_TYPE.items()}[crystal_system]

    return crystal_system


def get_lattice_type(sg_number):
    """
    Get the lattice for the structure, e.g., (triclinic,
    orthorhombic, cubic, etc.).This is the same than the
    crystal system with the exception of the hexagonal/rhombohedral
    lattice

    Returns:
        (str): Lattice type for structure or None if type cannot be detected.
    """
    system = get_crystal_system(sg_number)
    if sg_number in [146, 148, 155, 160, 161, 166, 167]:
        return "rhombohedral"
    elif system == "trigonal":
        return "hexagonal"

    return system


def get_centering_code(sg_number, sg_symbol):
    """get crystal centering codes, to convert from primitive to conventional"""
    lattice_type = get_lattice_type(sg_number)

    if "P" in sg_symbol or lattice_type == "hexagonal":
        return 1
    elif lattice_type == "rhombohedral":
        # can also be P_R (if a_length == c_length in conventional cell),
        # but crystal doesn't appear to use that anyway
        return 1
    elif "I" in sg_symbol:
        return 6
    elif "F" in sg_symbol:
        return 5
    elif "C" in sg_symbol:
        crystal_system = get_crystal_system(sg_number, as_number=False)
        if crystal_system == "monoclinic":
            return 4  # TODO this is P_C but don't know what code it is, maybe 3?
            # [[1.0, -1.0, 0.0], [1.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        return 4
    # elif "A" in sg_symbol:
    #     return 2  # TODO check this is always correct (not in original function)

    return 1


def frac2cart(lattice, fcoords):
    """a function that takes the cell parameters, in angstrom, and a list of fractional coordinates
    and returns the structure in cartesian coordinates
    """
    ccoords = []
    for i in fcoords:
        x = i[0] * lattice[0][0] + i[1] * lattice[1][0] + i[2] * lattice[2][0]
        y = i[0] * lattice[0][1] + i[1] * lattice[1][1] + i[2] * lattice[2][1]
        z = i[0] * lattice[0][2] + i[1] * lattice[1][2] + i[2] * lattice[2][2]
        ccoords.append([x, y, z])
    return ccoords


def cart2frac(lattice, ccoords):
    """a function that takes the cell parameters, in angstrom, and a list of Cartesian coordinates
    and returns the structure in fractional coordinates
    """
    det3 = np.linalg.det

    latt_tr = np.transpose(lattice)

    fcoords = []
    det_latt_tr = np.linalg.det(latt_tr)
    for i in ccoords:
        a = (det3([[i[0], latt_tr[0][1], latt_tr[0][2]], [
            i[1], latt_tr[1][1], latt_tr[1][2]
        ], [i[2], latt_tr[2][1], latt_tr[2][2]]])) / det_latt_tr
        b = (det3([[latt_tr[0][0], i[0], latt_tr[0][2]], [
            latt_tr[1][0], i[1], latt_tr[1][2]
        ], [latt_tr[2][0], i[2], latt_tr[2][2]]])) / det_latt_tr
        c = (det3([[latt_tr[0][0], latt_tr[0][1], i[0]], [
            latt_tr[1][0], latt_tr[1][1], i[1]
        ], [latt_tr[2][0], latt_tr[2][1], i[2]]])) / det_latt_tr
        fcoords.append([a, b, c])
    return fcoords


# TODO split this up into func where all data supplied and one where we calc sym
# pylint: disable=too-many-arguments,too-many-locals
def write_gui_file(structdata,
                   standardize=True,
                   primitive=True,
                   idealize=False,
                   cryversion=17,
                   symops=None,
                   crystal_type=None,
                   origin_setting=None,
                   symprec=0.01,
                   angletol=5):
    """create the content string for a CRYSTAL geometry (.gui) file

    Structures can first be standardized, to correctly centre them,
    and optionally can be idealized and/or converted to the primitive cell
    see https://atztogo.github.io/spglib/definition.html#conventions-of-standardized-unit-cell

    :param structdata: structure data
    :type structdata: dict containaing "lattice", "atomic_numbers", "ccoords", "pbc" and (optionally) "magmoms"
    :param standardize: standardize the structure
    :param primitive: find the primitive (standardized) structure
    :param idealize: Using obtained symmetry operations, the distortions are removed to idealize the unit cell structure
    :param cryversion: version of CRYSTAL
    :type cryversion: int
    :param symops: use specific symops array((N, 12)) in cartesian basis or, if None, computed by spglib
    :param crystal_type: the crystal type id (1 to 6)
    :param origin_setting: origin setting for primitive to conventional transform
    :param symprec: Tolerance for symmetry finding
                    0.01 is fairly strict and works well for properly refined structures
                    0.1 (the value used in Materials Project) may be needed for relaxed structures
    :param angletol: Angle tolerance for symmetry finding
    :return:

    """
    if cryversion != 17:
        raise NotImplementedError("CRYSTAL versions other than 17")

    rkeys = ["lattice", "atomic_numbers", "ccoords", "pbc"]
    if not set(rkeys).issubset(structdata.keys()):
        raise ValueError("stuctdata must contain: {}".format(rkeys))

    # set default values
    dimensionality = sum(structdata["pbc"])
    crystal_type = 1 if crystal_type is None else crystal_type
    origin_setting = 1 if origin_setting is None else origin_setting

    # if the symops are given, we can go straight to writing the file
    if symops is not None:
        num_symops = len(symops)
        sym_data = []
        for symop in symops:
            sym_data.append(symop[0:3])
            sym_data.append(symop[3:6])
            sym_data.append(symop[6:9])
            sym_data.append(symop[9:12])
        gui_str = _gui_string(dimensionality, origin_setting, crystal_type,
                              structdata["lattice"], num_symops, sym_data,
                              structdata["atomic_numbers"],
                              structdata["ccoords"], 1)
    else:
        # we need to work out the symmerty
        if dimensionality == 3:

            # first create the cell to pass to spglib
            lattice = structdata["lattice"]
            fcoords = cart2frac(structdata["lattice"], structdata["ccoords"])
            cell = [lattice, fcoords, structdata["atomic_numbers"]]
            if "magmoms" in structdata:
                cell.append(
                    structdata["magmoms"])  # Only works with get_symmetry
            cell = tuple(cell)

            if standardize or primitive:
                scell = spglib.standardize_cell(
                    cell,
                    no_idealize=not idealize,
                    to_primitive=primitive,
                    symprec=symprec,
                    angle_tolerance=angletol)
                if scell is None:
                    raise ValueError(
                        "standardization of cell failed: {}".format(cell))
                cell = scell

            lattice = cell[0]
            fcoords = cell[1]
            ccoords = frac2cart(lattice, fcoords)
            atomic_numbers = cell[2]

            # find symmetry
            symm_dataset = spglib.get_symmetry_dataset(
                cell, symprec=symprec, angle_tolerance=angletol)
            if symm_dataset is None:
                # TODO option to use P1 symmetry if can't find symmetry
                raise ValueError(
                    "could not find symmetry of cell: {}".format(cell))

            sg_num = symm_dataset[
                'number'] if symm_dataset['number'] is not None else 1
            crystal_type = get_crystal_system(sg_num, as_number=True)

            # fin symops
            num_symops = len(symm_dataset["rotations"])
            sym_data = []
            for rot, trans in zip(symm_dataset["rotations"],
                                  symm_dataset["translations"]):
                # fractional to cartesian
                lattice_tr = np.transpose(lattice)
                lattice_tr_inv = np.linalg.inv(lattice_tr)
                rot = np.dot(lattice_tr, np.dot(rot, lattice_tr_inv))
                trans = np.dot(trans, lattice)
                sym_data.extend([rot[0], rot[1], rot[2], trans])

            # find and set centering code
            # the origin_setting (aka centering code) refers to how to convert conventional to primitive
            if primitive:
                origin_setting = get_centering_code(
                    sg_num, symm_dataset["international"])

            # from jsonextended import edict
            # edict.pprint(symm_dataset)

            gui_str = _gui_string(dimensionality, origin_setting, crystal_type,
                                  lattice, num_symops, sym_data,
                                  atomic_numbers, ccoords, sg_num)

        elif dimensionality == 2:
            # maximise_orthogonality
            # get_orthogonal
            # set cvec as [0., 0., 500.]
            # TODO dimensionality == 2
            raise NotImplementedError("dimensionality other than 3")
        else:
            # TODO dimensionality < 2
            raise NotImplementedError("dimensionality other than 3")

    return gui_str


# pylint: disable=too-many-arguments
def _gui_string(dimensionality, origin_setting, crystal_type, lattice,
                num_symops, sym_data, atomic_numbers, ccoords, sg_num):
    """create string of gui file content (for CRYSTAL17)"""
    geom_str_list = []
    geom_str_list.append("{0} {1} {2}".format(dimensionality, origin_setting,
                                              crystal_type))
    geom_str_list.append("{0:17.9E} {1:17.9E} {2:17.9E}".format(*(
        np.round(lattice[0], 9) + 0.)))
    geom_str_list.append("{0:17.9E} {1:17.9E} {2:17.9E}".format(*(
        np.round(lattice[1], 9) + 0.)))
    geom_str_list.append("{0:17.9E} {1:17.9E} {2:17.9E}".format(*(
        np.round(lattice[2], 9) + 0.)))
    geom_str_list.append(str(num_symops))
    for sym_line in sym_data:
        geom_str_list.append("{0:17.9E} {1:17.9E} {2:17.9E}".format(*(
            np.round(sym_line, 9) + 0.)))
    geom_str_list.append(str(len(atomic_numbers)))
    for anum, coord in zip(atomic_numbers, ccoords):
        geom_str_list.append("{0:3} {1:17.9E} {2:17.9E} {3:17.9E}".format(
            anum, *coord))

    geom_str_list.append("{0} {1}".format(sg_num, num_symops))
    geom_str_list.append("")

    return "\n".join(geom_str_list)


def create_gui_from_struct(struct, settings):
    """ create the content of the gui file from a structure and settings

    :param struct: the input structure
    :type struct: StructureData
    :param settings: dictionary of settings
    :type settings: dict
    :return: content of .gui file (as string)
    """
    rkeys = [
        'struct_primitive', 'struct_origin_setting', 'struct_crystal_type',
        'struct_symops', 'struct_angletol', 'struct_idealize',
        'struct_symprec', 'struct_standardize'
    ]
    if not set(settings.keys()).issuperset(rkeys):
        raise ValueError("settings must contain: {}".format(rkeys))

    atoms = struct.get_ase()

    sdata = {
        "lattice": atoms.cell,
        "atomic_numbers": atoms.get_atomic_numbers(),
        "ccoords": atoms.positions,
        "pbc": atoms.pbc,
        "magmoms": atoms.get_tags()
    }
    # TODO here we use kind indices as magmoms to reduce symmetry, this should be documented
    # another option would be to use keywords in CRYSTAL, but this seems more elegant

    kwargs = {k.replace("struct_", ""): settings[k] for k in rkeys}

    return write_gui_file(sdata, **kwargs)
