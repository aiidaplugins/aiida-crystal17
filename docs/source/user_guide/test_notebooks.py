"""Test documentation notebooks."""
import io
import os
import logging
import subprocess

import pytest

logger = logging.getLogger(__name__)


@pytest.mark.cry17_doc_notebooks
@pytest.mark.parametrize(
    'filename',
    ('calc_basic.ipynb', 'calc_main.ipynb', 'calc_main_immigrant.ipynb', 'calc_gulp.ipynb', 'workflow_base.ipynb'))
def test_notebook(db_test_app, filename, nb_regression):
    """Execute Jupyter Notebook, using a clean AiiDA database/profile, and test its output is as expected."""
    from aiida.cmdline.utils.common import get_env_with_venv_bin

    # This environmental variable propagates in the jupyter kernel,
    # so that the test aiida database/profile is used.
    os.environ['AIIDA_PATH'] = db_test_app.environment.config_dir

    # We don't actually need to start a daemon, because ``aiida.engine.run`` creates its own.
    # However, for `verdi status` and `verdi process list`, we then get warning messages.
    curr_env = get_env_with_venv_bin()
    output = subprocess.check_output(['verdi', 'daemon', 'start'], env=curr_env, stderr=subprocess.STDOUT)
    logger.info(output)

    try:
        source_dir = os.path.abspath(os.path.dirname(__file__))
        with io.open(os.path.join(source_dir, filename), 'r+') as handle:
            nb_regression.check(handle, compare_all=False)
    finally:
        output = subprocess.check_output(['verdi', 'daemon', 'stop'], env=curr_env, stderr=subprocess.STDOUT)
        logger.info(output)
