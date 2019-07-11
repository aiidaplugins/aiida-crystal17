import copy
from hashlib import md5

import six

from aiida.common import exceptions
from aiida.orm import Data
from aiida.plugins.entry_point import load_entry_point, get_entry_point_names


class EmpiricalPotential(Data):
    """
    Store the empirical potential data
    """
    entry_name = 'gulp.potentials'
    potential_filename = 'potential.pot'

    @classmethod
    def list_pair_styles(cls):
        return get_entry_point_names(cls.entry_name)

    @classmethod
    def load_pair_style(cls, entry_name):
        return load_entry_point(cls.entry_name, entry_name)

    def __init__(self, pair_style, potential_data, **kwargs):
        # pair_style = kwargs.pop('pair_style', None)
        # potential_data = kwargs.pop('data', None)
        additional_data = kwargs.pop('additional', None)
        super(EmpiricalPotential, self).__init__(**kwargs)
        self.set_data(pair_style, potential_data, additional_data)

    def set_data(self, pair_style, potential_data, additional_data=None):
        """
        Store the potential type (ex. Tersoff, EAM, LJ, ..) and data
        """
        if pair_style is None:
            raise ValueError("'pair_style' must be provided")
        if pair_style not in self.list_pair_styles():
            raise ValueError("'pair_style' must be in: {}".format(self.list_pair_styles()))
        potential_writer = self.load_pair_style(pair_style)()

        description = potential_writer.get_description()
        content = potential_writer.create_string(potential_data)

        with self.open(self.potential_filename, 'w') as handle:
            handle.write(six.ensure_text(content))

        dictionary = {
            'pair_style': pair_style,
            'description': description,
            'data': potential_data,
            'input_lines_md5': md5(content.encode("utf-8")).hexdigest()
        }
        if additional_data is not None:
            dictionary["additional"] = additional_data

        dictionary_backup = copy.deepcopy(self.get_dict())

        try:
            # Clear existing attributes and set the new dictionary
            self.clear_attributes()
            self._update_dict(dictionary)
        except exceptions.ModificationNotAllowed:  # pylint: disable=try-except-raise
            # I reraise here to avoid to go in the generic 'except' below that would raise the same exception again
            raise
        except Exception:
            # Try to restore the old data
            self.clear_attributes()
            self._update_dict(dictionary_backup)
            raise

    def _update_dict(self, dictionary):
        """Update the current dictionary with the keys provided in the dictionary.

        .. note:: works exactly as `dict.update()` where new keys are simply added and existing keys are overwritten.

        :param dictionary: a dictionary with the keys to substitute
        """
        for key, value in dictionary.items():
            self.set_attribute(key, value)

    def get_dict(self):
        """Return a dictionary with the parameters currently set.

        :return: dictionary
        """
        return dict(self.attributes)

    def keys(self):
        """Iterator of valid keys stored in the Dict object.

        :return: iterator over the keys of the current dictionary
        """
        for key in self.attributes.keys():
            yield key

    def __getitem__(self, key):
        return self.get_attribute(key)

    @property
    def dict(self):
        """Return an instance of `AttributeManager` that transforms the dictionary into an attribute dict.

        .. note:: this will allow one to do `node.dict.key` as well as `node.dict[key]`.

        :return: an instance of the `AttributeResultManager`.
        """
        from aiida.orm.utils.managers import AttributeManager
        return AttributeManager(self)

    @property
    def pair_style(self):
        return self.get_attribute('pair_style')

    @property
    def input_lines_md5(self):
        return self.get_attribute('input_lines_md5')

    def get_description(self):
        return str(self.pair_style)

    def get_input_lines(self):
        if self.potential_filename not in self.list_object_names():
            raise KeyError("potential file not set for node pk={}".format(
                self.pk))

        with self.open(self.potential_filename, mode='r') as handle:
            lines = handle.read()

        return lines.splitlines()
