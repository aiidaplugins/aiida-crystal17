import copy

import jsonschema
from jsonschema import ValidationError as SchemeError

from aiida.common.utils import classproperty
from aiida.common.exceptions import ValidationError
from aiida.common.extendeddicts import AttributeDict
from aiida.orm import Data


class KindData(Data):
    """stores additional data for StructureData Kinds"""
    _data_schema = {
        "$schema": "http://json-schema.org/draft-07/schema",
        "title": "additional kind data",
        "type": "object",
        "required": [
            "kind_names"
        ],
        "additionalProperties": False,
        "properties": {
            "kind_names": {
                "type": "array",
                "minimum": 1,
                "items": {"type": "string"},
                "uniqueItems": True,
            }
        },
        "patternProperties": {
            ".+": {
                "type": "array"
            }
        }

    }

    def __init__(self, **kwargs):
        """Stores the symmetry data for a structure

        - symmetry operations are stored on file (in the style of ArrayData)
        - the rest of the values are stored as attributes in the database

        :param data: the data to set
        """
        data = kwargs.pop('data', None)
        super(KindData, self).__init__(**kwargs)
        if data is not None:
            self.set_data(data)

    @classproperty
    def data_schema(cls):
        return copy.deepcopy(cls._data_schema)

    def _validate(self):
        super(KindData, self)._validate()

        try:
            jsonschema.validate(self.data, self._data_schema)
        except SchemeError as err:
            raise ValidationError(err)

        kinds = self.data["kind_names"]
        for key, value in self.data.items():
            if len(value) != len(kinds):
                raise ValidationError(
                    "'{}' array not the same length as 'kind_names'"
                    "".format(key))

    def set_data(self, data):
        """
        Replace the current data with another one.

        :param data: The dictionary to set.
        """
        from aiida.common.exceptions import ModificationNotAllowed

        # first validate the inputs
        try:
            jsonschema.validate(data, self._data_schema)
        except SchemeError as err:
            raise ValidationError(err)

        kinds = data["kind_names"]
        for key, value in data.items():
            if len(value) != len(kinds):
                raise ValidationError(
                    "'{}' array not the same length as 'kind_names'"
                    "".format(key))

        # store all but the symmetry operations as attributes
        backup_dict = copy.deepcopy(dict(self.attributes))

        try:
            # Clear existing attributes and set the new dictionary
            self._update_attributes(data)
        except ModificationNotAllowed:  # pylint: disable=try-except-raise
            # I re-raise here to avoid to go in the generic 'except' below that
            # would raise the same exception again
            raise
        except Exception:
            # Try to restore the old data
            self.clear_attributes()
            self._update_attributes(backup_dict)
            raise

    def _update_attributes(self, data):
        """
        Update the current attribute with the keys provided in the dictionary.

        :param data: a dictionary with the keys to substitute. It works like
          dict.update(), adding new keys and overwriting existing keys.
        """
        for k, v in data.items():
            self.set_attribute(k, v)

    @property
    def data(self):
        """
        Return the data as an AttributeDict
        """
        data = dict(self.attributes)
        return AttributeDict(data)

    @property
    def kind_dict(self):
        """
        Return an AttributeDict with nested keys <kind_name>.<field> = value
        """
        data = dict(self.attributes)
        kind_names = data.pop("kind_names")
        dct = {k: {} for k in kind_names}
        for key, values in data.items():
            for kind, value in zip(kind_names, values):
                dct[kind][key] = value
        return AttributeDict(dct)

    @property
    def field_dict(self):
        """
        Return an AttributeDict with nested keys <field>.<kind_name> = value
        """
        data = dict(self.attributes)
        kind_names = data.pop("kind_names")
        dct = {}
        for key, values in data.items():
            dct[key] = {}
            for kind, value in zip(kind_names, values):
                dct[key][kind] = value
        return AttributeDict(dct)