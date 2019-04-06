"""a work flow to symmetrise a structure and compute the symmetry operations"""
from aiida.common.exceptions import ValidationError
from aiida.common.extendeddicts import AttributeDict
from aiida.plugins import DataFactory
from aiida.engine import WorkChain
from aiida_crystal17.symmetry import (
    standardize_cell, find_primitive, compute_symmetry_dict)
from aiida_crystal17.validation import validate_with_dict
from jsonextended import edict

StructureData = DataFactory('structure')
DictData = DataFactory('dict')
SymmetryData = DataFactory('crystal17.symmetry')
KindData = DataFactory('crystal17.kinds')


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
                "type": "number",
                "minimum": 0,
                "exclusiveMinimum": True
            },
            "angle_tolerance": {
                "description":
                "Angle tolerance for symmetry finding in the unit of angle degrees, "
                "if null, an optimized routine is used to judge symmetry",
                "type": ["number", "null"],
                "minimum": 0,
                "exclusiveMinimum": True
            },
            "standardize": {
                "description":
                "whether to standardize the structure, "
                "see https://atztogo.github.io/spglib/definition.html#conventions-of-standardized-unit-cell",
                "type": "boolean"
            },
            "primitive": {
                "description":
                "whether to convert the structure to its (standardized) primitive",
                "type": "boolean"
            },
            "idealize": {
                "description":
                "whether to remove distortions of the unit cell's atomic positions, using obtained symmetry operations",
                "type": "boolean"
            }
        }
    }

    _settings_defaults = {
        "symprec": 0.01,
        "angle_tolerance": None,
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
        spec.output("symmetry", valid_type=SymmetryData, required=True)
        spec.output("structure", valid_type=StructureData, required=False)

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

    def compute(self):

        if self.ctx.settings.standardize:
            structure = standardize_cell(
                self.inputs.structure,
                self.ctx.settings.symprec, self.ctx.settings.angle_tolerance,
                to_primitive=self.ctx.settings.primitive,
                no_idealize=not self.ctx.settings.idealize)
            self.out('structure', structure)
        elif self.ctx.settings.primitive:
            structure = find_primitive(
                self.inputs.structure,
                self.ctx.settings.symprec, self.ctx.settings.angle_tolerance
            )
            self.out('structure', structure)
        else:
            structure = self.inputs.structure

        symmdata = compute_symmetry_dict(
            structure,
            self.ctx.settings.symprec, self.ctx.settings.angle_tolerance
        )

        self.out('symmetry', SymmetryData(data=symmdata))


def run_symmetrise_3d_structure(structure, settings=None):
    """run the Symmetrise3DStructure workchain and return the structure and settings data nodes,
    for inputting into ``crystal17.main`` calculation

    :param structure: StructureData
    :param settings: dict or DictData
    :return: (StructureData, StructSettingsData)
    """
    from aiida.engine import run_get_node
    if isinstance(settings, dict):
        settings = unflatten_dict(settings)
        settings = DictData(dict=settings)
    inputs_dict = {"structure": structure}
    if settings:
        inputs_dict["settings"] = settings
    outcome = run_get_node(Symmetrise3DStructure, **inputs_dict)
    outgoing = outcome.node.get_outgoing()

    return (outgoing.get_node_by_label("structure"),
            outgoing.get_node_by_label("settings"))
