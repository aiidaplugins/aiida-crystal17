def parse_pbs_stderr(file_handle):
    """look for errors originating from PBS pro std error messages"""
    for line in file_handle.readlines():
        if "PBS: job killed: mem" in line:
            return "ERROR_OUT_OF_MEMORY"
        if "PBS: job killed: vmem" in line:
            return "ERROR_OUT_OF_VMEMORY"
        if "PBS: job killed: walltime" in line:
            return "ERROR_OUT_OF_WALLTIME"

    return None
