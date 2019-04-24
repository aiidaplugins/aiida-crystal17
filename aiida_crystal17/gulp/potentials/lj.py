from aiida_crystal17.validation import validate_against_schema


def write_gulp(data, species_filter=None):
    """write reaxff data in GULP input format

    :param data: dictionary of data
    :param species_filter: list of symbols to filter
    :rtype: str

    """
    validate_against_schema(data, "lj_potential.schema.json")

    lines = []

    lines.append("lennard {m} {n}".format(
        m=data.get("m", 12), n=data.get("n", 6)))

    species_used = {}

    for species1 in sorted(data["atoms"].keys()):
        if species_filter is not None and species1 not in species_filter:
            continue
        for species2 in sorted(data["atoms"][species1].keys()):
            if species_filter is not None and species2 not in species_filter:
                continue

            subdata = data["atoms"][species1][species2]

            if (species2, species1) in species_used:
                if subdata != species_used[(species2, species1)]:
                    raise ValueError(
                        "{0} {1} pairing is stored twice, but with "
                        "different parameters".format(species1, species2))
                continue

            if "rmin" in subdata:
                lines.append("{atom1} {atom2} {A} {B} {rmin} {rmax}".format(
                    atom1=species1, atom2=species2, **subdata
                ))
            else:
                lines.append("{atom1} {atom2} {A} {B} {rmax}".format(
                    atom1=species1, atom2=species2, **subdata
                ))

            species_used[(species1, species2)] = subdata

    return "\n".join(lines)
