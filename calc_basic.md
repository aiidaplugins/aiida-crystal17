---
jupytext:
  formats: ipynb,md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.12
    jupytext_version: 1.6.0
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Basic Calculation

+++

The `crystal17.basic` plugin is the simplest calculation plugin.
It accepts as input:

- a pre-written `main.d12` file and,
- (optionally) a `main.gui` file with geometry,
  to accompany a `main.d12` file containing the `EXTERNAL` keyword.

+++

## Initial Setup

+++

To run a computation, first ensure AiiDA is running:

```{code-cell} ipython3
!verdi status
```

:::{seealso}
AiiDA documentation: {ref}`aiida:intro:get_started`
:::

+++

If `aiida-crystal17` is installed,
the `crystal17.basic` computation should be available:

```{code-cell} ipython3
:tags: [nbreg_compare_output]

!verdi plugin list aiida.calculations crystal17.basic
```

To use the python interface, first ensure a profile is loaded in the python kernel, and import the required modules:

```{code-cell} ipython3
:init_cell: true

from aiida import load_profile
profile = load_profile()
profile.name
```

```{code-cell} ipython3
:init_cell: true

import os
from aiida_crystal17.common import display_json
from aiida_crystal17.tests import open_resource_binary
from aiida.orm import Code
from aiida.engine import run_get_node
from aiida.plugins import DataFactory
```

## Input Creation

+++

:::{seealso}
AiiDA documentation: {ref}`aiida:how-to:run-codes`

[CRYSTAL17 Manual](http://www.crystal.unito.it/Manuals/crystal17.pdf)
:::

+++

An {py:class}`~aiida.orm.nodes.data.code.Code` node should be set up in advance,
to use the `crystal17.basic` calculation plugin,
and call the ``runcry17`` executable
(or ``mock_runcry17`` used here for test purposes).

```{code-cell} ipython3
from aiida_crystal17.tests.utils import get_or_create_local_computer, get_or_create_code
computer = get_or_create_local_computer('work_directory', 'localhost')
code = get_or_create_code('crystal17.basic', computer, 'mock_crystal17')
code.get_full_text_info()
```

An {py:class}`~aiida.orm.nodes.data.singlefile.SinglefileData` node is then set containing the main input file.

```{code-cell} ipython3
SinglefileData = DataFactory('singlefile')
with open_resource_binary('crystal', 'mgo_sto3g_scf', 'INPUT') as handle:
   infile = SinglefileData(file=handle)

with infile.open() as handle:
    print(handle.read())
```

## Setting Up and Running the Calculation

+++

:::{seealso}
AiiDA documentation: {ref}`aiida:topics:processes`
:::

+++

A builder can be obtained from the `Code` node,
which will define all the required input nodes and settings:

```{code-cell} ipython3
builder = code.get_builder()
builder.metadata.options.withmpi = False
builder.metadata.options.resources = {
    "num_machines": 1,
    "num_mpiprocs_per_machine": 1}
builder.input_file = infile
display_json(builder)
```

In order to run the computation,
the builder can be parsed to one of the AiiDA ``run`` (blocking execution) or ``submit`` (non-blocking execution) functions:

```{code-cell} ipython3
result, calcnode = run_get_node(builder)
```

The process can be monitored on the command line:

```{code-cell} ipython3
!verdi process list -a -l 1 -D desc
```

Once the calculation is complete, a ``CalcJobNode`` will be created,
to store the settings and outcome of the computation.
Crucially, if the computation has completed successfully,
the `exit_status` will be **0**.

This can be assessed on the command line or with the python API.

```{code-cell} ipython3
!verdi process show {calcnode.pk}
```

```{code-cell} ipython3
:tags: [nbreg_compare_output]

print(calcnode.is_finished_ok)
print(calcnode.process_state)
print(calcnode.exit_status)
```

If the calculation fails, there are three things that should be checked:

1. The calculation's exit_message
2. The calculation's log messages and scheduler output
3. The `results` output node (if available)

```{code-cell} ipython3
print("Exit Message:", calcnode.exit_message)
from aiida.cmdline.utils.common import get_calcjob_report
print(get_calcjob_report(calcnode))
```

```{code-cell} ipython3
!verdi process report {calcnode.pk}
```

##  Analysis of Outputs

+++

The {py:class}`aiida.tools.visualization.graph.Graph` can be used to visualise the calculations provenance graph:

```{code-cell} ipython3
---
ipub:
  figure:
    caption: '`crystal17.basic` calculation provenance graph.'
---
from aiida.tools.visualization import Graph
graph = Graph(graph_attr={'size': "6,8!", "rankdir": "LR"})
graph.add_node(calcnode)
graph.add_incoming(calcnode, annotate_links="both")
graph.add_outgoing(calcnode, annotate_links="both")
graph.graphviz
```

The `retrieved` `FolderData` output node contains the CRYSTAL17 main output file.

```{code-cell} ipython3
calcnode.outputs.retrieved.list_object_names()
```

The `results` `Dict` output node contains key values extracted from the CRYSTAL17 main output file.

```{code-cell} ipython3
display_json(calcnode.outputs.results.attributes)
```

The `structure` `StructureData` output node contains the final structure,
obtained from the CRYSTAL17 main output file.

```{code-cell} ipython3
---
ipub:
  figure:
    caption: Structure visualisation, using ASE and Matplotlib.
---
%matplotlib inline
import matplotlib.pyplot as plt
from ase.visualize.plot import plot_atoms
atoms = calcnode.outputs.structure.get_ase()
fig, ax = plt.subplots()
plot_atoms(atoms.repeat((4,4,4)),
           ax, radii=0.8, show_unit_cell=True,
           rotation=('45x,0y,0z'));
```

The `symmetry` `SymmetryData` output node contains the symmetry of the final structure,
obtained from the CRYSTAL17 main output file.

```{code-cell} ipython3
print(calcnode.outputs.symmetry.attributes)
calcnode.outputs.symmetry.data.operations
```
