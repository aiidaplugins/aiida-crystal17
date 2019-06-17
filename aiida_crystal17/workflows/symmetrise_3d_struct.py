"""a work flow to symmetrise a structure and compute the symmetry operations"""
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
        spec.input("structure", valid_type=StructureData, required=False)
        spec.input("cif", valid_type=DataFactory("cif"), required=False)
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

        spec.outline(
            cls.validate_inputs,
            cls.compute
        )

        spec.output("symmetry", valid_type=SymmetryData, required=True)
        spec.output("structure", valid_type=StructureData, required=False)

        spec.exit_code(300, 'ERROR_INVALID_INPUT_RESOURCES',
                       message='one of either a structure or cif input must be supplied')
        spec.exit_code(301, 'ERROR_NON_3D_STRUCTURE',
                       message='the supplied structure must be 3D (i.e. have all dimensions pbc=True)"')
        spec.exit_code(302, 'ERROR_SYMMETRY_SETTINGS',
                       message='symprec/angle_tolerance must be greater than 0.0')
        spec.exit_code(303, 'ERROR_COMPUTE_OPTIONS',
                       message='idealize can only be used when standardize=True')

    def validate_inputs(self):

        if 'structure' in self.inputs:
            if 'cif' in self.inputs:
                return self.exit_codes.ERROR_INVALID_INPUT_RESOURCES
            self.ctx.structure = self.inputs.structure
        elif 'cif' in self.inputs:
            self.ctx.structure = self.inputs.cif.get_structure(converter="ase")
        else:
            return self.exit_codes.ERROR_INVALID_INPUT_RESOURCES

        if not all(self.ctx.structure.pbc):
            return self.exit_codes.ERROR_NON_3D_STRUCTURE

        if not self.inputs.symprec > 0.0:
            return self.exit_codes.ERROR_SYMMETRY_SETTINGS

        if "angle_tolerance" in self.inputs:
            if not self.inputs.angle_tolerance > 0.0:
                return self.exit_codes.ERROR_SYMMETRY_SETTINGS

        if self.inputs.compute.idealize and not self.inputs.compute.standardize:
            return self.exit_codes.ERROR_COMPUTE_OPTIONS

    def compute(self):

        structure = self.ctx.structure
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
        elif self.inputs.compute.primitive:
            new_structure = primitive_structure(structure, symprec, angtol)

        if new_structure is not None:
            self.out('structure', new_structure)
        else:
            new_structure = structure

        self.out('symmetry', compute_symmetry(new_structure, symprec, angtol))
