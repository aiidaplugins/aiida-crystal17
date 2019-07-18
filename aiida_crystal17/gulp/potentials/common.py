import copy

INDEX_SEP = "-"


def filter_by_species(data, species):
    """filter a potential dict by a subset of species

    Parameters
    ----------
    data : dict
        a potential or fitting dict
    species : list[str]
        the species to filter by

    Returns
    -------
    dict
        data filtered by species and with all species index keys re-indexed

    Raises
    ------
    KeyError
        if the data does not adhere to the potential or fitting jsonschema
    AssertionError
        if the filter set is not a subset of the available species

    """
    species = sorted(list(set(species)))

    if not set(species).issubset(data["species"]):
        raise AssertionError(
            "the filter set ({}) is not a subset of the available species ({})".format(
                set(species), set(data["species"])
            ))
    data = copy.deepcopy(data)
    indices = set([str(i) for i, s in enumerate(data["species"]) if s in species])

    def convert_indices(key):
        return INDEX_SEP.join([str(species.index(data["species"][int(k)])) for k in key.split(INDEX_SEP)])

    for key in ['1body', '2body', '3body', '4body']:
        if key not in data:
            continue
        data[key] = {convert_indices(k): v for k, v in data[key].items() if indices.issuperset(k.split(INDEX_SEP))}

    data["species"] = species

    return data
