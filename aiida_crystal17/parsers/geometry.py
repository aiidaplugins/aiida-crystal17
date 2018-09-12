"""
This module deals with reading/creating .gui files
for use with the EXTERNAL keyword

File Format

::

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
from aiida_crystal17.validation import validate_with_json
from aiida_crystal17.utils import ATOMIC_SYMBOL2NUM, ATOMIC_NUM2SYMBOL
from spglib import spglib

SYMMETRY_PROGRAM = "spglib"
SYMMETRY_VERSION = ".".join([str(i) for i in spglib.get_version()])

# python 3 to 2 compatibility
try:
    import pathlib
except ImportError:
    import pathlib2 as pathlib

CRYSTAL_TYPE_MAP = {
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
CENTERING_CODE_MAP = {
    1: [[1.0000, 0.0000, 0.0000], [0.0000, 1.0000, 0.0000],
        [0.0000, 0.0000, 1.0000]],
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
        if crystal_type not in CRYSTAL_TYPE_MAP:
            raise ValueError("crystal_type was not between 1 and 6: {}".format(
                dimensionality))
        structdata["crystal_type"] = CRYSTAL_TYPE_MAP[crystal_type]
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
        structdata["symops"] = ops_cart_to_frac(symops, structdata["lattice"])
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
    """Get the crystal system for the structure, e.g.,
    (triclinic, orthorhombic, cubic, etc.) from the space group number

    :param sg_number: the spacegroup number
    :param as_number: return the system as a number (recognized by CRYSTAL) or a str
    :return: Crystal system for structure or None if system cannot be detected.
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
                          for k, v in CRYSTAL_TYPE_MAP.items()}[crystal_system]

    return crystal_system


def get_lattice_type(sg_number):
    """Get the lattice for the structure, e.g., (triclinic,
    orthorhombic, cubic, etc.).This is the same than the
    crystal system with the exception of the hexagonal/rhombohedral
    lattice

    :param sg_number: space group number
    :return: Lattice type for structure or None if type cannot be detected.

    """
    system = get_crystal_system(sg_number)
    if sg_number in [146, 148, 155, 160, 161, 166, 167]:
        return "rhombohedral"
    elif system == "trigonal":
        return "hexagonal"

    return system


def get_centering_code(sg_number, sg_symbol):
    """get crystal centering codes, to convert from primitive to conventional

    :param sg_number: the space group number
    :param sg_symbol: the space group symbol
    :return: CRYSTAL centering code
    """
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


def _operation_frac_to_cart(lattice, rot, trans):
    """convert symmetry operation from fractional to cartesian

    :param lattice: 3x3 matrix (a, b, c)
    :param rot: 3x3 rotation matrix
    :param trans: 3 translation vector
    :return: (rot, trans)
    """
    lattice_tr = np.transpose(lattice)
    lattice_tr_inv = np.linalg.inv(lattice_tr)
    rot = np.dot(lattice_tr, np.dot(rot, lattice_tr_inv)).tolist()
    trans = np.dot(trans, lattice).tolist()
    return rot, trans


def ops_frac_to_cart(ops_flat, lattice):
    """convert a list of flattened fractional symmetry operations to cartesian"""
    cart_ops = []
    for op in ops_flat:
        rot = [op[0:3], op[3:6], op[6:9]]
        trans = op[9:12]
        rot, trans = _operation_frac_to_cart(lattice, rot, trans)
        cart_ops.append(rot[0] + rot[1] + rot[2] + trans)
    return cart_ops


def _operation_cart_to_frac(lattice, rot, trans):
    """convert symmetry operation from cartesian to fractional

    :param lattice: 3x3 matrix (a, b, c)
    :param rot: 3x3 rotation matrix
    :param trans: 3 translation vector
    :return: (rot, trans)
    """
    lattice_tr = np.transpose(lattice)
    lattice_tr_inv = np.linalg.inv(lattice_tr)
    rot = np.dot(lattice_tr_inv, np.dot(rot, lattice_tr)).tolist()
    trans = np.dot(trans, np.linalg.inv(lattice)).tolist()

    return rot, trans


