"""
run with
$ pytest -v -s test_storage_vs_memory.py
"""

"""
Output was:
[Storage]  0 ->    22254
[Memory]   0 ->    21736

[Storage] 10 ->   154994
[Memory]  10 ->   151556

[Storage] 20 ->   293867
[Memory]  20 ->   530776

[Storage] 30 ->   435237
[Memory]  30 ->  1159396

[Storage] 40 ->   576607
[Memory]  40 ->  2037416

[Storage] 50 ->   717977
[Memory]  50 ->  3164836

[Storage] 60 ->   859347
[Memory]  60 ->  4541656

[Storage] 70 ->  1000717
[Memory]  70 ->  6167876

[Storage] 80 ->  1142087
[Memory]  80 ->  8043496

[Storage] 90 ->  1283457
[Memory]  90 -> 10168516

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


for i in range(0, 100, 10):
    print("[Storage]", i, "->", call("with_storage", constructor_arguments=[i])["gas"])
    print("[Memory] ", i, "->", call("with_memory", constructor_arguments=[i])["gas"])
