"""
module to read and write CRYSTAL17 .d12 files
"""
import six
from aiida_crystal17.utils import get_keys
from aiida_crystal17.validation import validate_dict

# TODO float format and rounding, e.g. "{}".format(0.00001) -> 1e-05, can CRYSTAL handle that?

# TODO SHRINK where IS=0 and IS1 IS2 IS3 given
# TODO FIELD/FIELDCON
# TODO FREQCALC
# TODO ANHARM
# TODO EOS

# TODO RESTART (need to provide files from previous remote folder)

# TODO incompatability tests e.g. using ATOMSPIN without SPIN (and spin value of SPINLOCK)

# TODO look at https://gitlab.com/ase/ase/blob/master/ase/calculators/crystal.py to see if anything can be used


def format_value(dct, keys):
    """return the value + a new line, or empty string if keys not found"""
    value = get_keys(dct, keys, None)
    if value is None:
        return ""
    if isinstance(value, dict):
        outstr = ""
        for keyword in value.keys():
            args = value[keyword]
            if isinstance(args, bool):
                if args:
                    outstr += "{}\n".format(keyword)
            elif isinstance(args, (list, tuple)):
                outstr += "{0}\n{1}\n".format(keyword,
                                              " ".join([str(a) for a in args]))
            else:
                outstr += "{0}\n{1}\n".format(keyword, args)
        return outstr

    return "{}\n".format(value)


def write_input(indict, basis_sets, atom_props=None):
    """write input of a validated input dictionary

    :param indict: dictionary of input
    :param basis_sets: list of basis set strings or objects with `content` property
    :param atom_props: dictionary of atom ids with specific properties ("spin_alpha", "spin_beta", "unfixed", "ghosts")
    :return:
    """
    # validation
    validate_dict(indict)
    if not basis_sets:
        raise ValueError("there must be at least one basis set")
    elif not (all([isinstance(b, six.string_types) for b in basis_sets])
              or all([hasattr(b, "content") for b in basis_sets])):
        raise ValueError(
            "basis_sets must be either all strings or all objects with a `content` property"
        )
    if atom_props is None:
        atom_props = {}
    if not set(atom_props.keys()).issubset(
        ["spin_alpha", "spin_beta", "unfixed", "ghosts"]):
        raise ValueError(
            "atom_props should only contain: 'spin_alpha', 'spin_beta', 'unfixed', 'ghosts'"
        )
    # validate that a index isn't in both spin_alpha and spin_beta
    allspin = atom_props.get("spin_alpha", []) + atom_props.get(
        "spin_beta", [])
    if len(set(allspin)) != len(allspin):
        raise ValueError(
            "a kind cannot be in both spin_alpha and spin_beta: {}".format(
                allspin))

    outstr = ""

    # Title
    title = get_keys(indict, ["title"], "CRYSTAL run")
    outstr += "{}\n".format(" ".join(title.splitlines()))  # must be one line

    outstr = _geometry_block(outstr, indict, atom_props)

    outstr = _basis_set_block(outstr, indict, basis_sets, atom_props)

    outstr = _hamiltonian_block(outstr, indict, atom_props)

    return outstr


def _hamiltonian_block(outstr, indict, atom_props):
    # Hamiltonian Optional Keywords
    outstr += format_value(indict, ["scf", "single"])
    # DFT Optional Block
    if get_keys(indict, ["scf", "dft"], False):

        outstr += "DFT\n"

        xc = get_keys(indict, ["scf", "dft", "xc"], raise_error=True)
        if isinstance(xc, (tuple, list)):
            if len(xc) == 2:
                outstr += "CORRELAT\n"
                outstr += "{}\n".format(xc[0])
                outstr += "EXCHANGE\n"
                outstr += "{}\n".format(xc[1])
        else:
            outstr += format_value(indict, ["scf", "dft", "xc"])

        if get_keys(indict, ["scf", "dft", "SPIN"], False):
            outstr += "SPIN\n"

        outstr += format_value(indict, ["scf", "dft", "grid"])
        outstr += format_value(indict, ["scf", "dft", "grid_weights"])
        outstr += format_value(indict, ["scf", "dft", "numerical"])

        outstr += "END\n"

    # # K-POINTS (SHRINK\nPMN Gilat)
    outstr += "SHRINK\n"
    outstr += "{0} {1}\n".format(
        *get_keys(indict, ["scf", "k_points"], raise_error=True))
    # ATOMSPIN
    spins = []
    for anum in atom_props.get("spin_alpha", []):
        spins.append((anum, 1))
    for anum in atom_props.get("spin_beta", []):
        spins.append((anum, -1))
    if spins:
        outstr += "ATOMSPIN\n"
        outstr += "{}\n".format(len(spins))
        for anum, spin in sorted(spins):
            outstr += "{0} {1}\n".format(anum, spin)

    # SCF/Other Optional Keywords
    outstr += format_value(indict, ["scf", "numerical"])
    outstr += format_value(indict, ["scf", "fock_mixing"])
    outstr += format_value(indict, ["scf", "spinlock"])
    for keyword in get_keys(indict, ["scf", "post_scf"], []):
        outstr += "{}\n".format(keyword)

    # Hamiltonian and SCF End
    outstr += "END\n"
    return outstr


def _geometry_block(outstr, indict, atom_props):
    # Geometry
    outstr += "EXTERNAL\n"  # we assume external geometry
    # Geometry Optional Keywords (including optimisation)
    for keyword in get_keys(indict, ["geometry", "info_print"], []):
        outstr += "{}\n".format(keyword)
    for keyword in get_keys(indict, ["geometry", "info_external"], []):
        outstr += "{}\n".format(keyword)
    if "optimise" in indict.get("geometry", {}):
        outstr += "OPTGEOM\n"
        outstr += format_value(indict, ["geometry", "optimise", "type"])
        unfixed = atom_props.get("unfixed", [])
        if unfixed:
            outstr += "FRAGMENT\n"
            outstr += "{}\n".format(len(unfixed))
            outstr += " ".join([str(a) for a in sorted(unfixed)]) + " \n"
        outstr += format_value(indict, ["geometry", "optimise", "hessian"])
        outstr += format_value(indict, ["geometry", "optimise", "gradient"])
        for keyword in get_keys(indict, ["geometry", "optimise", "info_print"],
                                []):
            outstr += "{}\n".format(keyword)
        outstr += format_value(indict, ["geometry", "optimise", "convergence"])
        outstr += "ENDOPT\n"

    # Geometry End
    outstr += "END\n"
    return outstr


def _basis_set_block(outstr, indict, basis_sets, atom_props):
    # Basis Sets
    if isinstance(basis_sets[0], six.string_types):
        outstr += "\n".join([basis_set.strip() for basis_set in basis_sets])
    else:
        outstr += "\n".join(
            [basis_set.content.strip() for basis_set in basis_sets])
    outstr += "\n99 0\n"
    # GHOSTS
    ghosts = atom_props.get("ghosts", [])
    if ghosts:
        outstr += "GHOSTS\n"
        outstr += "{}\n".format(len(ghosts))
        outstr += " ".join([str(a) for a in sorted(ghosts)]) + " \n"

    # Basis Sets Optional Keywords
    outstr += format_value(indict, ["basis_set"])
    # Basis Sets End
    outstr += "END\n"
    return outstr
