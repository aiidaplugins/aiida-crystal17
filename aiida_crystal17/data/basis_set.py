"""
a data type to store CRYSTAL17 basis sets
"""
from __future__ import absolute_import
import os

import yaml
import six

from aiida.common.utils import classproperty
from aiida.orm.data.singlefile import SinglefileData
from aiida_crystal17.utils import flatten_dict, unflatten_dict

BASISGROUP_TYPE = 'data.basisset.family'

_ATOMIC_SYMBOLS = {
    1: 'H',
    2: 'He',
    3: 'Li',
    4: 'Be',
    5: 'B',
    6: 'C',
    7: 'N',
    8: 'O',
    9: 'F',
    10: 'Ne',
    11: 'Na',
    12: 'Mg',
    13: 'Al',
    14: 'Si',
    15: 'P',
    16: 'S',
    17: 'Cl',
    18: 'Ar',
    19: 'k',
    20: 'Ca',
    21: 'Sc',
    22: 'Ti',
    23: 'v',
    24: 'Cr',
    25: 'Mn',
    26: 'Fe',
    27: 'Co',
    28: 'Ni',
    29: 'Cu',
    30: 'Zn',
    31: 'Ga',
    32: 'Ge',
    33: 'As',
    34: 'Se',
    35: 'Br',
    36: 'Kr',
    37: 'Rb',
    38: 'Sr',
    39: 'Y',
    40: 'Zr',
    41: 'Nb',
    42: 'Mo',
    43: 'Tc',
    45: 'Ru',
    46: 'Pd',
    47: 'Ag',
    48: 'Cd',
    49: 'In',
    50: 'Sn',
    51: 'Sb',
    52: 'Te',
    53: 'I',
    54: 'Xe',
    55: 'Cs',
    56: 'Ba',
    57: 'La',
    72: 'Hf',
    73: 'Ta',
    74: 'W',
    75: 'Re',
    76: 'Os',
    77: 'Ir',
    78: 'Pt',
    79: 'Au',
    80: 'Hg',
    81: 'Tl',
    82: 'Pb',
    83: 'Bi',
    84: 'Po',
    85: 'At',
    86: 'Rn',
    87: 'Fr',
    88: 'Ra',
    89: 'Ac',
    104: 'Rf',
    105: 'Db',
    106: 'Sg',
    107: 'Bh',
    108: 'Hs',
    109: 'Mt'
}


def get_basissets_from_structure(structure, family_name):
    """
    Given a family name (a BasisSetFamily group in the DB) and an AiiDA
    structure, return a dictionary associating each kind name with its
    BasisSetData object.

    :raise MultipleObjectsError: if more than one Basis Set for the same element is
       found in the group.
    :raise NotExistent: if no Basis Set for an element in the group is
       found in the group.
    """
    from aiida.common.exceptions import NotExistent, MultipleObjectsError

    family_bases = {}
    family = BasisSetData.get_basis_group(family_name)
    for node in family.nodes:
        if isinstance(node, BasisSetData):
            if node.element in family_bases:
                raise MultipleObjectsError(
                    "More than one BasisSetData for element {} found in "
                    "family {}".format(node.element, family_name))
            family_bases[node.element] = node

    basis_list = {}
    for kind in structure.kinds:
        symbol = kind.symbol
        try:
            basis_list[kind.name] = family_bases[symbol]
        except KeyError:
            raise NotExistent(
                "No BasisSetData for element {} found in family {}".format(
                    symbol, family_name))

    return basis_list


