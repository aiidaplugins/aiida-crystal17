"""a work flow to symmetrise a structure and compute the symmetry operations"""
from aiida.common.exceptions import ValidationError
from aiida.common.extendeddicts import AttributeDict
from aiida.plugins import DataFactory
from aiida.engine import WorkChain
from aiida_crystal17.parsers.geometry import structure_to_dict, compute_symmetry_3d, SYMMETRY_PROGRAM, SYMMETRY_VERSION, \
    dict_to_structure
from aiida_crystal17.utils import unflatten_dict
from aiida.engine import run_get_node
from aiida_crystal17.validation import validate_with_dict
from aiida_crystal17 import __version__ as VERSION
from jsonextended import edict

StructureData = DataFactory('structure')
DictData = DataFactory('dict')
StructSettingsData = DataFactory('crystal17.structsettings')


class Symmetrise3DStructure(WorkChain):
    """modify an AiiDa structure instance and compute its symmetry, given a settings dictionary

    Symmetry is restricted by atom kinds
    """

    _settings_schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": "CRYSTAL17 structure input settings",
        "description": "Settings for initial manipulation of structures",
        "type": "object",
        "required": [],
        "additionalProperties": False,
        "properties": {
            "symprec": {
                "description":
                "Length tolerance for symmetry finding: "
                "0.01 is fairly strict and works well for properly refined structures, "
                "but 0.1 may be required for unrefined structures",
                "type":
                "number",
                "minimum":
                0,
                "exclusiveMinimum":
                True
            },
            "angletol": {
                "description":
                "Angle tolerance for symmetry finding in the unit of angle degrees, "
                "if null, an optimized routine is used to judge symmetry",
                "type": ["number", "null"],
                "minimum":
                0,
                "exclusiveMinimum":
                True
            },
            "standardize": {
                "description":
                "whether to standardize the structure, see https://atztogo.github.io/spglib/definition.html#conventions-of-standardized-unit-cell",
                "type":
                "boolean"
            },
            "primitive": {
                "description":
                "whether to convert the structure to its (standardized) primitive",
                "type":
                "boolean"
            },
            "idealize": {
                "description":
                "whether to remove distortions of the unit cell's atomic positions, using obtained symmetry operations",
                "type":
                "boolean"
            },
            "kinds": {
                "description":
                "settings for input properties of each species kind",
                "type":
                "object",
                "patternProperties": {
                    ".+": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "uniqueItems": True
                        }
                    }
                }
            }
        }
    }

    _settings_defaults = {
        "symprec": 0.01,
        "angletol": None,
        "standardize": True,
        "primitive": True,
        "idealize": False
    }

    @classmethod
    def define(cls, spec):
        super(Symmetrise3DStructure, cls).define(spec)
        spec.input("structure", valid_type=StructureData)
        spec.input("settings", valid_type=DictData, required=False)
        spec.outline(cls.validate, cls.compute)
        spec.output("output_structure", valid_type=StructureData)
        spec.output("output_settings", valid_type=StructSettingsData)

    def validate(self):
        # only allow 3d structures
        if not all(self.inputs.structure.pbc):
            raise ValidationError(
                "the structure must be 3D (i.e. have all dimensions pbc=True)")

        settings_dict = self.inputs.settings.get_dict(
        ) if "settings" in self.inputs else {}
        settings_dict = edict.merge([self._settings_defaults, settings_dict],
                                    overwrite=True)

        validate_with_dict(settings_dict, self._settings_schema)

        self.ctx.settings = AttributeDict(settings_dict)

        self.ctx.structdict = structure_to_dict(self.inputs.structure)

    def compute(self):

        structdict, symmdata = compute_symmetry_3d(
            self.ctx.structdict, self.ctx.settings.standardize,
            self.ctx.settings.primitive, self.ctx.settings.idealize,
            self.ctx.settings.symprec, self.ctx.settings.idealize)

        if "kinds" in self.ctx.settings:
            symmdata["kinds"] = self.ctx.settings.kinds

        symmdata["symmetry_program"] = SYMMETRY_PROGRAM
        symmdata["symmetry_version"] = SYMMETRY_VERSION
        symmdata["computation_class"] = self.__class__.__name__
        symmdata["computation_version"] = VERSION

        self.out('output_settings', StructSettingsData(data=symmdata))
        self.out('output_structure', dict_to_structure(structdict))


def run_symmetrise_3d_structure(structure, settings=None):
    """run the Symmetrise3DStructure workchain and return the structure and settings data nodes,
    for inputting into ``crystal17.main`` calculation

    :param structure: StructureData
    :param settings: dict or DictData
    :return: (StructureData, StructSettingsData)
    """
    if isinstance(settings, dict):
        settings = unflatten_dict(settings)
        settings = DictData(dict=settings)
    inputs_dict = {"structure": structure}
    if settings:
        inputs_dict["settings"] = settings
    node = run_get_node(Symmetrise3DStructure, inputs_dict)

    return node.out.output_structure, node.out.output_settings
