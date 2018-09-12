import copy
import tempfile

import numpy as np
from aiida.common.exceptions import ValidationError
from aiida.common.extendeddicts import AttributeDict
from aiida.common.utils import classproperty
from aiida.orm import Data
from aiida_crystal17.parsers.geometry import CRYSTAL_TYPE_MAP, CENTERING_CODE_MAP
from aiida_crystal17.validation import validate_with_dict
from jsonschema import ValidationError as SchemeError


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
            "symmetry_program": {
                "description": "the program used to generate the symmetry",
                "type": "string"
            },
            "symmetry_version": {
                "description":
                "the version of the program used to generate the symmetry",
                "type":
                "string"
            },
            "computation_class": {
                "description": "the class used to compute the settings",
                "type": "string"
            },
            "computation_version": {
                "description":
                "the version of the class used to compute the settings",
                "type":
                "string"
            },
            "space_group": {
                "description": "Space group number (international)",
                "type": "integer",
                "minimum": 1,
                "maximum": 230
            },
            "crystal_type": {
                "description": "The crystal type, as designated by CRYSTAL17",
                "type": "integer",
                "minimum": 1,
                "maximum": 6
            },
            "centring_code": {
                "description": "The crystal type, as designated by CRYSTAL17",
                "type": "integer",
                "minimum": 1,
                "maximum": 6
            },
            "operations": {
                "description":
                "symmetry operations to use (in the fractional basis)",
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
                        "type": "number",
                        "minimum": -1,
                        "maximum": 1
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

    @classproperty
    def data_schema(cls):
        return copy.deepcopy(cls._data_schema)

    def _validate(self):
        super(StructSettingsData, self)._validate()

        fname = self._ops_filename
        if fname not in self.get_folder_list():
            raise ValidationError("operations not set")

        try:
            validate_with_dict(self.data, self._data_schema)
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
            validate_with_dict(data, self._data_schema)
        except SchemeError as err:
            raise ValidationError(err)

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
        Return the data as an AttributeDict
        """
        data = dict(self.iterattrs())
        if "num_symops" in data:
            data.pop("num_symops")
        data["operations"] = self._get_operations()
        return AttributeDict(data)

    @property
    def num_symops(self):
        return self.get_attr("num_symops", None)

    @property
    def space_group(self):
        return self.get_attr("space_group", None)

    @property
    def crystal_system(self):
        """get the string version of the crystal system (e.g. 'triclinic')"""
        ctype = self.get_attr('crystal_type')
        return CRYSTAL_TYPE_MAP[ctype]

    @property
    def crystallographic_transform(self):
        """get the primitive to crystallographic transformation matrix"""
        ctype = self.get_attr('centring_code')
        return CENTERING_CODE_MAP[ctype]

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
