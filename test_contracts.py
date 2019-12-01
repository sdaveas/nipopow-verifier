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

import pickle
from create_blockchain_new import *
## Create roof pickle
# header, headerMap, mapInterlink = create_blockchain(blocks=450000)
# proof = make_proof(header, headerMap, mapInterlink)
# pickle_out = open("proof_new.pkl","wb")
# pickle.dump(proof, pickle_out)
# pickle_out.close()
## Read existing proof pickle
pickle_in = open("proof_new.pkl","rb")
proof = pickle.load(pickle_in)


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

def str_to_bytes32(s):
    r = []
    for start in range(0,len(s),32):
        r.append(s[start:start+32])
    return r

def extract_headers_siblings(proof):
    headers = []
    hashed_headers = []
    siblings = []
    # mp stands for merkle proof
    # hs stands for headers.
    for p in proof:
        hs = p[0]
        mp = p[1]
        # Copy the header to an array of 4 bytes32
        header = str_to_bytes32(hs)
        # Encode the Merkle bits (mu) in the largest byte
        # Encode the mp size in the next largest byte
        assert 0 <= len(mp) < 256
        mu = sum(bit << i for (i,(bit,_)) in enumerate(mp[::-1]))
        assert 0 <= mu < 256
        #header[3] = chr(len(mp)) + chr(mu) + header[3][2:]
        header[3] = header[3] + ('\x00'*14).encode() + bytes([len(mp)]) + bytes([mu])
        headers.append(header)

        for (_,sibling) in mp:
            siblings.append(sibling)

    return headers, siblings

def submit_event_proof(my_contract, proof):
    headers, siblings = extract_headers_siblings(proof)

    gas = my_contract.functions.submit_event_proof(
                                          headers,
                                          siblings,
                                          headers[100]
                                      ).estimateGas()
    print("Estimated gas:", gas)
    success = my_contract.functions.submit_event_proof(
                                          headers,
                                          siblings,
                                          headers[100]
                                      ).call()
    print("Result was:", res)

# Create a chain with custom parameters
genesis_overrides = {'gas_limit': 31415926}
custom_genesis_params = PyEVMBackend._generate_genesis_params(overrides=genesis_overrides)
pyevm_backend = PyEVMBackend(genesis_parameters=custom_genesis_params)
test_chain = EthereumTester(backend=pyevm_backend)
w3 = Web3(EthereumTesterProvider(test_chain))

# compile and deploy contracts
compiled_contracts = compile_contracts("./contractNipopow.sol")
deployed_contracts = deploy_contracts(compiled_contracts, w3)
my_contract = deployed_contracts[0]

# Aquire proof somehow and run the below
# submit_event_proof(my_contract, proof)

