import copy
import tempfile

import jsonschema
import numpy as np
from aiida.common.exceptions import ValidationError
from aiida.orm import Data


class StructSettingsData(Data):
    """
    Stores input symmetry and kind specific setting for a structure (as required by CRYSTAL17)

    - symmetry operations are stored on file (in the style of ArrayData)
    - the rest of the values are stored as attributes in the database

    """
    _ops_filename = "operations.npy"
    _data_schema = {
        "$schema":
        "http://json-schema.org/draft-04/schema#",
        "title":
        "CRYSTAL17 structure symmetry settings",
        "type":
        "object",
        "required":
        ["space_group", "crystal_type", "centring_code", "operations"],
        "additionalProperties":
        False,
        "properties": {
            "space_group": {
                "description": "Space group number (international)",
                "type": "integer",
                "minimum": 1,
                "maximum": 230
            },
            "crystal_type": {
                "description": "Space group number (international)",
                "type": "integer",
                "minimum": 1,
                "maximum": 6
            },
            "centring_code": {
                "description": "Space group number (international)",
                "type": "integer",
                "minimum": 1,
                "maximum": 6
            },
            "operations": {
                "description":
                "symmetry operations to use (in the cartesian basis)",
                "type": ["null", "array"],
                "items": {
                    "description":
                    "each item should be a list of [r00,r10,r20,r01,r11,r21,r02,r12,r22,t0,t1,t2]",
                    "type":
                    "array",
                    "minItems":
                    12,
                    "maxItems":
                    12,
                    "items": {
                        "type": "number"
                    }
                }
            },
            "kinds": {
                "description":
                "settings for input properties of each species kind",
                "type":
                "object",
                "additionalProperties":
                False,
                "properties": {
                    "spin_alpha": {
                        "description":
                        "kinds with initial alpha (+1) spin (set by ATOMSPIN)",
                        "type":
                        "array",
                        "items": {
                            "type": "string",
                            "uniqueItems": True
                        }
                    },
                    "spin_beta": {
                        "description":
                        "kinds with initial beta (-1) spin (set by ATOMSPIN)",
                        "type":
                        "array",
                        "items": {
                            "type": "string",
                            "uniqueItems": True
                        }
                    },
                    "fixed": {
                        "description":
                        "kinds with are fixed in position for optimisations (set by FRAGMENT)",
                        "type":
                        "array",
                        "items": {
                            "type": "string",
                            "uniqueItems": True
                        }
                    },
                    "ghosts": {
                        "description":
                        "kinds which will be removed, but their basis set are left (set by GHOSTS)",
                        "type":
                        "array",
                        "items": {
                            "type": "string",
                            "uniqueItems": True
                        }
                    }
                }
            },
        }
    }

    @property
    def data_schema(self):
        return copy.deepcopy(self._data_schema)

    def _validate_against_schema(self, data):

        validator = jsonschema.Draft4Validator

        # by default, only validates lists
        try:
            validator(
                self._data_schema, types={
                    "array": (list, tuple)
                }).validate(data)
        except jsonschema.ValidationError as err:
            raise ValidationError(err)

    def _validate(self):
        super(StructSettingsData, self)._validate()

        fname = self._ops_filename
        if fname not in self.get_folder_list():
            raise ValidationError("operations not set")

        self._validate_against_schema(self.data)

    def set_data(self, data):
        """
        Replace the current data with another one.

        :param data: The dictionary to set.
        """
        from aiida.common.exceptions import ModificationNotAllowed

        # first validate the inputs
        self._validate_against_schema(data)

        # store all but the symmetry operations as attributes
        old_dict = copy.deepcopy(dict(self.iterattrs()))
        attributes_set = False
        try:
            # Delete existing attributes
            self._del_all_attrs()
            # I set the keys
            self._update_attrs(
                {k: v
                 for k, v in data.items() if k != "operations"})
            self._set_attr("num_symops", len(data["operations"]))
            attributes_set = True
        finally:
            if not attributes_set:
                try:
                    # Try to restore the old data
                    self._del_all_attrs()
                    self._update_attrs(old_dict)
                except ModificationNotAllowed:
                    pass

        # store the symmetry operations on file
        self._set_operations(data["operations"])

    def _update_attrs(self, data):
        """
        Update the current attribute with the keys provided in the dictionary.

        :param data: a dictionary with the keys to substitute. It works like
          dict.update(), adding new keys and overwriting existing keys.
        """
        for k, v in data.iteritems():
            self._set_attr(k, v)

    def _set_operations(self, ops):
        fname = self._ops_filename

        if fname in self.get_folder_list():
            self.remove_path(fname)

        with tempfile.NamedTemporaryFile() as f:
            # Store in a temporary file, and then add to the node
            np.save(f, ops)
            f.flush(
            )  # Important to flush here, otherwise the next copy command
            # will just copy an empty file
            super(StructSettingsData, self).add_path(f.name, fname)

    def _get_operations(self):
        fname = self._ops_filename
        if fname not in self.get_folder_list():
            raise KeyError("symmetry operations not set for node pk={}".format(
                self.pk))

        array = np.load(self.get_abs_path(fname))

        return array.tolist()

    @property
    def data(self):
        """
        Return the data
        """
        data = dict(self.iterattrs())
        if "num_symops" in data:
            data.pop("num_symops")
        data["operations"] = self._get_operations()
        return data

    def add_path(self, src_abs, dst_path):
        from aiida.common.exceptions import ModificationNotAllowed

        raise ModificationNotAllowed(
            "Cannot add files or directories to StructSettingsData object")
