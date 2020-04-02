"""
run with
$ python consistency.py
"""

import sys

sys.path.append("../../tools/interface/")
import contract_interface

sys.path.append("..")
from config import profiler

import pickle


def export_pkl(data, filename):
    with open(filename, "wb") as f:
        pickle.dump(data, f)


def import_pkl(filename):
    with open(filename, "rb") as f:
        return pickle.load(f)


def deploy(constructor_arguments=[]):
    contract_path = "./consistency.sol"
    interface = contract_interface.ContractInterface(
        contract_path, backend="ganache", constructor_arguments=constructor_arguments
    )
    return interface


def finalize(interface):
    interface.end()


def print_debug_events(contract, receipt):
    try:
        debug_events = contract.events.debug().processReceipt(receipt)
    except Exception as ex:
        debug_events = {}
    if len(debug_events) > 0:
        for e in debug_events:
            log = dict(e)["args"]
            if isinstance(log["value"], bytes):
                value = log["value"].hex()
            else:
                value = log["value"]
            print(log["tag"], "\t", value)
    return debug_events