def ops_cart_to_frac(ops_flat, lattice):
    """convert a list of flattened cartesian symmetry operations to fractional"""
    frac_ops = []
    for op in ops_flat:
        rot = [op[0:3], op[3:6], op[6:9]]
        trans = op[9:12]
        rot, trans = _operation_cart_to_frac(lattice, rot, trans)
        frac_ops.append(rot[0] + rot[1] + rot[2] + trans)
    return frac_ops


# def compute_symmetry(structdata, settings, cryversion=17):
#     """compute the symmetry and (optionally) modified structure given settings
#
#     Structures can first be standardized, to correctly centre them,
#     and optionally can be idealized and/or converted to the primitive cell
#     see https://atztogo.github.io/spglib/definition.html#conventions-of-standardized-unit-cell
#
#     :param structdata: structure data as mandated by stucture.schema.json
#     :type structdata: dict
#     :param settings: Settings for initial manipulation of structures and conversion to .gui (fort.34) input file, as mandated by the settings.schema.json
#     :type settings: dict
#     :param cryversion: version of CRYSTAL
#     :type cryversion: int
#     :return: (structdata, symmdata)
#
#     """
#     if cryversion != 17:
#         raise NotImplementedError("CRYSTAL versions other than 17")
#
#     # validation of inputs
#     validate_with_json(settings, "settings")
#
#     # rkeys = ["lattice", "atomic_numbers", "ccoords", "pbc"]
#     # if not set(rkeys).issubset(structdata.keys()):
#     #     raise ValueError("stuctdata must contain: {}".format(rkeys))
#
#     # inputs to decide on how to manipulate geometry
#     symops = settings["symmetry"]["operations"]
#     dimensionality = sum(structdata["pbc"])
#
#     if symops is not None:
#         # if the symops are given, we can go straight to writing the file
#         crystal_type = {v: k
#                         for k, v in CRYSTAL_TYPE_MAP.items()
#                         }[settings["crystal"]["system"]]
#         origin_setting = settings["crystal"]["transform"]
#         origin_setting = 1 if origin_setting is None else origin_setting
#
#         symmdata = {
#             "space_group": settings["symmetry"]["space_group"],
#             "operations": symops,
#             "crystal_type": crystal_type,
#             "centring_code": origin_setting,
#         }
#
#     elif dimensionality == 3:
#
#         structdata, symmdata = compute_symmetry_3d(
#             structdata,
#             settings["3d"]["primitive"], settings["3d"]["standardize"],
#             settings["3d"]["idealize"],
#             settings["symmetry"]["symprec"], settings["symmetry"]["angletol"])
#
#     elif dimensionality == 2:
#         # maximise_orthogonality
#         # get_orthogonal
#         # set cvec as [0., 0., 500.]
#         # TODO dimensionality == 2
#         raise NotImplementedError("dimensionality other than 3")
#     else:
#         # TODO dimensionality < 2
#         raise NotImplementedError("dimensionality than less than 2")
#
#     return structdata, symmdata
#


