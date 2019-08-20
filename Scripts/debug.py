import inspect
from config import Config


def trace_begin(irods, args):
    if Config.Debug.ENABLE_TRACE:
        irods.write_log("TRACE Irods.{}({})".format(inspect.currentframe().f_back.f_code.co_name, args))


def trace_end(irods, out=None):
    if Config.Debug.ENABLE_TRACE:
        irods.write_log("TRACE Irods.{}() => {}".format(
            inspect.currentframe().f_back.f_code.co_name,
            out
        ))
    return out
