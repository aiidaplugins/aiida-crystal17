
from aiida_crystal17.validation import validate_against_schema


def read_doss_contents(content):
    """ read the contents of a doss.d3 input file """
    lines = content.splitlines()
    params = {}
    assert lines[0].rstrip() == "NEWK"
    params["shrink_is"] = int(lines[1].split()[0])
    params["shrink_isp"] = int(lines[1].split()[1])
    assert lines[2].rstrip() == "1 0"
    assert lines[3].rstrip() == "DOSS"
    settings = [int(i) for i in lines[4].split()]
    assert len(settings) == 7 or len(settings) == 9
    npro = settings[0]
    params["npt"] = settings[1]
    params["band_first"] = settings[2]
    params["band_last"] = settings[3]
    iplo = settings[4]  # noqa: F841
    params["npol"] = settings[5]
    npr = settings[6]  # noqa: F841
    if len(settings) == 9:
        params["energy_gap"] = [settings[7], settings[8]]
    else:
        params["energy_gap"] = None
    params["projections"] = {"atoms": [], "orbitals": []}
    for line in lines[5:5 + npro]:
        values = [int(i) for i in line.split()]
        if values[0] > 0:
            params["projections"]["orbitals"].append(values[1:])
        else:
            params["projections"]["atoms"].append(values[1:])
    assert lines[5 + npro] == "END"

    validate_against_schema(params, "doss_input.schema.json")

    return params


def create_doss_content(params):
    """ create the contents of a doss.d3 input file

    NPRO; number of additional (to total) projected densities to calculate (<= 15)
    NPT; number of uniformly spaced energy values (from bottom of band INZB to top of band IFNB)
    INZB; band considered in DOS calculation
    IFNB;  last band considered in DOS calculation
    IPLO; output type (1 = to .d25 file)
    NPOL; number of Legendre polynomials used to expand DOSS (<= 25)
    NPR; number of printing options to switch on

    Unit of measure:  energy:  hartree; DOSS: state/hartree/cell.
    """
    validate_against_schema(params, "doss_input.schema.json")

    lines = ["NEWK"]
    if not params["shrink_isp"] >= 2 * params["shrink_is"]:
        raise AssertionError(
            "ISP<2*IS, low values of the ratio ISP/IS can lead to numerical instabilities.")
    lines.append("{} {}".format(params["shrink_is"], params["shrink_isp"]))
    lines.append("1 0")
    lines.append("DOSS")

    if "projections" in params:
        proj_atoms = params["projections"].get("atoms", None)
        if proj_atoms is None:
            proj_atoms = []
        proj_orbitals = params["projections"].get("orbitals", None)
        if proj_orbitals is None:
            proj_orbitals = []
    else:
        proj_atoms = []
        proj_orbitals = []

    npro = len(proj_atoms) + len(proj_orbitals)

    settings_line = "{npro} {npt} {inzb} {ifnb} {iplo} {npol} {npr}".format(
        npro=npro,
        npt=params.get("npt", 1000),
        inzb=params["band_first"],
        ifnb=params["band_last"],
        iplo=1,  # output type (1=fort.25, 2=DOSS.DAT)
        npol=params.get("npol", 14),
        npr=0  # number of printing options
    )
    if params.get("energy_gap", None) is not None:
        settings_line += " {} {}".format(*params["energy_gap"])
    lines.append(settings_line)

    for atoms in proj_atoms:
        lines.append(str(-1 * len(atoms)) + " " + " ".join([str(a) for a in atoms]))
    for orbitals in proj_orbitals:
        lines.append(str(len(orbitals)) + " " + " ".join([str(o) for o in orbitals]))

    lines.append("END")
    return lines
