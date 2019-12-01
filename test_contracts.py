# TODO:
# 1. Import NipopwsContract.sol
# 2. Wrap the functionality around an object
# 3. Add snapshots
# 4. Check if there is something better than just estimating the gas used
# 5. Gas usage per solidity code line

import web3
from web3 import Web3, EthereumTesterProvider, contract

import eth_tester
from eth_tester import EthereumTester, PyEVMBackend

import solcx
from solcx import set_solc_version, get_solc_version, compile_source, compile_files

def print_fabulously(message, fill='='):
    message_length = len(message)
    print(fill * message_length)
    print(message)
    print(fill * message_length)

def compile_contracts(contract_path_list):

    if not isinstance(contract_path_list, list):
        contract_path_list = [contract_path_list]
    set_solc_version('v0.5.13')
    print_fabulously("Compiling with solidity " + str(get_solc_version()))
    compiled_contracts = compile_files(contract_path_list)
    print("Compiled contract(s): ", len(compiled_contracts))
    return compiled_contracts

def deploy_contracts(compiled_contracts, w3):
    deployed_contracts = []
    contract_instances = []
    for compiled_contract in compiled_contracts.items():
        deployed_contract = w3.eth.contract(
                                abi=compiled_contract[1]['abi'],
                                bytecode = compiled_contract[1]['bin']
                            )
        my_contract = deployed_contract.constructor()

        gas_estimate = my_contract.estimateGas()
        tx_hash = my_contract.transact()

        tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
        contract_address = tx_receipt['contractAddress']
        print("Deployed {0} at: {1} using {2} gas.".format(
            compiled_contract[0],
            contract_address,
            tx_receipt['cumulativeGasUsed']
            ))

        deployed_contracts.append(deployed_contract)

        contract_instance = w3.eth.contract(
                                abi = compiled_contract[1]['abi'],
                                address = contract_address
                            )
        contract_instances.append(contract_instance)

    return contract_instances

genesis_overrides = {'gas_limit': 31415926}
custom_genesis_params = PyEVMBackend._generate_genesis_params(overrides=genesis_overrides)
pyevm_backend = PyEVMBackend(genesis_parameters=custom_genesis_params)
test_chain = EthereumTester(backend=pyevm_backend)
w3 = Web3(EthereumTesterProvider(test_chain))

compiled_contracts = compile_contracts("./test.sol")
deployed_contracts = deploy_contracts(compiled_contracts, w3)
my_contract = deployed_contracts[0]

gas = my_contract.functions.test_func(True).estimateGas()
print("Estimated gas:", gas)

res = my_contract.functions.test_func(True).call()
print("Result was:", res)
