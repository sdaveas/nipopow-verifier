"""
run with
$ pytest -v -s test_storage_vs_memory.py
"""

"""
output:

[Storage] 0 -> 22449
[Memory]  0 -> 22341
[Storage] 10 -> 145097
[Memory]  10 -> 45446
[Storage] 20 -> 278919
[Memory]  20 -> 104449
[Storage] 30 -> 412741
[Memory]  30 -> 199453
[Storage] 40 -> 546564
[Memory]  40 -> 330459
[Storage] 50 -> 680388
[Memory]  50 -> 497467
[Storage] 60 -> 814212
[Memory]  60 -> 700476
[Storage] 70 -> 948038
[Memory]  70 -> 939487
[Storage] 80 -> 1081864
[Memory]  80 -> 1214499
[Storage] 90 -> 1215691
[Memory]  90 -> 1525513
"""

import sys

sys.path.append("../tools/interface/")
import contract_interface


def call(function_name, function_args=[], constructor_arguments=[]):
    """
    Deploys the contract with contructor_arguments and runs a function with function_args
    """

    contract_path = "./contracts/storage_vs_memory.sol"
    interface = contract_interface.ContractInterface(
        contract_path, backend="ganache", constructor_arguments=constructor_arguments
    )
    my_contract = interface.get_contract()
    from_address = interface.w3.eth.accounts[0]
    function = my_contract.get_function_by_name(function_name)
    res = function(*function_args).call({"from": from_address})
    tx_hash = function().transact({"from": from_address})
    receipt = interface.w3.eth.waitForTransactionReceipt(tx_hash)
    interface.end()
    return {"result": res, "gas": receipt["gasUsed"]}



print("[Storage]", call("with_storage", constructor_arguments=[1000])["gas"])

# for i in range(0, 100, 10):
#     print("[Storage]", i, "->", call("with_storage", constructor_arguments=[i])["gas"])
#     print("[Memory] ", i, "->", call("with_memory", constructor_arguments=[i])["gas"])
