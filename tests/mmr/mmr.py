"""
run with
$
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


def call(interface, function_name, function_args=[]):
    """
    Runs a function with function_args
    """

    my_contract = interface.get_contract()
    from_address = interface.w3.eth.accounts[0]
    function = my_contract.get_function_by_name(function_name)(*function_args)
    res = function.call({"from": from_address})
    tx_hash = function.transact({"from": from_address})
    receipt = interface.w3.eth.waitForTransactionReceipt(tx_hash)
    interface.run_gas_profiler(profiler, tx_hash, function_name)
    return {"result": res, "gas": receipt["gasUsed"]}


data = b"\xaa" * 32
times = 100

interface = deploy()

print("Appending ", data.hex(), times, "times")
result = call(interface, "testMMR", function_args=[data, times])
print("MMR root:", result["result"].hex())
print("Gas used:", result["gas"])

finalize(interface)