# pylint: disable=too-many-arguments
def compute_symmetry_3d(structdata, standardize, primitive, idealize, symprec,
                        angletol):
    """ create 3d geometry input for CRYSTAL17

    :param structdata: "lattice", "atomic_numbers", "ccoords", "pbc" and (optionally) "equivalent"
    :param standardize: whether to standardize the structure
    :param primitive: whether to create a primitive structure
    :param idealize: whether to idealize the structure
    :param symprec: symmetry precision to parse to spglib
    :param angletol: angletol to parse to spglib
    :return: (structdata, symmdata)

    """
    validate_with_json(structdata, "structure")

    angletol = -1 if angletol is None else angletol

    # first create the cell to pass to spglib
    lattice = structdata["lattice"]
    ccoords = structdata["ccoords"]

    # spglib only uses the atomic numbers to demark inequivalent sites
    inequivalent_sites = (np.array(structdata["atomic_numbers"]) * 1000 +
                          np.array(structdata["equivalent"])).tolist()

    if "kinds" in structdata:
        inequivalent_to_kind = {
            i: k
            for i, k in zip(inequivalent_sites, structdata["kinds"])
        }
    else:
        inequivalent_to_kind = None

    fcoords = cart2frac(lattice, ccoords)
    cell = [lattice, fcoords, inequivalent_sites]
    cell = tuple(cell)

    if standardize or primitive:
        scell = spglib.standardize_cell(
            cell,
            no_idealize=not idealize,
            to_primitive=primitive,
            symprec=symprec,
            angle_tolerance=angletol)
        if scell is None:
            raise ValueError("standardization of cell failed: {}".format(cell))
        cell = scell

        lattice = cell[0].tolist()
        fcoords = cell[1]
        ccoords = frac2cart(lattice, fcoords)
        inequivalent_sites = cell[2].tolist()

    # find symmetry
    # TODO can we get only the symmetry operators accepted by CRYSTAL?
    symm_dataset = spglib.get_symmetry_dataset(
        cell, symprec=symprec, angle_tolerance=angletol)
    if symm_dataset is None:
        # TODO option to use P1 symmetry if can't find symmetry
        raise ValueError("could not find symmetry of cell: {}".format(cell))
    sg_num = symm_dataset[
        'number'] if symm_dataset['number'] is not None else 1
    crystal_type = get_crystal_system(sg_num, as_number=True)

    # format the symmetry operations (fractional to cartesian)
    symops = []
    for rot, trans in zip(symm_dataset["rotations"],
                          symm_dataset["translations"]):
        # rot, trans = operation_frac_to_cart(lattice, rot, trans)
        symops.append(rot[0].tolist() + rot[1].tolist() + rot[2].tolist() +
                      trans.tolist())

    # find and set centering code
    # the origin_setting (aka centering code) refers to how to convert conventional to primitive
    if primitive:
        origin_setting = get_centering_code(sg_num,
                                            symm_dataset["international"])
    else:
        origin_setting = 1

    equivalent = np.mod(inequivalent_sites, 1000).tolist()
    atomic_numbers = ((np.array(inequivalent_sites) - np.array(equivalent)) /
                      1000).astype(int).tolist()

    # from jsonextended import edict
    # edict.pprint(symm_dataset)

    structdata = {
        "lattice": lattice,
        "ccoords": ccoords,
        "pbc": [True, True, True],
        "atomic_numbers": atomic_numbers,
        "equivalent": equivalent
    }

    if inequivalent_to_kind:
        structdata["kinds"] = [
            inequivalent_to_kind[i] for i in inequivalent_sites
        ]

    symmdata = {
        "space_group": sg_num,
        "operations": symops,
        "crystal_type": crystal_type,
        "centring_code": origin_setting,
    }

    return structdata, symmdata


def crystal17_gui_string(structdata, symmdata, fractional_ops=True):
    """create string of gui file content (for CRYSTAL17)

    :param structdata: dictionary of structure data with keys: 'pbc', 'atomic_numbers', 'ccoords', 'lattice'
    :param symmdata:  dictionary of symmetry data with keys: 'crystal_type', 'centring_code', 'sgnum', 'symops'
    :param fractional_ops: whether the symmetry operations are in fractional coordinates
    :return:
    """

    dimensionality = len(structdata["pbc"])
    atomic_numbers = structdata["atomic_numbers"]
    ccoords = structdata["ccoords"]
    lattice = structdata["lattice"]

    crystal_type = symmdata["crystal_type"]
    origin_setting = symmdata["centring_code"]
    sg_num = symmdata["space_group"]
    symops = symmdata["operations"]

    if fractional_ops:
        symops = ops_frac_to_cart(symops, lattice)

    num_symops = len(symops)
    sym_lines = []
    for symop in symops:
        sym_lines.append(symop[0:3])
        sym_lines.append(symop[3:6])
        sym_lines.append(symop[6:9])
        sym_lines.append(symop[9:12])

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
    for sym_line in sym_lines:
        geom_str_list.append("{0:17.9E} {1:17.9E} {2:17.9E}".format(*(
            np.round(sym_line, 9) + 0.)))
    geom_str_list.append(str(len(atomic_numbers)))
    for anum, coord in zip(atomic_numbers, ccoords):
        geom_str_list.append("{0:3} {1:17.9E} {2:17.9E} {3:17.9E}".format(
            anum, *coord))

    geom_str_list.append("{0} {1}".format(sg_num, num_symops))
    geom_str_list.append("")

    return "\n".join(geom_str_list)


