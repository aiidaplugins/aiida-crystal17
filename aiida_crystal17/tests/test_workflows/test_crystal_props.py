import os
import sys

from aiida.engine import run_get_node
from aiida.cmdline.utils.common import get_workchain_report  # noqa: F401
from aiida.orm import Dict, RemoteData

from aiida_crystal17.tests import TEST_FILES
from aiida_crystal17.tests.utils import AiidaTestApp, sanitize_calc_info  # noqa: F401

from aiida_crystal17.workflows.crystal_props.cry_doss import CryPropertiesWorkChain
from aiida_crystal17.data.input_params import CryInputParamsData


def test_init_prop_steps(db_test_app, data_regression):
    """ test the workchains initial setup and validation steps """
    if hasattr(CryPropertiesWorkChain, '_spec'):
        # TODO this is required while awaiting fix for aiidateam/aiida-core#3143
        del CryPropertiesWorkChain._spec

    cry_calc = db_test_app.generate_calcjob_node(
        'crystal17.main',
        mark_completed=True,
        remote_path=os.path.join(TEST_FILES, 'crystal', 'mgo_sto3g_scf'),
        input_nodes={
            'parameters': CryInputParamsData(data={
                'title': 'MgO Bulk',
                'scf': {
                    'k_points': (8, 8),
                    'GUESSP': True
                }
            })
        })

    wc_builder = CryPropertiesWorkChain.get_builder()
    wc_builder.test_run = True
    wc_builder.wf_folder = cry_calc.outputs.remote_folder
    wc_builder.doss.code = db_test_app.get_or_create_code('crystal17.doss')
    wc_builder.doss.parameters = Dict(dict={
        'shrink_is': 18,
        'shrink_isp': 36,
        'npoints': 100,
        'band_minimum': -10,
        'band_maximum': 10,
        'band_units': 'eV'
    })
    wc_builder.doss.metadata = db_test_app.get_default_metadata()

    wkchain, step_outcomes, context = db_test_app.generate_context(
        CryPropertiesWorkChain, wc_builder,
        ['check_remote_folder', 'submit_scf_calculation', 'submit_doss_calculation'])

    data_regression.check(context)

    try:
        assert step_outcomes[0] is True
        assert step_outcomes[1] == CryPropertiesWorkChain.exit_codes.END_OF_TEST_RUN
        assert step_outcomes[2] == CryPropertiesWorkChain.exit_codes.END_OF_TEST_RUN
    except Exception:
        sys.stderr.write(get_workchain_report(wkchain, 'REPORT'))
        raise


def test_run_prop_mgo_no_scf(db_test_app, get_structure_and_symm, upload_basis_set_family, data_regression):
    """ test the workchains when a remote folder is supplied that contains the wavefunction file """
    if hasattr(CryPropertiesWorkChain, '_spec'):
        # TODO this is required while awaiting fix for aiidateam/aiida-core#3143
        del CryPropertiesWorkChain._spec

    remote_folder = RemoteData(
        remote_path=os.path.join(TEST_FILES, 'doss', 'mgo_sto3g_scf'), computer=db_test_app.get_or_create_computer())

    wc_builder = CryPropertiesWorkChain.get_builder()
    wc_builder.wf_folder = remote_folder
    wc_builder.doss.code = db_test_app.get_or_create_code('crystal17.doss')
    wc_builder.doss.parameters = Dict(dict={
        'shrink_is': 18,
        'shrink_isp': 36,
        'npoints': 100,
        'band_minimum': -10,
        'band_maximum': 10,
        'band_units': 'eV'
    })
    wc_builder.doss.metadata = db_test_app.get_default_metadata()

    outputs, wc_node = run_get_node(wc_builder)
    sys.stderr.write(get_workchain_report(wc_node, 'REPORT'))

    wk_attributes = wc_node.attributes
    for key in ['job_id', 'last_jobinfo', 'scheduler_lastchecktime', 'version']:
        wk_attributes.pop(key, None)

    data_regression.check({
        'calc_node': wk_attributes,
        'incoming': sorted(wc_node.get_incoming().all_link_labels()),
        'outgoing': sorted(wc_node.get_outgoing().all_link_labels()),
        # "results": outputs["results"].attributes
    })


def test_run_prop_mgo_with_scf(db_test_app, get_structure_and_symm, upload_basis_set_family, data_regression):
    """ test the workchains when a remote folder is supplied that does not contain the wavefunction file """
    if hasattr(CryPropertiesWorkChain, '_spec'):
        # TODO this is required while awaiting fix for aiidateam/aiida-core#3143
        del CryPropertiesWorkChain._spec

    structure, symmetry = get_structure_and_symm('MgO')

    cry_calc = db_test_app.generate_calcjob_node(
        'crystal17.main',
        mark_completed=True,
        remote_path=os.path.join(TEST_FILES, 'crystal', 'mgo_sto3g_scf'),
        input_nodes={
            'parameters': CryInputParamsData(data={
                'title': 'MgO Bulk',
                'scf': {
                    'k_points': (8, 8),
                    'post_scf': ['PPAN']
                }
            }),
            'code': db_test_app.get_or_create_code('crystal17.main'),
            'structure': structure,
            'symmetry': symmetry,
            'basissets': {k: v for k, v in upload_basis_set_family().items() if k in ['Mg', 'O']}
        },
        options=db_test_app.get_default_metadata()['options'])

    wc_builder = CryPropertiesWorkChain.get_builder()
    wc_builder.wf_folder = cry_calc.outputs.remote_folder
    wc_builder.doss.code = db_test_app.get_or_create_code('crystal17.doss')
    wc_builder.doss.parameters = Dict(dict={
        'shrink_is': 18,
        'shrink_isp': 36,
        'npoints': 100,
        'band_minimum': -10,
        'band_maximum': 10,
        'band_units': 'eV'
    })
    wc_builder.doss.metadata = db_test_app.get_default_metadata()
    wc_builder.clean_workdir = True

    outputs, wc_node = run_get_node(wc_builder)
    sys.stderr.write(get_workchain_report(wc_node, 'REPORT'))

    wk_attributes = wc_node.attributes
    for key in ['job_id', 'last_jobinfo', 'scheduler_lastchecktime', 'version']:
        wk_attributes.pop(key, None)

    data_regression.check({
        'calc_node': wk_attributes,
        'incoming': sorted(wc_node.get_incoming().all_link_labels()),
        'outgoing': sorted(wc_node.get_outgoing().all_link_labels()),
        # "results": outputs["results"].attributes
    })
