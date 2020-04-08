"""
run with
$ python consistency.py
"""

import sys

sys.path.append("../../tools/interface/")
import contract_interface

sys.path.append("..")
from config import profiler

CONTR_DIR = "../../contracts/"
LIB_DIR = CONTR_DIR + "lib/"


def deploy(
    contract={"path": LIB_DIR + "Merkle.sol", "ctor": [1]},
    libraries=[
        LIB_DIR + "Math.sol",
        LIB_DIR + "Arrays.sol",
    ],
    backend="ganache",
):
    """
    Deploys a contract with a name and returns the interface
    """

    interface = contract_interface.ContractInterface(
        contract, libraries=libraries, backend=backend,
    )
    return interface


def print_debug_events(contract, receipt):
    """
    Prints 'debug' events
    """

    try:
        debug_events = contract.events.debug().processReceipt(receipt)
    except Exception:
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


def call(interface, function_name, function_args=[]):
    """
    Runs the output of a function
    """

    contract = interface.get_contract()
    from_address = interface.w3.eth.accounts[0]
    function = contract.get_function_by_name(function_name)(*function_args)
    res = function.call({"from": from_address})
    tx_hash = function.transact({"from": from_address})
    receipt = interface.w3.eth.waitForTransactionReceipt(tx_hash)
    interface.run_gas_profiler(profiler, tx_hash, function_name)
    print_debug_events(contract, receipt)
    return {"result": res, "gas": receipt["gasUsed"]}
