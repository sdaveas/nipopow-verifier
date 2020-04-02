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


def call(interface, function_name, function_args=[]):
    """
    Runs a function with function_args
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


def test_log2Ceiling(data):
    interface = deploy()

    result = call(interface, "log2Ceiling", function_args=[data])
    res = result["result"]
    print(res)
    print(result["gas"])

    finalize(interface)


def test_closestPow2(data):
    interface = deploy()
    result = call(interface, "closestPow2", function_args=[data])
    print(result["result"])
    print(result["gas"])

    finalize(interface)


def test_merkle_tree_hash_rec():
    size = 100
    data = []
    for i in range(size):
        data.append(int(i).to_bytes(32, "big"))

    interface = deploy()

    result = call(interface, "merkleTreeHashRec", function_args=[data])
    res = result["result"]
    print(res.hex())
    print(result["gas"])

    finalize(interface)
