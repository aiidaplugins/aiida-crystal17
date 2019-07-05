import datetime
import json


def with_dbenv(func):
    def wrapper(*args, **kwargs):
        from aiida import load_profile
        load_profile()
        return func(*args, **kwargs)
    return wrapper


@with_dbenv
def get_data_plugin(name):
    from aiida.plugins import DataFactory
    return DataFactory(name)


@with_dbenv
def load_node(identifier=None, pk=None, uuid=None, **kwargs):
    from aiida.orm import load_node
    return load_node(identifier=identifier, pk=pk, uuid=uuid, **kwargs)


def get_calc_log(calcnode):
    """get a formatted string of the calculation log"""
    from aiida.backends import get_log_messages

    def json_default(o):
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()
        return None

    log_string = (
        "- Calc State:\n{0}\n"
        "- Scheduler Out:\n{1}\n"
        "- Scheduler Err:\n{2}\n"
        "- Log:\n{3}".format(
            calcnode.get_state(), calcnode.get_scheduler_output(),
            calcnode.get_scheduler_error(),
            json.dumps(
                get_log_messages(calcnode), default=json_default, indent=2)))
    return log_string