def get_basisset_dict(structure, family_name):
    """
    Get a dictionary of {kind: basis} for all the elements within the given
    structure using a the given basis set family name.

    :param structure: The structure that will be used.
    :param family_name: the name of the group containing the basis sets
    """
    from collections import defaultdict

    # A dict {kind_name: basis_object}
    kind_basis_dict = get_basissets_from_structure(structure, family_name)

    # We have to group the species by basis, I use the basis PK
    # basis_dict will just map PK->basis_object
    basis_dict = {}
    # Will contain a list of all species of the basis with given PK
    basis_species = defaultdict(list)

    for kindname, basis in kind_basis_dict.iteritems():
        basis_dict[basis.pk] = basis
        basis_species[basis.pk].append(kindname)

    bases = {}
    for basis_pk in basis_dict:
        basis = basis_dict[basis_pk]
        kinds = basis_species[basis_pk]
        for kind in kinds:
            bases[kind] = basis

    return bases


# pylint: disable=too-many-locals
def upload_basisset_family(folder,
                           group_name,
                           group_description,
                           stop_if_existing=True,
                           extension=".basis"):
    """
    Upload a set of Basis Set files in a given group.

    :param folder: a path containing all Basis Set files to be added.
        Only files ending in the set extension (case-insensitive) are considered.
    :param group_name: the name of the group to create. If it exists and is
        non-empty, a UniquenessError is raised.
    :param group_description: a string to be set as the group description.
        Overwrites previous descriptions, if the group was existing.
    :param stop_if_existing: if True, check for the md5 of the files and,
        if the file already exists in the DB, raises a MultipleObjectsError.
        If False, simply adds the existing UPFData node to the group.
    :param extension: the filename extension to look for
    """
    from aiida.common import aiidalogger
    from aiida.orm import Group
    from aiida.common.exceptions import UniquenessError, NotExistent

    # aiida v1 compatibility
    try:
        from aiida.backends.utils import get_automatic_user
        automatic_user = get_automatic_user()
    except ImportError:
        from aiida.orm.backend import construct_backend
        backend = construct_backend()
        automatic_user = backend.users.get_automatic_user()

    if not os.path.isdir(folder):
        raise ValueError("folder must be a directory")

    # only files, and only those ending with specified exension;
    # go to the real file if it is a symlink
    files = [
        os.path.realpath(os.path.join(folder, i)) for i in os.listdir(folder)
        if os.path.isfile(os.path.join(folder, i))
        and i.lower().endswith(extension)
    ]

    nfiles = len(files)

    try:
        group = Group.get(name=group_name, type_string=BASISGROUP_TYPE)
        group_created = False
    except NotExistent:
        group = Group(
            name=group_name, type_string=BASISGROUP_TYPE, user=automatic_user)
        group_created = True

    if group.user.email != automatic_user.email:
        raise UniquenessError(
            "There is already a BasisFamily group with name {}"
            ", but it belongs to user {}, therefore you "
            "cannot modify it".format(group_name, group.user.email))

    # Always update description, even if the group already existed
    group.description = group_description

    # NOTE: GROUP SAVED ONLY AFTER CHECKS OF UNICITY

    basis_and_created = retrieve_basis_sets(files, stop_if_existing)
    # check whether basisset are unique per element
    elements = [(i[0].element, i[0].md5sum) for i in basis_and_created]
    # If group already exists, check also that I am not inserting more than
    # once the same element
    if not group_created:
        for aiida_n in group.nodes:
            # Skip non-basis sets
            if not isinstance(aiida_n, BasisSetData):
                continue
            elements.append((aiida_n.element, aiida_n.md5sum))

    elements = set(elements)  # Discard elements with the same MD5, that would
    # not be stored twice
    elements_names = [e[0] for e in elements]

    if not len(elements_names) == len(set(elements_names)):
        duplicates = set(
            [x for x in elements_names if elements_names.count(x) > 1])
        duplicates_string = ", ".join(i for i in duplicates)
        raise UniquenessError("More than one Basis found for the elements: " +
                              duplicates_string + ".")

        # At this point, save the group, if still unstored
    if group_created:
        group.store()

    # save the basis set in the database, and add them to group
    for basisset, created in basis_and_created:
        if created:
            basisset.store()

            aiidalogger.debug("New node {0} created for file {1}".format(  # pylint: disable=logging-format-interpolation
                basisset.uuid, basisset.filename))
        else:
            aiidalogger.debug("Reusing node {0} for file {1}".format(  # pylint: disable=logging-format-interpolation
                basisset.uuid, basisset.filename))

    # Add elements to the group all together
    group.add_nodes(basis for basis, created in basis_and_created)

    nuploaded = len([_ for _, created in basis_and_created if created])

    return nfiles, nuploaded


