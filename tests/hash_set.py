"""
run with
$ python hash_set
"""

import sys

sys.path.append("../tools/interface/")
import contract_interface
import web3


def test_make_hash_set(byte_array):
    """
    calls and measures gas of makeHashSet my_function
    """

    contract_path = "./contracts/hash_set.sol"
    interface = contract_interface.ContractInterface(
        contract_path, backend="geth"
    )
    my_contract = interface.get_contract()
    from_address = interface.w3.eth.accounts[0]

    # my_function = my_contract.functions.makeHashSet
    my_function = my_contract.functions.useMapping

    res = my_function(byte_array).call({"from": from_address})
    tx_hash = my_function(byte_array).transact({"from": from_address})
    receipt = interface.w3.eth.waitForTransactionReceipt(tx_hash)
    interface.end()
    print("Gas:", receipt['gasUsed'])

byte_array = []
for i in range(500):
    byte_array.append(i.to_bytes(32, 'big'))

print('Testing with', len(byte_array))
test_make_hash_set(byte_array)
