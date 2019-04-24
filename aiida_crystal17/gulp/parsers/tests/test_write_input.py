from aiida_crystal17.gulp.parsers.write_input import (
    InputCreationBase, InputCreationSingle, InputCreationOpt)


def test_initialisation():
    InputCreationBase()
    InputCreationSingle()
    InputCreationOpt()


def test_create_potential_lines():
    icreate = InputCreationBase()
    lines = icreate.create_potential_lines("lj", {
        "atoms": {
            "H": {
                "He": {
                    "A": 1.0,
                    "B": 2.0,
                    "rmax": 12.0
                }
            }
        }
    })

    expected = [
        "lennard 12 6",
        "H He 1.0 2.0 12.0"
    ]
    assert lines == expected


def test_create_geometry_basic():
    icreate = InputCreationBase()
    structure_data = {
        "lattice": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        "ccoords": [[0, 0, 0], [0.5, 0.5, 0.5]],
        "atomic_numbers": [1, 2],
        "pbc": [True, True, True]
    }
    lines = icreate.create_geometry_lines(structure_data)
    expected = [
        "name main-geometry",
        "vectors",
        "1.000000 0.000000 0.000000",
        "0.000000 1.000000 0.000000",
        "0.000000 0.000000 1.000000",
        "cartesian",
        "H core 0.000000 0.000000 0.000000",
        "He core 0.500000 0.500000 0.500000"
    ]
    assert lines == expected


def test_create_geometry_with_symm():
    icreate = InputCreationBase()
    structure_data = {
        "lattice": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        "ccoords": [[0, 0, 0], [0.5, 0.5, 0.5]],
        "atomic_numbers": [1, 2],
        "pbc": [True, True, True]
    }
    symmetry_data = {
        "hall_number": None,
        "basis": "fractional",
        "operations": [
            [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
            [1, 1, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0]
        ]
    }
    lines = icreate.create_geometry_lines(structure_data, symmetry_data)
    expected = [
        "name main-geometry",
        "vectors",
        "1.000000 0.000000 0.000000",
        "0.000000 1.000000 0.000000",
        "0.000000 0.000000 1.000000",
        "cartesian",
        "H core 0.000000 0.000000 0.000000",
        "He core 0.500000 0.500000 0.500000",
        "symmetry_operator",
        " 1.00000  0.00000  0.00000  0.00000",
        " 1.00000  1.00000  0.00000  0.00000",
        " 0.00000  1.00000  1.00000  0.00000"
    ]
    assert lines == expected


def test_create_content_basic():
    icreate = InputCreationBase(outputs={"cif": "output.cif"})
    structure_data = {
        "lattice": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        "ccoords": [[0, 0, 0], [0.5, 0.5, 0.5]],
        "atomic_numbers": [1, 2],
        "pbc": [True, True, True]
    }
    potential_data = {
        "pair_style": "lj",
        "data": {
            "atoms": {
                "H": {
                    "He": {
                        "A": 1.0,
                        "B": 2.0,
                        "rmax": 12.0
                    }
                }
            }
        }
    }
    symmetry_data = {
        "hall_number": None,
        "basis": "fractional",
        "operations": [
            [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
            [1, 1, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0]
        ]
    }
    lines = icreate.create_content(
        structure_data, potential_data,
        symmetry=symmetry_data, parameters={"title": "My Title"})
    expected = [
        "verb",
        "",
        "title",
        "My Title",
        "end",
        "",
        "# Geometry",
        "name main-geometry",
        "vectors",
        "1.000000 0.000000 0.000000",
        "0.000000 1.000000 0.000000",
        "0.000000 0.000000 1.000000",
        "cartesian",
        "H core 0.000000 0.000000 0.000000",
        "He core 0.500000 0.500000 0.500000",
        "symmetry_operator",
        " 1.00000  0.00000  0.00000  0.00000",
        " 1.00000  1.00000  0.00000  0.00000",
        " 0.00000  1.00000  1.00000  0.00000",
        "",
        "# Force Field",
        "lennard 12 6",
        "H He 1.0 2.0 12.0",
        "",
        "# External Outputs",
        "output cif output.cif",
        ""
    ]
    assert lines == expected


def test_create_content_single():
    icreate = InputCreationSingle()
    structure_data = {
        "lattice": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        "ccoords": [[0, 0, 0], [0.5, 0.5, 0.5]],
        "atomic_numbers": [1, 2],
        "pbc": [True, True, True]
    }
    potential_data = {
        "pair_style": "lj",
        "data": {
            "atoms": {
                "H": {
                    "He": {
                        "A": 1.0,
                        "B": 2.0,
                        "rmax": 12.0
                    }
                }
            }
        }
    }
    lines = icreate.create_content(structure_data, potential_data)
    expected = [
        "verb",
        "",
        "# Geometry",
        "name main-geometry",
        "vectors",
        "1.000000 0.000000 0.000000",
        "0.000000 1.000000 0.000000",
        "0.000000 0.000000 1.000000",
        "cartesian",
        "H core 0.000000 0.000000 0.000000",
        "He core 0.500000 0.500000 0.500000",
        "",
        "# Force Field",
        "lennard 12 6",
        "H He 1.0 2.0 12.0",
        ""
    ]
    assert lines == expected


def test_create_content_opt():
    icreate = InputCreationOpt()
    structure_data = {
        "lattice": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        "ccoords": [[0, 0, 0], [0.5, 0.5, 0.5]],
        "atomic_numbers": [1, 2],
        "pbc": [True, True, True]
    }
    potential_data = {
        "pair_style": "lj",
        "data": {
            "atoms": {
                "H": {
                    "He": {
                        "A": 1.0,
                        "B": 2.0,
                        "rmax": 12.0
                    }
                }
            }
        }
    }
    parameters = {
        "minimize": {"style": "cg", "max_iterations": 100},
        "relax": {"type": "conp"}}
    lines = icreate.create_content(
        structure_data, potential_data, parameters=parameters)
    expected = [
        "optimise verb conp cg",
        "",
        "# Geometry",
        "name main-geometry",
        "vectors",
        "1.000000 0.000000 0.000000",
        "0.000000 1.000000 0.000000",
        "0.000000 0.000000 1.000000",
        "cartesian",
        "H core 0.000000 0.000000 0.000000",
        "He core 0.500000 0.500000 0.500000",
        "",
        "# Force Field",
        "lennard 12 6",
        "H He 1.0 2.0 12.0",
        "",
        "# Other Options",
        "maxcyc opt 100",
        ""
    ]
    assert lines == expected