def retrieve_basis_sets(files, stop_if_existing):
    """ get existing basis sets or create if not

    :param files: list of basis set file paths
    :param stop_if_existing: if True, check for the md5 of the files and,
        if the file already exists in the DB, raises a MultipleObjectsError.
        If False, simply adds the existing UPFData node to the group.
    :return:
    """
    import aiida.common
    from aiida.orm.querybuilder import QueryBuilder

    basis_and_created = []
    for f in files:
        md5sum = aiida.common.utils.md5_file(f)
        qb = QueryBuilder()
        qb.append(BasisSetData, filters={'attributes.md5': {'==': md5sum}})
        existing_basis = qb.first()

        if existing_basis is None:
            # return the basis set data instances, not stored
            basisset, created = BasisSetData.get_or_create(
                f, use_first=True, store_basis=False)
            # to check whether only one basis set per element exists
            # NOTE: actually, created has the meaning of "to_be_created"
            basis_and_created.append((basisset, created))
        else:
            if stop_if_existing:
                raise ValueError("A Basis Set with identical MD5 to "
                                 " {} cannot be added with stop_if_existing"
                                 "".format(f))
            existing_basis = existing_basis[0]
            basis_and_created.append((existing_basis, False))

    return basis_and_created


# pylint: disable=too-many-locals
def parse_basis(fname):
    """get relevant information from the basis file

    :param fname: the file path
    :return: the parsed data

    - The basis file must contain one basis set in the CRYSTAL17 format
    - lines beginning # will be ignored
    - the file can also start with a fenced (with ---), yaml formatted header section
        - Note keys should not contain '.'s

    Example:

        # an ignored comment
        ---
        author: J Smith
        year: 1999
        ---
        8 2
        1 0 3  2.  0.
        1 1 3  6.  0.
    
    """
    from aiida.common.exceptions import ParsingError
    parsed_data = {}

    in_yaml = False
    yaml_lines = []
    used_keys = ["atomic_number", "num_shells", "element", "basis_type"]
    parsing_data = False
    with open(fname) as f:
        for line in f:
            # ignore commented lines
            if line.strip().startswith("#"):
                continue
            if line.strip() == "---" and not parsing_data:
                if not in_yaml:
                    in_yaml = True
                    continue
                else:
                    head_data = yaml.load("".join(yaml_lines))
                    head_data = {} if not head_data else head_data
                    if not isinstance(head_data, dict):
                        raise ParsingError(
                            "the header data could not be read for file: {}".
                            format(fname))
                    if set(head_data.keys()).intersection(used_keys):
                        raise ParsingError(
                            "the header data contained a forbidden key(s) {} for file: {}".
                            format(used_keys, fname))
                    parsed_data = head_data
                    in_yaml = False
                    parsing_data = True
                    continue
            if in_yaml:
                yaml_lines.append(line)
                continue
            # parsing_data = True
            # first line should contain the atomic number as the first argument
            first_line = line.strip().split()
            if not len(first_line) == 2:
                raise ParsingError(
                    "The first line should contain only two fields: '{}' for file {}".
                    format(line, fname))

            atomic_number_str = first_line[0]
            if not atomic_number_str.isdigit():
                raise ParsingError(
                    "The first field should be the atomic number '{}' for file {}".
                    format(line, fname))
            anumber = int(atomic_number_str)
            atomic_number = None
            if anumber < 99:
                atomic_number = anumber
                basis_type = "all-electron"

            elif 200 < anumber < 999:
                atomic_number = anumber % 100
                basis_type = "valence-electron"

            elif anumber > 1000:
                atomic_number = anumber % 100
                basis_type = "all-electron"

            if anumber is None:
                raise ParsingError(
                    "Illegal atomic number {} for file {}".format(
                        anumber, fname))

            num_shells_str = first_line[0]
            if not num_shells_str.isdigit():
                raise ParsingError(
                    "The second field should be the number of shells {} for file {}".
                    format(line, fname))
            num_shells = int(num_shells_str)

            parsed_data["atomic_number"] = atomic_number
            parsed_data["element"] = _ATOMIC_SYMBOLS[atomic_number]
            parsed_data["basis_type"] = basis_type
            parsed_data["num_shells"] = num_shells

            break

    return parsed_data


