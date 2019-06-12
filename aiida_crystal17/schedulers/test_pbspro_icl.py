import uuid

from aiida_crystal17.schedulers.pbspro_icl import PbsproICLScheduler
from aiida.schedulers.datastructures import JobTemplate
from aiida.common.datastructures import CodeInfo, CodeRunMode


def test_submit_script():
    scheduler = PbsproICLScheduler()

    job_tmpl = JobTemplate()
    job_tmpl.uuid = str(uuid.uuid4())
    job_tmpl.shebang = '#!/bin/bash -l'
    job_tmpl.job_resource = scheduler.create_job_resource(
        num_machines=1, num_cores_per_machine=32)
    job_tmpl.max_memory_kb = 2000
    job_tmpl.max_wallclock_seconds = 24.5 * 3600
    job_tmpl.queue_name = "myqueue"
    code_info = CodeInfo()
    code_info.cmdline_params = ["mpirun", "-np", "23", "pw.x", "-npool", "1"]
    code_info.stdin_name = 'aiida.in'
    job_tmpl.codes_info = [code_info]
    job_tmpl.codes_run_mode = CodeRunMode.SERIAL

    submit_script_text = scheduler.get_submit_script(job_tmpl).splitlines()

    assert "#PBS -l select=1:ncpus=32:mem=2gb" in submit_script_text
    assert '#PBS -l walltime=24:30:00' in submit_script_text
    assert '#PBS -q myqueue' in submit_script_text
