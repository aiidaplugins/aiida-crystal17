#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 Chris Sewell
#
# This file is part of aiida-crystal17.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms and conditions
# of version 3 of the GNU Lesser General Public License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
""" a data type to store CRYSTAL17 basis sets
"""
from __future__ import absolute_import

import hashlib
import io
import os
import tempfile

import six
from ruamel.yaml import YAML
from aiida.common.utils import classproperty
from aiida.orm import Data, Str
from aiida_crystal17.common import flatten_dict, unflatten_dict
from aiida_crystal17.common.atoms import SYMBOLS_R
from aiida_crystal17.parsers.raw.parse_bases import parse_bsets_stdin

BASISGROUP_TYPE = 'crystal17.basisset'


def _retrieve_basis_sets(files, stop_if_existing):
    """ get existing basis sets or create if not

    :param files: list of basis set file paths
    :param stop_if_existing: if True, check for the md5 of the files and,
        if the file already exists in the DB, raises a MultipleObjectsError.
        If False, simply adds the existing BasisSetData node to the group.
    :return:
    """
    from aiida.orm.querybuilder import QueryBuilder

    basis_and_created = []
    for f in files:
        _, content = parse_basis(f)
        md5sum = md5_from_string(content)
        qb = QueryBuilder()
        qb.append(BasisSetData, filters={'attributes.md5': {'==': md5sum}})
        existing_basis = qb.first()

        if existing_basis is None:
            # return the basis set data instances, not stored
            basisset, created = BasisSetData.get_or_create(f, use_first=True, store_basis=False)
            # to check whether only one basis set per element exists
            # NOTE: actually, created has the meaning of "to_be_created"
            basis_and_created.append((basisset, created))
        else:
            if stop_if_existing:
                raise ValueError('A Basis Set with identical MD5 to '
                                 ' {} cannot be added with stop_if_existing'
                                 ''.format(f))
            existing_basis = existing_basis[0]
            basis_and_created.append((existing_basis, False))

    return basis_and_created


