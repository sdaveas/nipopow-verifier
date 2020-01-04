import sys
sys.path.append('../lib/')
import contract_interface
from create_proof import import_proof, create_proof, make_proof_file_name, get_proof
from timer import Timer

import argparse

class Proof:
    def __init__(
            self,
            headers=None,
            siblings=None
            ):
        self.headers=headers
        self.siblings=siblings


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

def submit_event_proof(interface, headers, siblings, block_of_interest):

    my_contract = interface.get_contract()
    from_address = interface.w3.eth.accounts[0]
    collateral = pow(10, 17)
    estimated_gas = my_contract.functions.submit_event_proof(
                                            headers,
                                            siblings,
                                            block_of_interest,
                                            ).estimateGas()

    res = my_contract.functions.submit_event_proof(
                                            headers,
                                            siblings,
                                            block_of_interest
                                            ).call({'from' : from_address,
                                                    'value': collateral})

    tx_hash = my_contract.functions.submit_event_proof(
                                            headers,
                                            siblings,
                                            block_of_interest
                                            ).transact({'from' : from_address,
                                                        'value': collateral})

    receipt = interface.w3.eth.waitForTransactionReceipt(tx_hash)

    events = interface.get_contract().events.GasUsed().processReceipt(receipt)

    return {'result'        : {'submit': res},
            'receipt'       : receipt,
            'estimated_gas' : estimated_gas,
            'from'          : from_address,
            'backend'       : interface.backend,
            'events'        : events}

def submit_contesting_proof(interface, headers, siblings, block_of_interest):

    my_contract = interface.get_contract()
    from_address = interface.w3.eth.accounts[0]
    collateral = pow(10, 17)
    estimated_gas = my_contract.functions.submit_contesting_proof(
                                            headers,
                                            siblings,
                                            block_of_interest,
                                            ).estimateGas()

    res = my_contract.functions.submit_contesting_proof(
                                            headers,
                                            siblings,
                                            block_of_interest
                                            ).call({'from' : from_address})

    tx_hash = my_contract.functions.submit_contesting_proof(
                                            headers,
                                            siblings,
                                            block_of_interest
                                            ).transact({'from' : from_address})

    receipt = interface.w3.eth.waitForTransactionReceipt(tx_hash)

    events = interface.get_contract().events.GasUsed().processReceipt(receipt)

    return {'result'        : {'contesting': res},
            'receipt'       : receipt,
            'estimated_gas' : estimated_gas,
            'from'          : from_address,
            'backend'       : interface.backend,
            'events'        : events}

def submit_over_contest(backend, proof_1, proof_2, block_of_interest):

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

    results = []
    res = submit_event_proof(interface, proof_1.headers, proof_1.siblings, block_of_interest)
    results.append(res)
    res = submit_contesting_proof(interface, proof_2.headers, proof_2.siblings, block_of_interest)
    results.append(res)
    return results

def strip_result(result, tabs='  '):
    for res in result:
        print(tabs, end=' ')
        print('result:', res['result'])
        # print('gas used:', res['receipt']['gasUsed'])
        # for e in res['events']:
        #      print(e['args']['tag'], end=' ')
        #      print(' -> ', end=' ')
        #      print(e['args']['gas_used'])

def import_proofs(big_proof_name='big_proof.pkl', small_proof_name='small_proof.pkl', proof_dir='../proofs/'):
    proof_big = import_proof(proof_dir+big_proof_name)
    print('Big proof has length', len(proof_big))
    headers_big, siblings_big = extract_headers_siblings(proof_big)

    proof_small = import_proof(proof_dir+small_proof_name)
    print('Small proof has lenght', len(proof_small))
    headers_small, siblings_small = extract_headers_siblings(proof_small)

    return Proof(headers_big, siblings_big), Proof(headers_small, siblings_small)

def get_blocks_of_interest(big_proof, small_proof):

    blocks_and_summary = [ { 'ctx': big_proof.headers[-1],  'summary': 'a common block'       },
                           { 'ctx': big_proof.headers[ 0],  'summary': 'only in big chain'  },
                           { 'ctx': small_proof.headers[0], 'summary': 'only in small chain'}, ]
    return blocks_and_summary

def main():

    available_backends = contract_interface.ContractInterface.available_backends()
    parser = argparse.ArgumentParser(description='Benchmark Py-EVM, Ganache and Geth')
    parser.add_argument('--backend', choices=available_backends+['all'], required=True, type=str, help='The name of the EVM')
    parser.add_argument('--big', required=True, type=str, help='Filename of big proof')
    parser.add_argument('--small', required=True, type=str, help='Filename of small proof')

    args = parser.parse_args()
    backend = args.backend
    big_proof_name = args.big
    small_proof_name = args.small

    if (backend=='all'):
        backend=available_backends
    else:
        backend=[backend]

    big_proof = Proof()
    small_proof = Proof()
    big_proof, small_proof = import_proofs(big_proof_name=big_proof_name,
                                           small_proof_name=small_proof_name)

    blocks_of_interest = get_blocks_of_interest(big_proof, small_proof)

    for b in backend:
        print('Testing with', b)
        for block in blocks_of_interest:
            print('================================================================')
            print('Block of interest is', block['summary'],':')
            print('Submit with big, contest with small')
            result = submit_over_contest(b, big_proof, small_proof, block['ctx'])
            strip_result(result)
            print('Submit with small, contest with big')
            result = submit_over_contest(b, small_proof, big_proof, block['ctx'])
            strip_result(result)
            print('================================================================')

if __name__ == "__main__":
    main()
