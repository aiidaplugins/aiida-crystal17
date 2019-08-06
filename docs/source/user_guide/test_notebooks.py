"""Test documentation notebooks.

Could use https://github.com/computationalmodelling/nbval,
but this treats the whole notebook file as the test file, so doesn't allow
programmatic access to the file before/after testing.
"""
import copy
import difflib
import io
import os

import pytest
import ruamel.yaml as yaml


def nb_to_dict(d, strip_keys=()):
    """Recursively convert dict-like NotebookNode to dict."""
    from nbformat import NotebookNode
    if isinstance(d, (NotebookNode, dict)):
        return {k: nb_to_dict(v, strip_keys) for k, v in d.items() if k not in strip_keys}
    elif isinstance(d, (tuple, list)):
        return [nb_to_dict(i, strip_keys) for i in d]
    else:
        return d


def compare_text(obtained, expected):
    """Compare two pieces of text.

    :param str obtained: obtained text.
    :param str expected: expected text.

    """
    __tracebackhide__ = True

    obtained_lines = obtained.splitlines()
    expected_lines = expected.splitlines()

    if obtained_lines != expected_lines:
        diff_lines = list(difflib.unified_diff(expected_lines, obtained_lines, lineterm=''))
        if len(diff_lines) <= 500:
            return '\n'.join(diff_lines)
        else:
            return 'Texts are different, but diff is too big to show ({} lines)'.format(len(diff_lines))
    return None


def compare_nbs(obtained, expected):
    """Compare two section of a Jupyter Notebook."""
    return compare_text(yaml.safe_dump(nb_to_dict(obtained, ['execution_count'])),
                        yaml.safe_dump(nb_to_dict(expected, ['execution_count'])))


@pytest.mark.cry17_doc_notebooks
@pytest.mark.parametrize(
    'filename',
    ('calc_basic.ipynb', 'calc_main.ipynb', 'calc_main_immigrant.ipynb', 'calc_gulp.ipynb', 'workflow_base.ipynb'))
def test_notebook(db_test_app, filename, pytestconfig):
    """Run documentation workbooks, and test their output is as expected.

    TODO this test runs the notebooks, using the externally configured aiida profile,
    but we actually want it to use the profile supplied by db_test_app
    """
    from nbconvert.preprocessors import ExecutePreprocessor
    import nbformat
    from nbformat import NotebookNode

    source_dir = os.path.abspath(os.path.dirname(__file__))
    with io.open(os.path.join(source_dir, filename)) as handle:
        notebook = nbformat.read(handle, as_version=4)  # type: NotebookNode

    proc = ExecutePreprocessor(timeout=120, allow_errors=True)
    resources = {
        'metadata': {
            'path': db_test_app.work_directory
        }
    }  # path specifies the directroy the kernel will run in
    new_notebook, new_resources = proc.preprocess(copy.deepcopy(notebook), resources)

    if pytestconfig.getoption('cry17_regen_nbs', False):
        with io.open(os.path.join(source_dir, filename), mode='w') as handle:
            nbformat.write(new_notebook, handle)

    errors = {}
    for i, cell in enumerate(new_notebook.cells):
        key = 'Cell_{}'.format(i + 1)
        default = {'_source': cell.source}

        if 'pytest_compare' in cell.metadata.get('tags', []):
            # directly compare the outputs
            diff = compare_nbs(cell.outputs, notebook.cells[i].outputs)
            if diff:
                errors.setdefault(key, default)['comparison'] = diff
            continue

        exception_found = False
        if 'outputs' in cell:
            # check the output does not contain any exceptions
            for output in cell['outputs']:
                if output.output_type == 'error':
                    if 'pytest_exception' in cell.metadata.get('tags', []):
                        exception_found = True
                    else:
                        errors.setdefault(key, default)['exception'] = output

        if 'pytest_exception' in cell.metadata.get('tags', []) and not exception_found:
            errors.setdefault(key, default)['no_exception'] = True

    if errors:
        errors = nb_to_dict(errors)
        yaml.scalarstring.walk_tree(errors)  # converts all strings that have a newline in them to block style
        raise AssertionError('\n{}'.format(yaml.round_trip_dump(errors, default_flow_style=False)))


def run_in_parent_dir(notebook, proc, cwd):
    # I tried this (adapted from nbval) but it doesn't find the test profile
    import ipykernel.kernelspec
    from jupyter_client.manager import KernelManager
    from jupyter_client.kernelspec import KernelSpecManager

    class CustomKernelSpecManager(KernelSpecManager):
        """Kernel manager that also allows for python kernel in parent environment."""

        def get_kernel_spec(self, kernel_name):
            """Return a `KernelSpec` instance for kernel in parent environment."""
            if kernel_name == 'USE_PARENT':
                return self.kernel_spec_class(resource_dir=ipykernel.kernelspec.RESOURCES,
                                              **ipykernel.kernelspec.get_kernel_dict())
            else:
                return super(CustomKernelSpecManager, self).get_kernel_spec(kernel_name)

    km = KernelManager(kernel_name='USE_PARENT', kernel_spec_manager=CustomKernelSpecManager())
    kc = km.start_kernel(stderr=open(os.devnull, 'w'), cwd=cwd)
    kc = km.client()

    try:
        new_notebook, resources = proc.preprocess(notebook, {}, km=km)
    except RuntimeError:
        kc.stop_channels()
        km.shutdown_kernel()
        raise

    kc.stop_channels()
    km.shutdown_kernel()

    return new_notebook, resources
