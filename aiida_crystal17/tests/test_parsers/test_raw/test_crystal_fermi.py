from aiida_crystal17.parsers.raw.newk_output import read_newk_content
from aiida_crystal17.tests import open_resource_text


def test_read_newk_out_file(data_regression):

    with open_resource_text('doss', 'cubic_rocksalt_orbitals', 'cubic-rocksalt_2x1_pdos.doss.out') as handle:
        data = read_newk_content(handle, 'dummy_parser_class')

    data = {k: round(i, 7) if isinstance(i, float) else i for k, i in data.items()}

    data_regression.check(data)
