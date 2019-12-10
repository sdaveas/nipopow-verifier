# TODO:
# 1. Test NipopwsContract.sol all functionalities
# 2.~Wrap the functionality around an object~
# 3. Add snapshots
# 4.~Check if there is something better than just estimating the gas used
# 5. Gas usage per solidity code line
# 6. Provide thorough unit tests

import contract_interface
import argparse

# import/export proof
def import_proof(filename='proof_new.pkl'):
    import pickle
    pickle_in = open(filename,'rb')
    proof = pickle.load(pickle_in)
    return proof

def create_proof(blocks=450000, filename='proof_new.pkl'):
    import pickle
    import create_blockchain_new as blockchain_utils
    header, headerMap, mapInterlink = blockchain_utils.create_blockchain(blocks=blocks)
    proof = blockchain_utils.make_proof(header, headerMap, mapInterlink)
    pickle_out = open(filename, 'wb')
    pickle.dump(proof, pickle_out)
    pickle_out.close()
    print("Proof was written in " + filename)
    return proof

# proof data manipulation
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

# tests
def measure_gas(method, backend, filepath='./unit_tests/test.sol'):

    interface = contract_interface.ContractInterface(filepath, backend=backend)

    estimated_gas = interface.get_contract().functions.measure_gas().estimateGas()
    from_address = interface.w3.eth.accounts[0]
    result = interface.get_contract().functions.measure_gas().transact({'from':from_address})

    print(interface.get_contract().functions.gas().call())

    return {'result'        : result,
            'method'        : method,
            'estimated_gas' : estimated_gas,
            'from'          : from_address,
            'backend'       : interface.backend}

def run_test(method, backend, filepath='./unit_tests/test.sol'):

    interface = contract_interface.ContractInterface(filepath, backend=backend)

    callback=interface.get_contract().get_function_by_name(method)

    # estimated_gas = interface.get_contract().functions.test(True).estimateGas()
    estimated_gas = callback(True).estimateGas()
    from_address = interface.w3.eth.accounts[0]
    tx_hash = callback(False).transact({'from':from_address})
    receipt = interface.w3.eth.waitForTransactionReceipt(tx_hash)

    return {'method'        : method,
            'estimated_gas' : estimated_gas,
            'gas_used'      : receipt['gasUsed'],
            'from'          : from_address,
            'backend'       : interface.backend}


def submit_event_proof(interface, proof):
    headers, siblings = extract_headers_siblings(proof)

    my_contract = interface.get_contract()
    from_address = interface.w3.eth.accounts[0]
    estimated_gas = my_contract.functions.submit_event_proof(
                                            headers,
                                            siblings,
                                            headers[1]
                                            ).estimateGas()

    tx_hash = my_contract.functions.submit_event_proof(
                                            headers,
                                            siblings,
                                            headers[1]
                                            ).transact({'from' : from_address,
                                                    'value': 100000000000000000})

    receipt = interface.w3.eth.waitForTransactionReceipt(tx_hash)

    gas_used = interface.w3.eth.getBlock('pending').gasUsed

    return {'receipt'       : receipt,
            'estimated_gas' : estimated_gas,
            'from'          : from_address,
            'backend'       : interface.backend}

def run_nipopow(backend, blocks):

    interface=contract_interface.ContractInterface(
                                    "./contractNipopow.sol",
                                    backend=backend,
                                    genesis_overrides={
                                                        'gas_limit': 67219750
                                                        },
                                    precompiled_contract={
                                                        'abi':'./Crosschain.abi',
                                                        'bin':'./Crosschain.bin'
                                                        })

    proof = create_proof(blocks=blocks, filename=str('proof_'+str(blocks)+'.pkl'))
    print("Proof lenght:", len(proof))
    result = submit_event_proof(interface, proof)
    return {'gas_used' : result['receipt']['gasUsed'], result['backend'] : backend}

def main():

    blocks = 100
    # print(run_nipopow(backend='Py-EVM', blocks=blocks))
    # print(run_nipopow(backend='ganache', blocks=blocks))

    # methods = [
    #         # 'test',
    #         # 'test_payable',
    #         'test_memory',
    #         ]
    # backends = [
    #         'ganache',
    #         'Py-EVM',
    #         ]

    # for method in methods:
    #     for backend in backends:
    #         print(method, backend)
    #         print(run_test(method=method, backend=backend))

    print(measure_gas('measure_gas', 'ganache'));

if __name__ == "__main__":
    main()