def parse_basis(fname):
    """get relevant information from the basis file

    :param fname: the file path
    :return: (metadata_dict, content_str)

    - The basis file must contain one basis set in the CRYSTAL17 format
    - blank lines and lines beginning '#' will be ignored
    - the file can also start with a fenced (with ---),
      yaml formatted header section
      (Note keys should not contain '.'s)

    Example

    ::

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
    meta_data = {}

    in_yaml = False
    yaml_lines = []
    protected_keys = ['atomic_number', 'num_shells', 'element', 'basis_type', 'content']
    parsing_data = False
    content = []

    try:
        contentlines = fname.readlines()
        fname = fname.name
    except AttributeError:
        with io.open(fname, encoding='utf8') as f:
            contentlines = f.read().splitlines()

    for line in contentlines:
        # ignore commented and blank lines
        if line.strip().startswith('#') or not line.strip():
            continue
        if line.strip() == '---' and not parsing_data:
            if not in_yaml:
                in_yaml = True
                continue
            else:
                yaml = YAML(typ='safe')
                head_data = yaml.load('\n'.join(yaml_lines))
                head_data = {} if not head_data else head_data
                if not isinstance(head_data, dict):
                    raise ParsingError('the header data could not be read for file: {}'.format(fname))
                if set(head_data.keys()).intersection(protected_keys):
                    raise ParsingError('the header data contained a forbidden key(s) '
                                       '{} for file: {}'.format(protected_keys, fname))
                meta_data = head_data
                in_yaml = False
                parsing_data = True
                continue
        if in_yaml:
            yaml_lines.append(line)
            continue

        parsing_data = True

        content.append(line.strip())

    data = parse_bsets_stdin('\n'.join(content), isolated=True)
    if len(data) > 1:
        raise ParsingError('the basis set string contains more than one basis set: {}'.format(list(data.keys())))
    atomic_symbol = list(data.keys())[0]

    meta_data['atomic_number'] = atomic_number = SYMBOLS_R[atomic_symbol]
    meta_data['element'] = atomic_symbol
    meta_data['basis_type'] = basis_type = data[atomic_symbol]['type']
    meta_data['num_shells'] = num_shells = len(data[atomic_symbol]['bs'])
    meta_data['orbital_types'] = [o['type'] for o in data[atomic_symbol]['bs']]

    # the input atomic number may be > 100, but we should standardise this in the stored file
    first_line = content[0].strip().split()
    if len(first_line) != 2 or first_line[1] != str(num_shells):
        raise ParsingError(
            "The first line should contain only the atomic id and num shells ({}): '{}' for file {}".format(
                num_shells, line, fname))
    newline = '{0} {1}'.format(atomic_number if basis_type == 'all-electron' else 200 + atomic_number, num_shells)
    content[0] = newline

    return meta_data, '\n'.join(content)


def md5_from_string(string, encoding='utf-8'):
    """ return md5 hash of string

    :param string: the string to hash
    :param encoding: the encoding to use
    :return:
    """
    md5 = hashlib.md5(string.encode(encoding))
    return md5.hexdigest()


class BasisSetData(Data):
    """
    a data type to store CRYSTAL17 basis sets
    it is intended to work much like the UpfData type

    - The basis file must contain one basis set in the CRYSTAL17 format
    - lines beginning # will be ignored
    - the file can also start with a fenced,
      yaml formatted header section (starting/ending '---')
      (Note keys should not contain '.'s)
    - only the actual basis data (not commented lines or the header section)
      will be stored as a file and hashed

    Example file

    ::

        # an ignored comment
        ---
        author: J Smith
        year: 1999
        ---
        8 2
        1 0 3  2.  0.
        1 1 3  6.  0.

    """

    def __init__(self, filepath, **kwargs):
        super(BasisSetData, self).__init__(**kwargs)
        self.set_file(filepath)

    @property
    def filename(self):
        """
        Returns the name of the file stored
        """
        return self.get_attribute('filename')

    @property
    def md5sum(self):
        """ return the md5 hash of the basis set

        :return:
        """
        return self.get_attribute('md5', None)

    def set_file(self, filepath):
        """
        pre-parse the file to store the attributes and content separately.
        """
        # to keep things simple,
        # we only allow one file to ever be set for one class instance
        if 'filename' in list(self.attributes_keys()):
            raise ValueError('a file has already been set for this BasisSetData instance')

        metadata, content = parse_basis(filepath)
        md5sum = md5_from_string(content)

        # store the metadata and md5 in the database
        for key, val in flatten_dict(metadata).items():
            self.set_attribute(key, val)
        self.set_attribute('md5', md5sum)

        # store the rest of the file content as a file in the file repository
        filename = os.path.basename(filepath)
        with tempfile.NamedTemporaryFile() as f:
            with io.open(f.name, 'w', encoding='utf8') as fobj:
                fobj.writelines(content)

            super(BasisSetData, self).put_object_from_file(
                path=f.name, key=filename, mode='w', encoding='utf8', force=False)

        self.set_attribute('filename', filename)

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

    @property
    def metadata(self):
        """return the attribute data as a nested dictionary

        :return: metadata dict
        """
        return unflatten_dict({k: v for k, v in self.attributes_items()})

    def open(self, mode='r'):  # pylint: disable=arguments-differ
        """Return an open file handle to the content of this data node.

        :param mode: the mode with which to open the file handle
        :return: a file handle in read mode
        """
        return self._repository.open(self.filename, mode=mode)

    @property
    def content(self):
        """return the content string for insertion into .d12 file

        :return: content_str
        """
        # TODO dealing with caching? see get_array in ArrayData,
        # or are we doing this with the md5 hash
        with self.open() as handle:
            return handle.read()

    @property
    def element(self):
        """return the element symbol associated with the basis set"""
        return self.get_attribute('element', None)

    def get_data(self):
        """ return the basis set content, parsed to a JSON format"""
        return parse_bsets_stdin(self.content, isolated=True)[self.element]

    @classmethod
    def get_or_create(cls, filepath, use_first=False, store_basis=True):
        """
        Pass the same parameter of the init; if a file with the same md5
        is found, that BasisSetData is returned.

        :param filepath: an absolute filename on disk
        :param use_first: if False (default), raise an exception if more than \
                one basis set is found.\
                If it is True, instead, use the first available basis set.
        :param bool store_basis: If false, \
        the BasisSetData objects are not stored in
                the database. default=True.
        :return (basis, created): where basis is the BasisSetData object, \
            and create is either True if the object was created, \
                or False if the object was retrieved from the DB.
        """
        if not os.path.isabs(filepath):
            raise ValueError('filepath must be an absolute path')

        _, content = parse_basis(filepath)
        print()
        print(content)
        md5sum = md5_from_string(content)

        basissets = cls.from_md5(md5sum)
        if not basissets:
            if store_basis:
                instance = cls(filepath=filepath).store()
                return (instance, True)

            instance = cls(filepath=filepath)
            return (instance, True)
        else:
            if len(basissets) > 1:
                if use_first:
                    return (basissets[0], False)
                else:
                    raise ValueError('More than one copy of a basis set '
                                     'with the same MD5 has been found in the '
                                     'DB. pks={}'.format(','.join([str(i.pk) for i in basissets])))
            return basissets[0], False

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
        """
        from aiida.common.exceptions import ValidationError

        if self.is_stored:
            return self

        if self.md5sum is None:
            raise ValidationError('No valid Basis Set was passed!')

        with self.open('r') as handle:
            metadata, content = parse_basis(handle)
        md5sum = md5_from_string(content)

        for key, val in flatten_dict(metadata).items():
            self.set_attribute(key, val)
        self.set_attribute('md5', md5sum)

        return super(BasisSetData, self).store(with_transaction=with_transaction, use_cache=use_cache)

    def _validate(self):
        from aiida.common.exceptions import ValidationError, ParsingError

        super(BasisSetData, self)._validate()

        try:
            filename = self.filename
        except AttributeError:
            raise ValidationError("attribute 'filename' not set.")

        objects = self.list_object_names()
        if [filename] != objects:
            raise ValidationError('The list of files in the folder does not '
                                  "match the 'filename' attribute. "
                                  "_filename='{}', content: {}".format(filename, self.list_object_names()))

        try:
            with self.open('r') as handle:
                metadata, content = parse_basis(handle)
        except (ParsingError, IOError, NotImplementedError) as err:
            raise ValidationError("The file '{}' could not be " 'parsed: {}'.format(err))
        md5 = md5_from_string(content)

        try:
            element = metadata['element']
        except KeyError:
            raise ValidationError("No 'element' could be parsed in the " 'BasisSet file')

        try:
            attr_element = self.get_attribute('element')
        except AttributeError:
            raise ValidationError("attribute 'element' not set.")

        try:
            attr_md5 = self.get_attribute('md5')
        except AttributeError:
            raise ValidationError("attribute 'md5' not set.")

        if attr_element != element:
            raise ValidationError("Attribute 'element' says '{}' but '{}' was "
                                  'parsed instead.'.format(attr_element, element))

        if attr_md5 != md5:
            raise ValidationError("Attribute 'md5' says '{}' but '{}' was " 'parsed instead.'.format(attr_md5, md5))

    @classproperty
    def basisfamily_type_string(cls):
        return BASISGROUP_TYPE

    def get_basis_family_names(self):
        """
        Get the list of all basiset family names to which the basis belongs
        """
        from aiida.orm import Group

        return [_.name for _ in Group.query(nodes=self, type_string=self.basisfamily_type_string)]

    @classmethod
    def get_basis_group(cls, group_name):
        """
        Return the BasisFamily group with the given name.
        """
        from aiida.orm import Group

        return Group.objects.get(label=group_name, type_string=cls.basisfamily_type_string)

    @classmethod
    def get_basis_group_map(cls, group_name):
        """get a mapping of elements to basissets in a basis set family

        Parameters
        ----------
        group_name : str
            the group name of the basis set

        Returns
        -------
        dict
            a mapping of element to basis set

        Raises
        ------
        aiida.common.exceptions.MultipleObjectsError
            if there is more than one element s

        """
        from aiida.common.exceptions import MultipleObjectsError
        family_bases = {}
        family = cls.get_basis_group(group_name)
        for node in family.nodes:
            if isinstance(node, cls):
                if node.element in family_bases:
                    raise MultipleObjectsError('More than one BasisSetData for element {} found in '
                                               'family {}'.format(node.element, group_name))
                family_bases[node.element] = node
        return family_bases

    @classmethod
    def get_basis_groups(cls, filter_elements=None, user=None):
        """
        Return all names of groups of type BasisFamily,
        possibly with some filters.

        :param filter_elements: A string or a list of strings.
               If present, returns only the groups that contains one Basis for
               every element present in the list. Default=None, meaning that
               all families are returned.
        :param user: if None (default), return the groups for all users.
               If defined, it should be either a DbUser instance, or a string
               for the username (that is, the user email).
        """
        from aiida.orm import Group
        from aiida.orm import QueryBuilder
        from aiida.orm import User

        query = QueryBuilder()
        filters = {'type_string': {'==': cls.basisfamily_type_string}}

        query.append(Group, filters=filters, tag='group', project='*')

        if user is not None:
            query.append(User, filters={'email': {'==': user}}, with_group='group')

        if isinstance(filter_elements, six.string_types):
            filter_elements = [filter_elements]

        if filter_elements is not None:
            # actual_filter_elements = [_ for _ in filter_elements]
            query.append(BasisSetData, filters={'attributes.element': {'in': filter_elements}}, with_group='group')

        query.order_by({Group: {'id': 'asc'}})
        query.distinct()
        return [_[0] for _ in query.all()]

    @classmethod
    def get_basissets_from_structure(cls, structure, family_name, by_kind=False):
        """
        Given a family name (a BasisSetFamily group in the DB) and an AiiDA
        structure, return a dictionary associating each element or kind name
        (if ``by_kind=True``) with its BasisSetData object.

        :raise aiida.common.exceptions.MultipleObjectsError:
            if more than one Basis Set for the same element is found in the group.
        :raise aiida.common.exceptions.NotExistent:
            if no Basis Set for an element in the group is found in the group.

        """
        from aiida.common.exceptions import NotExistent

        family_bases = cls.get_basis_group_map(family_name)

        basis_list = {}
        for kind in structure.kinds:
            symbol = kind.symbol
            if symbol not in family_bases:
                raise NotExistent('No BasisSetData for element {} found in family {}'.format(symbol, family_name))
            if by_kind:
                basis_list[kind.name] = family_bases[symbol]
            else:
                basis_list[symbol] = family_bases[symbol]

        return basis_list

    @classmethod
    def get_basissets_by_kind(cls, structure, family_name):
        """
        Get a dictionary of {kind: basis} for all the kinds within the given
        structure using the given basis set family name.

        :param structure: The structure that will be used.
        :param family_name: the name of the group containing the basis sets
        """
        from collections import defaultdict

        # A dict {kind_name: basis_object}
        kind_basis_dict = cls.get_basissets_from_structure(structure, family_name, by_kind=True)

        # We have to group the species by basis, I use the basis PK
        # basis_dict will just map PK->basis_object
        basis_dict = {}
        # Will contain a list of all species of the basis with given PK
        basis_species = defaultdict(list)

        for kindname, basis in kind_basis_dict.items():
            basis_dict[basis.pk] = basis
            basis_species[basis.pk].append(kindname)

        bases = {}
        for basis_pk in basis_dict:
            basis = basis_dict[basis_pk]
            kinds = basis_species[basis_pk]
            for kind in kinds:
                bases[kind] = basis

        return bases

    @classmethod
    def prepare_and_validate_inputs(cls, structure, basissets=None, basis_family=None):
        """validate and prepare a dictionary mapping elements of the structure
        to a BasisSetData node, for use as input to a calculation

        Parameters
        ----------
        structure : aiida.StructureData
        basissets : dict
            a dictionary where keys are the symbol names and value are BasisSetData nodes
        basis_family : str
            basis set family name to use

        Raises
        ------
        ValueError
            if neither basissets or basis_family is specified or if no BasisSetData is found for
            every element in the structure

        """
        if basissets and basis_family:
            raise ValueError('you cannot specify both "basissets" and "basis_family"')
        elif basissets is None and basis_family is None:
            raise ValueError('neither an explicit basissets dictionary nor a basis_family was specified')
        elif basis_family:
            if isinstance(basis_family, Str):
                basis_family = basis_family.value
            basissets = cls.get_basissets_from_structure(structure, basis_family, by_kind=False)

        elements_required = set([kind.symbol for kind in structure.kinds])
        if set(basissets.keys()) != elements_required:
            err_msg = ('Mismatch between the defined basissets and the list of '
                       'elements of the structure. Basissets: {}; elements: {}'.format(
                           set(basissets.keys()), elements_required))
            raise ValueError(err_msg)

        return basissets

    # pylint: disable=too-many-locals,too-many-arguments
    @classmethod
    def upload_basisset_family(cls,
                               folder,
                               group_name,
                               group_description,
                               stop_if_existing=True,
                               extension='.basis',
                               dry_run=False):
        """
        Upload a set of Basis Set files in a given group.

        :param folder: a path containing all Basis Set files to be added.
            Only files ending in set extension (case-insensitive) considered
        :param group_name: the name of the group to create. If it exists and is
            non-empty, a UniquenessError is raised.
        :param group_description: a string to be set as the group description.
            Overwrites previous descriptions, if the group was existing.
        :param stop_if_existing: if True, check for the md5 of the files and,
            if file already exists in the DB, raises a MultipleObjectsError.
            If False, simply adds the existing BasisSetData node to the group.
        :param extension: the filename extension to look for
        :param dry_run: If True, do not change the database.
        """
        from aiida.orm import Group, User
        from aiida.common.exceptions import UniquenessError

        if not os.path.isdir(folder):
            raise ValueError('folder must be a directory')

        # only files, and only those ending with specified exension;
        # go to the real file if it is a symlink
        files = []
        for i in os.listdir(folder):
            if not os.path.isfile(os.path.join(folder, i)):
                continue
            if not i.lower().endswith(extension):
                continue
            files.append(os.path.realpath(os.path.join(folder, i)))

        nfiles = len(files)

        automatic_user = User.objects.get_default()
        group, group_created = Group.objects.get_or_create(
            label=group_name, type_string=BASISGROUP_TYPE, user=automatic_user)

        if group.user.email != automatic_user.email:
            raise UniquenessError('There is already a BasisFamily group with name {}'
                                  ', but it belongs to user {}, therefore you '
                                  'cannot modify it'.format(group_name, group.user.email))

        # Always update description, even if the group already existed
        group.description = group_description

        # NOTE: GROUP SAVED ONLY AFTER CHECKS OF UNICITY

        basis_and_created = _retrieve_basis_sets(files, stop_if_existing)
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
            duplicates = set([x for x in elements_names if elements_names.count(x) > 1])
            duplicates_string = ', '.join(i for i in duplicates)
            raise UniquenessError(('More than one Basis found for the elements: ' '{}').format(duplicates_string))

        # At this point, save the group, if still unstored
        if group_created and not dry_run:
            group.store()

        # save the basis set in the database, and add them to group
        for basisset, created in basis_and_created:
            if created:
                if not dry_run:
                    basisset.store()
                # TODO what happened to aiidalogger?
                # pylint: disable=logging-format-interpolation
                # aiidalogger.debug(
                # "New node {0} created for file {1}".format(
                #     basisset.uuid, basisset.filename))
            else:
                pass
                # pylint: disable=logging-format-interpolation
                # aiidalogger.debug("Reusing node {0} for file {1}".format(
                #     basisset.uuid, basisset.filename))

        # Add elements to the group all together
        if not dry_run:
            group.add_nodes([basis for basis, created in basis_and_created])

        nuploaded = len([_ for _, created in basis_and_created if created])

        return nfiles, nuploaded
