"""a work flow to symmetrise a structure and compute the symmetry operations"""
from aiida.common.exceptions import ValidationError
from aiida.plugins import DataFactory
from aiida.engine import WorkChain, calcfunction
from aiida_crystal17.symmetry import (
    standardize_cell, find_primitive, compute_symmetry_dict)

from aiida.orm import Float
StructureData = DataFactory('structure')
DictData = DataFactory('dict')
SymmetryData = DataFactory('crystal17.symmetry')


@calcfunction
def standard_structure(structure, symprec, angle_tolerance=None):
    return standardize_cell(
        structure, symprec, angle_tolerance,
        to_primitive=False, no_idealize=True)


@calcfunction
def standard_primitive_structure(structure, symprec, angle_tolerance=None):
    return standardize_cell(
        structure, symprec, angle_tolerance,
        to_primitive=True, no_idealize=True)


@calcfunction
def standard_primitive_ideal_structure(structure, symprec, angle_tolerance=None):
    return standardize_cell(
        structure, symprec, angle_tolerance,
        to_primitive=True, no_idealize=False)


@calcfunction
def standard_ideal_structure(structure, symprec, angle_tolerance=None):
    return standardize_cell(
        structure, symprec, angle_tolerance,
        to_primitive=False, no_idealize=False)


@calcfunction
def primitive_structure(structure, symprec, angle_tolerance=None):
    return find_primitive(
        structure, symprec, angle_tolerance)


@calcfunction
def compute_symmetry(structure, symprec, angle_tolerance=None):
    data = compute_symmetry_dict(
        structure, symprec, angle_tolerance)
    return SymmetryData(data=data)


class Symmetrise3DStructure(WorkChain):
    """modify an AiiDa structure instance and compute its symmetry

    Inequivalent atomic sites are dictated by atom kinds
    """

    @classmethod
    def define(cls, spec):
        super(Symmetrise3DStructure, cls).define(spec)
        spec.input("structure", valid_type=StructureData, required=True)
        spec.input("symprec", valid_type=Float, required=True,
                   serializer=lambda x: Float(x),
                   help=("Length tolerance for symmetry finding: "
                         "0.01 is fairly strict and works well for properly refined structures, "
                         "but 0.1 may be required for unrefined structures"))
        spec.input("angle_tolerance", valid_type=Float, required=False,
                   serializer=lambda x: Float(x),
                   help=("Angle tolerance for symmetry finding, "
                         "in the unit of angle degrees"))
        spec.input_namespace("compute", required=False, non_db=True,
                             help="options for computing primitive and standardized structures")
        spec.input("compute.primitive", valid_type=bool, default=False,
                   help="whether to convert the structure to its primitive form")
        spec.input("compute.standardize", valid_type=bool, default=False,
                   help=(
                       "whether to standardize the structure, see"
                       "https://atztogo.github.io/spglib/definition.html#conventions-of-standardized-unit-cell"))
        spec.input("compute.idealize", valid_type=bool, default=False,
                   help=("whether to remove distortions of the unit cell's atomic positions, "
                         "using obtained symmetry operations"))
        spec.outline(cls.validate, cls.compute)
        spec.output("symmetry", valid_type=SymmetryData, required=True)
        spec.output("structure", valid_type=StructureData, required=False)

    def validate(self):
        # only allow 3d structures
        if not all(self.inputs.structure.pbc):
            raise ValidationError(
                "the structure must be 3D (i.e. have all dimensions pbc=True)")

        if not self.inputs.symprec > 0.0:
            raise ValidationError("symprec must be greater than 0.0")

    def compute(self):

        structure = self.inputs.structure
        symprec = self.inputs.symprec
        angtol = self.inputs.get("angle_tolerance", None)

        new_structure = None
        if self.inputs.compute.standardize:
            if self.inputs.compute.primitive and self.inputs.compute.idealize:
                new_structure = standard_primitive_ideal_structure(
                    structure, symprec, angtol)
            elif self.inputs.compute.primitive:
                new_structure = standard_primitive_structure(
                    structure, symprec, angtol)
            elif self.inputs.compute.idealize:
                new_structure = standard_ideal_structure(
                    structure, symprec, angtol)
            else:
                new_structure = standard_structure(
                    structure, symprec, angtol)
        elif self.inputs.compute.idealize:
            raise ValueError("idealize can only be used when standardize=True")
        elif self.inputs.compute.primitive:
            new_structure = primitive_structure(structure, symprec, angtol)

        if new_structure is not None:
            self.out('structure', new_structure)
        else:
            new_structure = structure

        self.out('symmetry', compute_symmetry(new_structure, symprec, angtol))
