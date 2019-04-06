import copy
import tempfile

import jsonschema
from jsonschema import ValidationError as SchemeError
import numpy as np

from aiida.common.utils import classproperty
from aiida.common.exceptions import ValidationError
from aiida.common.extendeddicts import AttributeDict
from aiida.orm import Data


class SymmetryData(Data):
    """
    Stores data regarding the symmetry of a structure

    - symmetry operations are stored on file (in the style of ArrayData)
    - the rest of the values (and the number of symmetry operators)
      are stored as attributes in the database

    """
    _data_schema = {
        "$schema": "http://json-schema.org/draft-07/schema",
        "title": "structure symmetry settings",
        "type": "object",
        "required": [
            "hall_number",
            "operations",
            "basis"
        ],
        "additionalProperties": True,
        "properties": {
            "hall_number": {
                "description": "Hall number defining the symmetry group",
                "type": ["null", "integer"],
                "minimum": 1,
                "maximum": 530,
            },
            "operations": {
                "description": "symmetry operations, should at least include the unity operation",
                "type": "array",
                "minItems": 1,
                "items": {
                    "description": "each item should be a list of [r00,r10,r20,r01,r11,r21,r02,r12,r22,t0,t1,t2]",
                    "type": "array",
                    "minItems": 12,
                    "maxItems": 12,
                    "items": {
                        "type": "number"
                    }
                },
                "uniqueItems": True
            },
            "basis": {
                "description": "whether the symmetry operations are fractional or cartesian",
                "type": "string",
                "enum": ["fractional", "cartesian"]
            },
            "computation": {
                "description": "details of the computation",
                "type": "object"
            }
        }
    }
    _ops_filename = "operations.npy"

    def __init__(self, **kwargs):
        """Stores the symmetry data for a structure

        - symmetry operations are stored on file (in the style of ArrayData)
        - the rest of the values are stored as attributes in the database

        :param data: the data to set
        """
        data = kwargs.pop('data', None)
        super(SymmetryData, self).__init__(**kwargs)
        if data is not None:
            self.set_data(data)

    @classproperty
    def data_schema(cls):
        return copy.deepcopy(cls._data_schema)

    def _validate(self):
        super(SymmetryData, self)._validate()

        fname = self._ops_filename
        if fname not in self.list_object_names():
            raise ValidationError("operations not set")

        try:
            jsonschema.validate(self.data, self._data_schema)
        except SchemeError as err:
            raise ValidationError(err)

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

        # store all but the symmetry operations as attributes
        backup_dict = copy.deepcopy(dict(self.attributes))

        try:
            # Clear existing attributes and set the new dictionary
            self._update_attributes(
                {k: v
                 for k, v in data.items() if k != "operations"})
            self.set_attribute("num_symops", len(data["operations"]))
        except ModificationNotAllowed:  # pylint: disable=try-except-raise
            # I re-raise here to avoid to go in the generic 'except' below that
            # would raise the same exception again
            raise
        except Exception:
            # Try to restore the old data
            self.clear_attributes()
            self._update_attributes(backup_dict)
            raise

        # store the symmetry operations on file
        self._set_operations(data["operations"])

    def _update_attributes(self, data):
        """
        Update the current attribute with the keys provided in the dictionary.

        :param data: a dictionary with the keys to substitute. It works like
          dict.update(), adding new keys and overwriting existing keys.
        """
        for k, v in data.items():
            self.set_attribute(k, v)

    def _set_operations(self, ops):
        fname = self._ops_filename

        if fname in self.list_object_names():
            self.delete_object(fname)

        with tempfile.NamedTemporaryFile() as handle:
            # Store in a temporary file, and then add to the node
            np.save(handle, ops)

            # Flush and rewind the handle, otherwise the command to store it in
            # the repo will write an empty file
            handle.flush()
            handle.seek(0)

            # Write the numpy array to the repository,
            # keeping the byte representation
            self.put_object_from_filelike(handle, fname,
                                          mode='wb', encoding=None)

    def _get_operations(self):
        filename = self._ops_filename
        if filename not in self.list_object_names():
            raise KeyError("symmetry operations not set for node pk={}".format(
                self.pk))

        # Open a handle in binary read mode as the arrays are written
        # as binary files as well
        with self.open(filename, mode='rb') as handle:
            array = np.load(handle)

        return array.tolist()

    @property
    def data(self):
        """
        Return the data as an AttributeDict
        """
        data = dict(self.attributes)
        if "num_symops" in data:
            data.pop("num_symops")
        data["operations"] = self._get_operations()
        return AttributeDict(data)

    def get_dict(self):
        """get dictionary of data"""
        data = dict(self.attributes)
        if "num_symops" in data:
            data.pop("num_symops")
        data["operations"] = self._get_operations()
        return data

    @property
    def num_symops(self):
        return self.get_attribute("num_symops", None)

    @property
    def hall_number(self):
        return self.get_attribute("hall_number", None)

    def add_path(self, src_abs, dst_path):
        from aiida.common.exceptions import ModificationNotAllowed

        raise ModificationNotAllowed(
            "Cannot add files or directories to StructSettingsData object")

    def compare_operations(self, ops, decimal=5):
        """compare operations against stored ones

        :param ops: list of (flattened) symmetry operations
        :param decimal: number of decimal points to round values to
        :returns: dict of differences
        """
        ops_orig = self._get_operations()

        # create a set for each
        ops_orig = set(
            [tuple([round(i, decimal) for i in op]) for op in ops_orig])
        ops_new = set([tuple([round(i, decimal) for i in op]) for op in ops])

        differences = {}
        if ops_orig.difference(ops_new):
            differences["missing"] = ops_orig.difference(ops_new)
        if ops_new.difference(ops_orig):
            differences["additional"] = ops_new.difference(ops_orig)

        return differences
