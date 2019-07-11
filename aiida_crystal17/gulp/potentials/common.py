import copy

from aiida_crystal17.validation import validate_against_schema


def filter_by_species(data, species):
    """ filter a potential dict by a subset of species
    NB: all species index keys will be re-indexed
    """
    validate_against_schema(data, "potential.base.schema.json")

    species = sorted(list(set(species)))

    if not set(species).issubset(data["species"]):
        raise AssertionError(
            "the filter set ({}) is not a subset of the available species ({})".format(
                set(species), set(data["species"])
            ))
    data = copy.deepcopy(data)
    indices = set([str(i) for i, s in enumerate(data["species"]) if s in species])

    def convert_indices(key):
        return ".".join([str(species.index(data["species"][int(k)])) for k in key.split(".")])

    for key in ['1body', '2body', '3body', '4body']:
        if key not in data:
            continue
        data[key] = {convert_indices(k): v for k, v in data[key].items() if indices.issuperset(k.split("."))}

    data["species"] = species

    return data
