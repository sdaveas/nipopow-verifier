# TODO:
# 1. Test NipopwsContract.sol all functionalities
# 2.~Wrap the functionality around an object~
# 3. Add snapshots
# 4.~Check if there is something better than just estimating the gas used
# 5. Gas usage per solidity code line
# 6. Provide thorough unit tests

import sys
sys.path.append('../lib/')
import contract_interface
from create_proof import import_proof, create_proof, make_proof_file_name, get_proof
from timer import Timer

import argparse

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

def submit_event_proof(interface, proof):
    headers, siblings = extract_headers_siblings(proof)

    my_contract = interface.get_contract()
    from_address = interface.w3.eth.accounts[0]
    collateral = pow(10, 17)
    estimated_gas = my_contract.functions.submit_event_proof(
                                            headers,
                                            siblings,
                                            headers[-1],
                                            ).estimateGas()

    res = my_contract.functions.submit_event_proof(
                                            headers,
                                            siblings,
                                            headers[-1],
                                            ).call({'from' : from_address,
                                                    'value': collateral})

    tx_hash = my_contract.functions.submit_event_proof(
                                            headers,
                                            siblings,
                                            headers[-1],
                                            ).transact({'from' : from_address,
                                                        'value': collateral})

    receipt = interface.w3.eth.waitForTransactionReceipt(tx_hash)
    events = interface.get_contract().events.GasUsed().processReceipt(receipt)

    return {'result'        : res,
            'estemated gas' : estimated_gas,
            'receipt'       : receipt,
            'from'          : from_address,
            'backend'       : interface.backend,
            'events'        : events}

def run_nipopow(backend, proof):

    interface=contract_interface.ContractInterface(
                                    "../contractNipopow.sol",
                                    backend=backend,
                                    genesis_overrides={
                                                        'gas_limit': 67219750
                                                        },
                                    # precompiled_contract={
                                    #                     'abi':'./Crosschain.abi',
                                    #                     'bin':'./Crosschain.bin'
                                    #                     }
                                    )

    t = Timer()
    result = submit_event_proof(interface, proof)
    del t

    interface.end()

    return result['events']
    # return {'gas_used' : result['receipt']['gasUsed'], result['backend'] : backend}

def main():

    available_backends = contract_interface.ContractInterface.available_backends()
    parser = argparse.ArgumentParser(description='Benchmark Py-EVM, Ganache and Geth')
    parser.add_argument('--backend', choices=available_backends+['all'], required=True, type=str, help='The name of the EVM')
    parser.add_argument('--blocks', required=True, type=int, help='Number of blocks')
    parser.add_argument('--timer', action='store_true', help='Enable timers')

    args = parser.parse_args()
    backend = args.backend
    blocks = args.blocks
    timer = args.timer

    if (backend=='all'):
        backend=available_backends
    else:
        backend=[backend]

    proof = get_proof(blocks=blocks)
    print("Proof lenght:", len(proof))

    for b in backend:
        print('Testing', b)
        res = run_nipopow(backend=b, proof=proof)
        for e in res:
            print(e['args']['tag'], end=' ')
            print('\t', end=' ')
            print(e['args']['gas_used'])

if __name__ == "__main__":
    main()