def structdict_to_ase(structdict):
    """convert struct dict to ase.Atoms

    :param structdict: dict containing 'lattice', 'atomic_numbers', 'pbc', 'ccoords', 'equivalent'
    :rtype: ase.Atoms
    """
    import ase
    atoms = ase.Atoms(
        cell=structdict["lattice"],
        numbers=structdict["atomic_numbers"],
        pbc=structdict["pbc"],
        positions=structdict["ccoords"],
        tags=structdict["equivalent"])
    return atoms


def ase_to_structdict(atoms):
    """convert ase.Atoms to struct dict

    :type atoms: ase.Atoms
    :return structdict: dict containing 'lattice', 'atomic_numbers', 'pbc', 'ccoords', 'equivalent'
    :type structdict: dict
    """
    structdict = {
        "lattice": atoms.cell.tolist(),
        "ccoords": atoms.positions.tolist(),
        "atomic_numbers": atoms.get_atomic_numbers().tolist(),
        "pbc": atoms.pbc.tolist(),
        "equivalent": atoms.get_tags().tolist()
    }
    return structdict


def structure_to_dict(structure):
    """create a dictionary of structure properties per atom

    :param structure: the input structure
    :type structure: aiida.orm.data.structure.StructureData
    :return: dictionary containing; lattice, atomic_numbers, ccoords, pbc, kinds, equivalent
    :rtype: dict

    """
    from aiida.common.exceptions import InputValidationError

    for kind in structure.kinds:
        if kind.is_alloy():
            raise InputValidationError(
                "Kind '{}' is an alloy. This is not allowed for CRYSTAL input structures."
                "".format(kind.name))
        if kind.has_vacancies():
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
        "atomic_numbers": [ATOMIC_SYMBOL2NUM[sym] for sym in symbols],
        "ccoords": [site.position for site in structure.sites],
        "pbc": structure.pbc,
        "equivalent": equivalent,
        "kinds": kinds,
    }

    return sdata


def dict_to_structure(structdict, logger=None):
    """create a dictionary of structure properties per atom

    :param: dictionary containing; 'lattice', 'atomic_numbers' (or 'symbols'), 'ccoords', 'pbc', 'kinds', 'equivalent'
    :type structdict: dict
    :param logger: a logger with a `warning` method
    :return structure: the input structure
    :rtype structure: aiida.orm.data.structure.StructureData

    """
    from aiida.orm import DataFactory
    StructureData = DataFactory('structure')
    struct = StructureData(cell=structdict['lattice'])
    struct.set_pbc(structdict["pbc"])
    atom_kinds = structdict.get("kinds", None)

    if atom_kinds is None:
        if logger:
            logger.warning("no 'kinds' available, creating new kinds")
        symbols = structdict.get("symbols", None)
        if symbols is None:
            symbols = [
                ATOMIC_NUM2SYMBOL[anum]
                for anum in structdict["atomic_numbers"]
            ]

        if len(symbols) != len(structdict['ccoords']):
            raise AssertionError(
                "the length of ccoords and atomic_numbers/symbols must be the same"
            )
        for symbol, ccoord in zip(symbols, structdict['ccoords']):
            struct.append_atom(position=ccoord, symbols=symbol)
    else:
        if len(atom_kinds) != len(structdict['ccoords']):
            raise AssertionError(
                "the length of ccoords and atom_kinds must be the same")

        from aiida.orm.data.structure import Site, Kind
        for kind, ccoord in zip(atom_kinds, structdict['ccoords']):
            if not isinstance(kind, Kind):
                kind = Kind(raw=kind)
            if kind.name not in struct.get_site_kindnames():
                struct.append_kind(kind)
            struct.append_site(Site(position=ccoord, kind_name=kind.name))

    return struct
