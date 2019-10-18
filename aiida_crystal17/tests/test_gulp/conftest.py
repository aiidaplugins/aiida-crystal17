import pytest


@pytest.fixture(scope='function')
def pyrite_potential_lj():
    from aiida.plugins import DataFactory
    from aiida_crystal17.gulp.potentials.common import INDEX_SEP
    potential_cls = DataFactory('gulp.potential')
    return potential_cls(
        'lj', {
            'species': ['Fe core', 'S core'],
            '2body': {
                '0' + INDEX_SEP + '0': {
                    'lj_A': 1.0,
                    'lj_B': 1.0,
                    'lj_rmax': 12.0
                },
                '0' + INDEX_SEP + '1': {
                    'lj_A': 1.0,
                    'lj_B': 1.0,
                    'lj_rmax': 12.0
                },
                '1' + INDEX_SEP + '1': {
                    'lj_A': 1.0,
                    'lj_B': 1.0,
                    'lj_rmax': 12.0
                }
            }
        })


@pytest.fixture(scope='function')
def pyrite_potential_reaxff():
    from aiida.plugins import DataFactory
    from aiida_crystal17.tests import read_resource_text
    from aiida_crystal17.gulp.potentials.common import filter_by_species
    from aiida_crystal17.gulp.potentials.raw_reaxff import read_lammps_format
    data = read_lammps_format(read_resource_text('gulp', 'potentials', 'FeCrOSCH.reaxff').splitlines())
    data = filter_by_species(data, ['Fe core', 'S core'])
    return DataFactory('gulp.potential')('reaxff', data)


@pytest.fixture(scope='function')
def pyrite_potential_reaxff_lowtol():
    from aiida.plugins import DataFactory
    from aiida_crystal17.tests import read_resource_text
    from aiida_crystal17.gulp.potentials.common import filter_by_species
    from aiida_crystal17.gulp.potentials.raw_reaxff import read_lammps_format
    data = read_lammps_format(read_resource_text('gulp', 'potentials', 'FeCrOSCH.reaxff').splitlines())
    data = filter_by_species(data, ['Fe core', 'S core'])
    data['global']['torsionprod'] = 0.001
    return DataFactory('gulp.potential')('reaxff', data)