class BasisSetData(SinglefileData):
    """
    a data type to store CRYSTAL17 basis sets
    it is intended to work much like the UpfData type


    Example file:

        # an ignored comment
        ---
        author: J Smith
        year: 1999
        ---
        8 2
        1 0 3  2.  0.
        1 1 3  6.  0.

    """

    @classmethod
    def get_or_create(cls, filename, use_first=False, store_basis=True):
        """
        Pass the same parameter of the init; if a file with the same md5
        is found, that BasisSetData is returned.

        :param filename: an absolute filename on disk
        :param use_first: if False (default), raise an exception if more than \
                one potential is found.\
                If it is True, instead, use the first available basis set.
        :param bool store_basis: If false, the BasisSetData objects are not stored in
                the database. default=True.
        :return (basis, created): where basis is the BasisSetData object, and create is either\
            True if the object was created, or False if the object was retrieved\
            from the DB.
        """
        import aiida.common.utils

        if not os.path.isabs(filename):
            raise ValueError("filename must be an absolute path")
        md5 = aiida.common.utils.md5_file(filename)

        basissets = cls.from_md5(md5)
        if not basissets:
            if store_basis:
                instance = cls(file=filename).store()
                return (instance, True)

            instance = cls(file=filename)
            return (instance, True)
        else:
            if len(basissets) > 1:
                if use_first:
                    return (basissets[0], False)
                else:
                    raise ValueError("More than one copy of a basis set "
                                     "with the same MD5 has been found in the "
                                     "DB. pks={}".format(",".join(
                                         [str(i.pk) for i in basissets])))
            return (basissets[0], False)

    @classproperty
    def basisfamily_type_string(cls):
        return BASISGROUP_TYPE

    def store(self, with_transaction=True, use_cache=None):
        """
        Store a new node in the DB, also saving its repository directory
        and attributes, and reparsing the file so that the md5 and the element
        are correctly reset.

        After being called attributes cannot be
        changed anymore! Instead, extras can be changed only AFTER calling
        this store() function.

        :note: After successful storage, those links that are in the cache, and
            for which also the parent node is already stored, will be
            automatically stored. The others will remain unstored.

        :parameter with_transaction: if False, no transaction is used. This
          is meant to be used ONLY if the outer calling function has already
          a transaction open!
        :parameter use_cache: whether to cache the node
        """
        from aiida.common.exceptions import ParsingError, ValidationError
        import aiida.common.utils

        basis_abspath = self.get_file_abs_path()
        if not basis_abspath:
            raise ValidationError("No valid Basis Set was passed!")

        parsed_data = parse_basis(basis_abspath)
        md5sum = aiida.common.utils.md5_file(basis_abspath)

        if "element" not in parsed_data:
            raise ParsingError("No 'element' parsed in the Basis Set file {};"
                               " unable to store".format(self.filename))

        for key, val in flatten_dict(parsed_data).items():
            self._set_attr(key, val)
        self._set_attr('md5', md5sum)

        return super(BasisSetData, self).store(
            with_transaction=with_transaction, use_cache=use_cache)

    @classmethod
    def from_md5(cls, md5):
        """
        Return a list of all Basis Sets that match a given MD5 hash.

        Note that the hash has to be stored in a _md5 attribute, otherwise
        the basis will not be found.
        """
        from aiida.orm.querybuilder import QueryBuilder
        qb = QueryBuilder()
        qb.append(cls, filters={'attributes.md5': {'==': md5}})
        return [_ for [_] in qb.all()]

    def set_file(self, filename):
        """
        pre-parse the file to store the attributes.
        """
        from aiida.common.exceptions import ParsingError
        import aiida.common.utils

        parsed_data = parse_basis(filename)
        md5sum = aiida.common.utils.md5_file(filename)

        if "element" not in parsed_data:
            raise ParsingError("No 'element' parsed in the Basis Set file {};"
                               " unable to store".format(self.filename))

        super(BasisSetData, self).set_file(filename)

        for key, val in flatten_dict(parsed_data).items():
            self._set_attr(key, val)
        self._set_attr('md5', md5sum)

    def get_basis_family_names(self):
        """
        Get the list of all basiset family names to which the basis belongs
        """
        from aiida.orm import Group

        return [
            _.name for _ in Group.query(
                nodes=self, type_string=self.basisfamily_type_string)
        ]

    @property
    def element(self):
        return self.get_attr('element', None)

    @property
    def md5sum(self):
        return self.get_attr('md5', None)

    @property
    def metadata(self):
        return unflatten_dict({k: v for k, v in self.iterattrs()})

    def _validate(self):
        from aiida.common.exceptions import ValidationError, ParsingError
        import aiida.common.utils

        super(BasisSetData, self)._validate()

        basis_abspath = self.get_file_abs_path()
        if not basis_abspath:
            raise ValidationError("No valid Basis Set was passed!")

        try:
            parsed_data = parse_basis(basis_abspath)
        except ParsingError:
            raise ValidationError("The file '{}' could not be "
                                  "parsed".format(basis_abspath))
        md5 = aiida.common.utils.md5_file(basis_abspath)

        try:
            element = parsed_data['element']
        except KeyError:
            raise ValidationError("No 'element' could be parsed in the UPF "
                                  "file {}".format(basis_abspath))

        try:
            attr_element = self.get_attr('element')
        except AttributeError:
            raise ValidationError("attribute 'element' not set.")

        try:
            attr_md5 = self.get_attr('md5')
        except AttributeError:
            raise ValidationError("attribute 'md5' not set.")

        if attr_element != element:
            raise ValidationError("Attribute 'element' says '{}' but '{}' was "
                                  "parsed instead.".format(
                                      attr_element, element))

        if attr_md5 != md5:
            raise ValidationError("Attribute 'md5' says '{}' but '{}' was "
                                  "parsed instead.".format(attr_md5, md5))

    @classmethod
    def get_basis_group(cls, group_name):
        """
        Return the BasisFamily group with the given name.
        """
        from aiida.orm import Group

        return Group.get(
            name=group_name, type_string=cls.basisfamily_type_string)

    @classmethod
    def get_basis_groups(cls, filter_elements=None, user=None):
        """
        Return all names of groups of type BasisFamily, possibly with some filters.

        :param filter_elements: A string or a list of strings.
               If present, returns only the groups that contains one Basis for
               every element present in the list. Default=None, meaning that
               all families are returned.
        :param user: if None (default), return the groups for all users.
               If defined, it should be either a DbUser instance, or a string
               for the username (that is, the user email).
        """
        from aiida.orm import Group

        group_query_params = {"type_string": cls.basisfamily_type_string}

        if user is not None:
            group_query_params['user'] = user

        if isinstance(filter_elements, six.string_types):
            filter_elements = [filter_elements]

        if filter_elements is not None:
            actual_filter_elements = {_.capitalize() for _ in filter_elements}

            group_query_params['node_attributes'] = {
                'element': actual_filter_elements
            }

        all_basis_groups = Group.query(**group_query_params)

        groups = [(g.name, g) for g in all_basis_groups]
        # Sort by name
        groups.sort()
        # Return the groups, without name
        return [_[1] for _ in groups]
