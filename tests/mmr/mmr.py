"""
run with
$ python mmr.py

if everything works OK, root of
10  should be ee943d2cc1a3b3728349c86d6a65a80bd4011f6e58c9c49772b9533ee2d6506d
100 should be 37ff9d8ccc1acb194f8a56b06592bca6381260d6c44abe018795751bea43eddf
"""

import sys

sys.path.append("../../tools/interface/")
import contract_interface

sys.path.append("..")
from config import profiler


def deploy(constructor_arguments=[]):
    contract_path = "./MMR.sol"
    interface = contract_interface.ContractInterface(
        contract_path, backend="geth", constructor_arguments=constructor_arguments
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


size = 10
data = [b"\xaa" * 32] * size

interface = deploy()

result = call(interface, "getAllSubpeaks", function_args=[data])
print(len(result["result"]))
print(result["result"][0].hex()[:3])
print(result["result"][1].hex()[:3])
print(result["gas"])


finalize(interface)
